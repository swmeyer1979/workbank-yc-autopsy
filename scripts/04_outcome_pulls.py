"""
04_outcome_pulls.py — Outcome collection pipeline for YC × WORKBank postmortem.

For each company in yc_companies.csv:
  - HTTP fetch of company website
  - site_live, site_status_code, site_content_length
  - has_careers_page
  - current_site_meta_description
  - description_drift_cosine (all-MiniLM-L6-v2)

Also writes site_texts.jsonl (slug, text, meta) for full body storage.
Resume-safe: skips slugs already in outcomes.csv.
"""

import csv
import hashlib
import json
import os
import random
import re
import time
import urllib.parse
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV      = os.path.join(BASE, "data", "processed", "yc_companies.csv")
OUTPUT_CSV     = os.path.join(BASE, "data", "processed", "outcomes.csv")
SITE_TEXTS_OUT = os.path.join(BASE, "data", "processed", "site_texts.jsonl")
CACHE_DIR      = os.path.join(BASE, "data", "raw", "site_cache")

os.makedirs(CACHE_DIR, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_WORKERS    = 20
TIMEOUT        = 10
RETRY_WAIT     = 2
JITTER_LO      = 0.2
JITTER_HI      = 0.8
BODY_TRUNC     = 2000
DRIFT_MIN_CHARS = 100
EMBED_MODEL    = "all-MiniLM-L6-v2"

PARKED_KEYWORDS = re.compile(
    r"(domain\s+for\s+sale|this\s+domain|parked\s+by|buy\s+this\s+domain"
    r"|domain\s+is\s+for\s+sale|sedoparking|hugedomains|namecheap\s+parked"
    r"|godaddy\s+parked|this\s+web\s+page\s+is\s+parked|expired\s+domain"
    r"|domain\s+expired|renewal\s+date\s+has\s+passed)",
    re.IGNORECASE,
)
CAREERS_RE = re.compile(
    r"(careers|jobs|hiring|we.?re\s+hiring|open\s+roles|join.*team)",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (research; yc-workbank-postmortem) "
        "contact: research@example.com"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

OUTPUT_COLUMNS = [
    "slug", "website", "site_live", "site_status_code", "site_content_length",
    "has_careers_page", "current_site_meta_description",
    "description_drift_cosine", "fetch_skipped_reason", "fetch_timestamp",
]

# ── Robots cache (per-host, in-process) ──────────────────────────────────────
_robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}


def get_robots(host: str) -> urllib.robotparser.RobotFileParser | None:
    if host in _robots_cache:
        return _robots_cache[host]
    rp = urllib.robotparser.RobotFileParser()
    robots_url = f"https://{host}/robots.txt"
    try:
        rp.set_url(robots_url)
        rp.read()
        _robots_cache[host] = rp
    except Exception:
        _robots_cache[host] = None
        return None
    return rp


def robots_allows(url: str) -> bool:
    """Return True if robots.txt allows our UA to fetch url (fail-open)."""
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc
        rp = get_robots(host)
        if rp is None:
            return True
        return rp.can_fetch(HEADERS["User-Agent"], url)
    except Exception:
        return True


# ── HTML cache ────────────────────────────────────────────────────────────────

def cache_path(slug: str) -> str:
    return os.path.join(CACHE_DIR, f"{slug}.html")


def load_cache(slug: str) -> bytes | None:
    p = cache_path(slug)
    if os.path.exists(p):
        with open(p, "rb") as f:
            return f.read()
    return None


def save_cache(slug: str, content: bytes) -> None:
    with open(cache_path(slug), "wb") as f:
        f.write(content)


# ── HTTP fetch ────────────────────────────────────────────────────────────────

def fetch_url(url: str, slug: str) -> tuple[int | None, bytes | None, str | None]:
    """
    Returns (status_code, body_bytes, error_reason).
    Tries cache first. One retry on 429/503/connection error.
    """
    cached = load_cache(slug)
    if cached is not None:
        # cached — we don't have the original status code; treat as 200
        return 200, cached, None

    time.sleep(random.uniform(JITTER_LO, JITTER_HI))

    def attempt() -> tuple[int | None, bytes | None, str | None]:
        try:
            resp = requests.get(
                url, headers=HEADERS, timeout=TIMEOUT,
                allow_redirects=True, stream=False,
            )
            return resp.status_code, resp.content, None
        except requests.exceptions.ConnectionError as e:
            return None, None, f"connection_error: {e}"
        except requests.exceptions.Timeout:
            return None, None, "timeout"
        except Exception as e:
            return None, None, f"error: {e}"

    status, body, err = attempt()

    if err or (status in (429, 503)):
        time.sleep(RETRY_WAIT)
        status, body, err = attempt()

    if err:
        return None, None, err

    if status is not None and body is not None:
        save_cache(slug, body)

    return status, body, err


# ── HTML parsing ──────────────────────────────────────────────────────────────

NAV_FOOTER_SELECTORS = [
    "nav", "footer", "header", "[role='navigation']",
    ".nav", ".navbar", ".footer", ".header", ".menu",
    "#nav", "#footer", "#header", "#menu", "#navigation",
    ".cookie-banner", ".cookie-notice", ".gdpr",
]


def extract_body_text(soup: BeautifulSoup) -> str:
    """Strip nav/footer, extract text from body, collapse whitespace."""
    body = soup.find("body")
    if not body:
        body = soup
    # remove noise elements
    for sel in NAV_FOOTER_SELECTORS:
        for tag in body.select(sel):
            tag.decompose()
    text = body.get_text(separator=" ")
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_meta_description(soup: BeautifulSoup) -> str | None:
    for attrs in [
        {"name": "description"},
        {"property": "og:description"},
        {"name": "twitter:description"},
    ]:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content", "").strip():
            return tag["content"].strip()
    return None


def extract_careers_signal(soup: BeautifulSoup) -> bool:
    # Check all <a> tags: href and text
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = a.get_text(" ", strip=True)
        if CAREERS_RE.search(href) or CAREERS_RE.search(text):
            return True
    # Also check button/span text
    for el in soup.find_all(["button", "span", "li"]):
        if CAREERS_RE.search(el.get_text(" ", strip=True)):
            return True
    return False


def parse_html(slug: str, body: bytes) -> dict:
    try:
        soup = BeautifulSoup(body, "html.parser")
    except Exception as e:
        return {"parse_error": str(e)}

    full_text = extract_body_text(soup)
    meta_desc = extract_meta_description(soup)
    has_careers = extract_careers_signal(soup)
    truncated_text = full_text[:BODY_TRUNC]

    return {
        "full_text": full_text,
        "truncated_text": truncated_text,
        "meta_description": meta_desc,
        "has_careers": has_careers,
        "content_length": len(full_text),
    }


# ── Per-company worker ────────────────────────────────────────────────────────

def process_company(row: dict) -> dict:
    slug      = row.get("slug", "").strip()
    website   = row.get("website", "").strip()
    long_desc = row.get("long_description", "").strip()
    one_liner = row.get("one_liner", "").strip()
    # Use long_description; fall back to one_liner if missing/short
    yc_text = long_desc if len(long_desc) >= 20 else one_liner

    base = {
        "slug": slug,
        "website": website,
        "site_live": None,
        "site_status_code": None,
        "site_content_length": None,
        "has_careers_page": None,
        "current_site_meta_description": None,
        "description_drift_cosine": None,
        "fetch_skipped_reason": None,
        "fetch_timestamp": None,
        # internal fields (not written to CSV)
        "_full_text": None,
        "_meta_description": None,
        "_long_description": yc_text,
    }

    # ── Skip invalid URLs ─────────────────────────────────────────────────────
    if not website:
        base["fetch_skipped_reason"] = "no_website"
        return base
    if not website.lower().startswith("http"):
        base["fetch_skipped_reason"] = "non_http_url"
        return base

    # ── Robots check ─────────────────────────────────────────────────────────
    if not robots_allows(website):
        base["fetch_skipped_reason"] = "robots_disallowed"
        return base

    # ── Fetch ─────────────────────────────────────────────────────────────────
    ts = datetime.now(timezone.utc).isoformat()
    status, body, err = fetch_url(website, slug)
    base["fetch_timestamp"] = ts

    if err or body is None:
        base["fetch_skipped_reason"] = err or "fetch_error"
        base["site_status_code"] = status
        return base

    base["site_status_code"] = status

    # ── Parse ─────────────────────────────────────────────────────────────────
    parsed = parse_html(slug, body)
    if "parse_error" in parsed:
        base["fetch_skipped_reason"] = f"parse_error: {parsed['parse_error']}"
        return base

    full_text     = parsed["full_text"]
    meta_desc     = parsed["meta_description"]
    content_len   = parsed["content_length"]
    has_careers   = parsed["has_careers"]

    base["site_content_length"]        = content_len
    base["has_careers_page"]           = has_careers
    base["current_site_meta_description"] = meta_desc
    base["_full_text"]                 = parsed["truncated_text"]
    base["_meta_description"]          = meta_desc

    # ── site_live logic ───────────────────────────────────────────────────────
    is_2xx_3xx = status is not None and (200 <= status < 400)
    # count non-whitespace chars in body text; fall back to meta desc length
    # for JS-heavy SPAs that serve an empty body but set meta tags server-side
    non_ws = len(re.sub(r"\s", "", full_text))
    meta_non_ws = len(re.sub(r"\s", "", meta_desc or ""))
    has_content = (non_ws > 200) or (meta_non_ws > 50)
    not_parked = not PARKED_KEYWORDS.search(full_text[:3000])

    base["site_live"] = bool(is_2xx_3xx and has_content and not_parked)

    return base


# ── Embeddings + drift (batch after all fetches) ──────────────────────────────

def compute_drift(results: list[dict], model: SentenceTransformer) -> list[dict]:
    """
    Compute description_drift_cosine for each result in-place.
    Batches all embedding calls for efficiency.
    """
    # Build pairs: (idx, yc_text, site_text)
    pairs = []
    for i, r in enumerate(results):
        long_desc = r.get("_long_description", "")
        meta_desc = r.get("_meta_description") or ""
        full_text = r.get("_full_text", "") or ""

        # prefer meta if ≥50 chars (real description); else fall back to body
        site_text = meta_desc if len(meta_desc) >= 50 else full_text[:500]

        # threshold: 50 chars for meta-only pages, 100 for body text
        min_thresh = 50 if (len(meta_desc) >= 50 and len(full_text) < 100) else DRIFT_MIN_CHARS

        if not long_desc or len(site_text) < min_thresh:
            continue
        pairs.append((i, long_desc, site_text))

    if not pairs:
        return results

    indices  = [p[0] for p in pairs]
    yc_texts = [p[1] for p in pairs]
    site_txts = [p[2] for p in pairs]

    all_texts = yc_texts + site_txts
    embeddings = model.encode(all_texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)

    n = len(pairs)
    yc_embs   = embeddings[:n]
    site_embs = embeddings[n:]

    for j, idx in enumerate(indices):
        cos_sim = float(np.dot(yc_embs[j], site_embs[j]))
        drift   = round(1.0 - cos_sim, 6)
        results[idx]["description_drift_cosine"] = drift

    return results


# ── Validation / summary ──────────────────────────────────────────────────────

def print_summary(results: list[dict], runtime_s: float) -> None:
    total       = len(results)
    live        = sum(1 for r in results if r.get("site_live") is True)
    errors      = sum(1 for r in results if r.get("fetch_skipped_reason") and
                      r["fetch_skipped_reason"] not in ("no_website", "non_http_url", "robots_disallowed"))
    skipped     = sum(1 for r in results if r.get("fetch_skipped_reason") in
                      ("no_website", "non_http_url", "robots_disallowed"))
    drift_vals  = [r["description_drift_cosine"] for r in results if r.get("description_drift_cosine") is not None]

    print(f"\n{'='*60}")
    print(f"SUMMARY  (runtime: {runtime_s:.1f}s)")
    print(f"{'='*60}")
    print(f"Total processed : {total}")
    print(f"site_live=True  : {live}  ({100*live/total:.1f}%)")
    print(f"Fetch errors    : {errors}")
    print(f"Skipped (no URL): {skipped}")
    print(f"Drift computed  : {len(drift_vals)}")

    if drift_vals:
        arr = np.array(drift_vals)
        print(f"Drift mean      : {arr.mean():.4f}")
        print(f"Drift std       : {arr.std():.4f}")
        print(f"Drift min/max   : {arr.min():.4f} / {arr.max():.4f}")
        bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        hist, _ = np.histogram(arr, bins=bins)
        print("\nDrift histogram:")
        for i in range(len(hist)):
            label = f"  [{bins[i]:.1f}–{bins[i+1]:.1f})"
            bar   = "█" * (hist[i] // max(1, len(drift_vals) // 50))
            print(f"{label}: {hist[i]:4d}  {bar}")
        if arr.mean() > 0.7:
            print("\n⚠  WARNING: mean drift >0.7 — possible scrape quality issue")
        if arr.mean() < 0.1:
            print("\n⚠  WARNING: mean drift <0.1 — companies mostly unchanged or meta too short")
    print(f"{'='*60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    t0 = time.time()

    # ── Load input ────────────────────────────────────────────────────────────
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        companies = list(reader)

    print(f"Loaded {len(companies)} companies from {INPUT_CSV}")

    # ── Resume: load already-completed slugs ──────────────────────────────────
    done_slugs: set[str] = set()
    existing_rows: list[dict] = []

    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
                done_slugs.add(row["slug"])
        print(f"Resuming: {len(done_slugs)} slugs already in outcomes.csv — skipping")

    # ── Load already-done site texts ──────────────────────────────────────────
    done_text_slugs: set[str] = set()
    if os.path.exists(SITE_TEXTS_OUT):
        with open(SITE_TEXTS_OUT, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    done_text_slugs.add(obj.get("slug", ""))
                except Exception:
                    pass

    # ── Filter to pending ─────────────────────────────────────────────────────
    pending = [c for c in companies if c.get("slug", "").strip() not in done_slugs]
    print(f"Fetching {len(pending)} companies...")

    if not pending:
        print("Nothing to do.")
        # still print summary from existing data
        print_summary(existing_rows, time.time() - t0)
        return

    # ── Concurrent fetch ──────────────────────────────────────────────────────
    new_results: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_company, row): row for row in pending}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching"):
            try:
                result = future.result()
                new_results.append(result)
            except Exception as e:
                row = futures[future]
                new_results.append({
                    "slug": row.get("slug", ""),
                    "website": row.get("website", ""),
                    "site_live": None,
                    "site_status_code": None,
                    "site_content_length": None,
                    "has_careers_page": None,
                    "current_site_meta_description": None,
                    "description_drift_cosine": None,
                    "fetch_skipped_reason": f"executor_error: {e}",
                    "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
                    "_full_text": None,
                    "_meta_description": None,
                    "_long_description": row.get("long_description", ""),
                })

    # ── Compute embeddings + drift in batch ───────────────────────────────────
    print(f"\nLoading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    print("Computing description drift (batch)...")
    new_results = compute_drift(new_results, model)

    # ── Write site_texts.jsonl (append, new slugs only) ───────────────────────
    with open(SITE_TEXTS_OUT, "a", encoding="utf-8") as f:
        for r in new_results:
            slug = r.get("slug", "")
            if slug in done_text_slugs:
                continue
            full_text = r.get("_full_text")
            meta      = r.get("_meta_description")
            if full_text or meta:
                f.write(json.dumps({
                    "slug": slug,
                    "text": full_text or "",
                    "meta": meta or "",
                }, ensure_ascii=False) + "\n")

    # ── Write outcomes.csv ────────────────────────────────────────────────────
    # Append new results; reconstruct full file so headers are consistent
    all_results = existing_rows + [
        {k: r.get(k) for k in OUTPUT_COLUMNS}
        for r in new_results
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"Wrote {len(all_results)} rows to {OUTPUT_CSV}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print_summary(all_results, time.time() - t0)


if __name__ == "__main__":
    main()
