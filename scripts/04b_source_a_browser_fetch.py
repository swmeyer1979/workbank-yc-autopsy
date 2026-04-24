"""
04b_source_a_browser_fetch.py — Source A for 2-of-3 shuttered label.

Browser-grade HTTP fetch per company using scrapling.
- StealthyFetcher (adetect-mode) first; falls back to AsyncFetcher on failure;
  falls back to requests with Chrome UA if scrapling entirely fails.
- site_live = 2xx/3xx AND body_text > 300 chars AND no parked-domain keywords.
- Cache per-company to data/raw/site_fetch_v2/<slug>.json (gitignored).
- Resume-safe: skips slugs already in outcomes_browser.csv.

Output: data/processed/outcomes_browser.csv
Columns: slug, source_A_live, source_A_status, source_A_body_len,
         source_A_method, source_A_timestamp
"""

import asyncio
import csv
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from tqdm import tqdm

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV  = os.path.join(BASE, "data", "processed", "yc_companies.csv")
OUTPUT_CSV = os.path.join(BASE, "data", "processed", "outcomes_browser.csv")
CACHE_DIR  = os.path.join(BASE, "data", "raw", "site_fetch_v2")

os.makedirs(CACHE_DIR, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_WORKERS        = 10   # headless browsers are heavy
STEALTHY_TIMEOUT   = 20_000  # ms for StealthyFetcher
ASYNC_TIMEOUT      = 15      # seconds for AsyncFetcher
REQUESTS_TIMEOUT   = 20      # seconds for fallback requests
BODY_MIN_CHARS     = 300
PREVIEW_LEN        = 500

CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

PARKED_KEYWORDS = re.compile(
    r"(domain\s+for\s+sale|this\s+domain|parked\s+by|buy\s+this\s+domain"
    r"|domain\s+is\s+for\s+sale|sedoparking|hugedomains|namecheap\s+parked"
    r"|godaddy\s+parked|this\s+web\s+page\s+is\s+parked|expired\s+domain"
    r"|domain\s+expired|renewal\s+date\s+has\s+passed"
    r"|coming\s+soon|this\s+site\s+can.t\s+be\s+reached)",
    re.IGNORECASE,
)

OUTPUT_COLUMNS = [
    "slug", "source_A_live", "source_A_status",
    "source_A_body_len", "source_A_method", "source_A_timestamp",
]


# ── Cache helpers ─────────────────────────────────────────────────────────────

def cache_path(slug: str) -> str:
    return os.path.join(CACHE_DIR, f"{slug}.json")


def load_cache(slug: str) -> dict | None:
    p = cache_path(slug)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_cache(slug: str, data: dict) -> None:
    with open(cache_path(slug), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# ── Live classification ───────────────────────────────────────────────────────

def classify_live(status: int | None, body_text: str) -> bool:
    if status is None:
        return False
    is_2xx_3xx = 200 <= status < 400
    body_clean = re.sub(r"\s+", " ", body_text).strip()
    has_content = len(body_clean) > BODY_MIN_CHARS
    not_parked = not PARKED_KEYWORDS.search(body_clean[:3000])
    return bool(is_2xx_3xx and has_content and not_parked)


# ── StealthyFetcher (sync, run in thread) ────────────────────────────────────

def fetch_stealthy(url: str) -> tuple[int | None, str, str]:
    """Returns (status, body_text, error_or_empty). Runs sync."""
    try:
        from scrapling import StealthyFetcher
        page = StealthyFetcher.fetch(
            url,
            network_idle=True,
            timeout=STEALTHY_TIMEOUT,
        )
        status = page.status
        body_text = page.body.text_content() if page.body else ""
        if not body_text:
            body_text = page.get_all_text(ignore_tags=("script", "style"))
        return status, body_text or "", ""
    except Exception as e:
        return None, "", str(e)


# ── AsyncFetcher fallback ─────────────────────────────────────────────────────

def fetch_async_fetcher(url: str) -> tuple[int | None, str, str]:
    """Returns (status, body_text, error_or_empty)."""
    try:
        from scrapling import AsyncFetcher

        async def _run():
            page = await AsyncFetcher.get(
                url,
                stealthy_headers=True,
                follow_redirects=True,
                timeout=ASYNC_TIMEOUT,
            )
            return page

        page = asyncio.run(_run())
        status = page.status
        body_text = page.body.text_content() if page.body else ""
        if not body_text:
            body_text = page.get_all_text(ignore_tags=("script", "style"))
        return status, body_text or "", ""
    except Exception as e:
        return None, "", str(e)


# ── requests fallback ─────────────────────────────────────────────────────────

def fetch_requests(url: str) -> tuple[int | None, str, str]:
    """Returns (status, body_text, error_or_empty). Chrome UA fallback."""
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(
            url,
            headers={"User-Agent": CHROME_UA},
            allow_redirects=True,
            timeout=REQUESTS_TIMEOUT,
        )
        soup = BeautifulSoup(resp.content, "html.parser")
        body = soup.find("body")
        text = (body or soup).get_text(separator=" ")
        text = re.sub(r"\s+", " ", text).strip()
        return resp.status_code, text, ""
    except Exception as e:
        return None, "", str(e)


# ── Per-company worker ────────────────────────────────────────────────────────

def process_company(row: dict) -> dict:
    slug    = row.get("slug", "").strip()
    website = row.get("website", "").strip()
    ts      = datetime.now(timezone.utc).isoformat()

    base = {
        "slug": slug,
        "source_A_live": None,
        "source_A_status": None,
        "source_A_body_len": None,
        "source_A_method": None,
        "source_A_timestamp": ts,
    }

    if not website or not website.lower().startswith("http"):
        base["source_A_method"] = "skipped_no_url"
        return base

    # Check cache first
    cached = load_cache(slug)
    if cached is not None:
        base.update({
            "source_A_live":      cached.get("source_A_live"),
            "source_A_status":    cached.get("source_A_status"),
            "source_A_body_len":  cached.get("source_A_body_len"),
            "source_A_method":    cached.get("source_A_method") + "_cached",
            "source_A_timestamp": cached.get("source_A_timestamp", ts),
        })
        return base

    # Jitter
    time.sleep(random.uniform(0.1, 0.5))

    # Try StealthyFetcher first
    status, body_text, err = fetch_stealthy(website)
    method = "stealthy_fetcher"

    # Fall back to AsyncFetcher
    if status is None or err:
        status, body_text, err = fetch_async_fetcher(website)
        method = "async_fetcher"

    # Fall back to requests
    if status is None or err:
        status, body_text, err = fetch_requests(website)
        method = "requests_chrome_ua"

    live = classify_live(status, body_text) if status is not None else None

    result = {
        "slug":             slug,
        "source_A_live":    live,
        "source_A_status":  status,
        "source_A_body_len": len(body_text) if body_text else 0,
        "source_A_method":  method,
        "source_A_timestamp": ts,
        # cache extras
        "body_preview_500": body_text[:PREVIEW_LEN] if body_text else "",
    }

    save_cache(slug, {
        "status":            status,
        "body_len":          len(body_text) if body_text else 0,
        "body_preview_500":  body_text[:PREVIEW_LEN] if body_text else "",
        "timestamp":         ts,
        "method":            method,
        # store these for the CSV reload path
        "source_A_live":     live,
        "source_A_status":   status,
        "source_A_body_len": len(body_text) if body_text else 0,
        "source_A_method":   method,
        "source_A_timestamp": ts,
    })

    return {k: result[k] for k in OUTPUT_COLUMNS}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    t0 = time.time()

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        companies = list(csv.DictReader(f))
    print(f"Loaded {len(companies)} companies")

    # Resume
    done_slugs: set[str] = set()
    existing_rows: list[dict] = []
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_rows.append(row)
                done_slugs.add(row["slug"])
        print(f"Resuming: {len(done_slugs)} already done")

    pending = [c for c in companies if c.get("slug", "").strip() not in done_slugs]
    print(f"Fetching {len(pending)} companies (max {MAX_WORKERS} concurrent)...")

    if not pending:
        print("Nothing to do.")
        return

    new_results: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(process_company, row): row for row in pending}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Source A"):
            try:
                new_results.append(future.result())
            except Exception as e:
                row = futures[future]
                new_results.append({
                    "slug":             row.get("slug", ""),
                    "source_A_live":    None,
                    "source_A_status":  None,
                    "source_A_body_len": None,
                    "source_A_method":  f"executor_error: {e}",
                    "source_A_timestamp": datetime.now(timezone.utc).isoformat(),
                })

    all_results = existing_rows + new_results
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(all_results)

    live_n   = sum(1 for r in all_results if str(r.get("source_A_live")) == "True")
    dead_n   = sum(1 for r in all_results if str(r.get("source_A_live")) == "False")
    null_n   = sum(1 for r in all_results if r.get("source_A_live") is None or r.get("source_A_live") == "")
    elapsed  = time.time() - t0

    print(f"\nWrote {len(all_results)} rows to {OUTPUT_CSV}")
    print(f"  source_A_live=True:  {live_n}")
    print(f"  source_A_live=False: {dead_n}")
    print(f"  null:                {null_n}")
    print(f"  Runtime: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
