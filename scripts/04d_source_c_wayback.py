"""
04d_source_c_wayback.py — Source C for 2-of-3 shuttered label.

Wayback Machine last-snapshot recency per company.
API: https://archive.org/wayback/available?url={website}

Classification:
  - snapshot exists AND timestamp within last 180 days → source_C_live = True
  - snapshot older than 180 days OR response body < 500 chars → source_C_live = False
  - Wayback has never archived the site → source_C_live = None

Rate-limit: max 20 concurrent, 0.3s jitter, single retry on 429/503.
Respectful to Wayback (nonprofit).

Output: data/processed/outcomes_wayback.csv
Columns: slug, source_C_live, source_C_last_snapshot_date,
         source_C_snapshot_body_len, source_C_timestamp
"""

import csv
import json
import os
import random
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

import requests
from tqdm import tqdm

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV  = os.path.join(BASE, "data", "processed", "yc_companies.csv")
OUTPUT_CSV = os.path.join(BASE, "data", "processed", "outcomes_wayback.csv")

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_WORKERS        = 20
JITTER_S           = 0.3
WAYBACK_TIMEOUT    = 15
SNAPSHOT_WINDOW_DAYS = 180
SNAPSHOT_BODY_MIN  = 500   # chars; below this → treat as parked/empty
WAYBACK_API        = "https://archive.org/wayback/available"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (research; yc-postmortem-wayback) "
        "contact: research@example.com"
    ),
}

OUTPUT_COLUMNS = [
    "slug", "source_C_live", "source_C_last_snapshot_date",
    "source_C_snapshot_body_len", "source_C_timestamp",
]

CUTOFF = datetime.now(timezone.utc) - timedelta(days=SNAPSHOT_WINDOW_DAYS)


# ── Wayback fetch ─────────────────────────────────────────────────────────────

def query_wayback(url: str) -> dict:
    """
    Returns dict with keys: snapshot_ts, snapshot_url, api_body_len, error.
    snapshot_ts is None if no snapshot exists.
    """
    params = {"url": url}
    encoded = urllib.parse.urlencode(params)
    api_url = f"{WAYBACK_API}?{encoded}"

    def attempt():
        try:
            resp = requests.get(
                api_url,
                headers=HEADERS,
                timeout=WAYBACK_TIMEOUT,
            )
            body = resp.text
            return resp.status_code, body, None
        except Exception as e:
            return None, "", str(e)

    status, body, err = attempt()

    # Single retry on 429/503
    if err or status in (429, 503):
        time.sleep(1.0 + random.uniform(0, 0.5))
        status, body, err = attempt()

    if err or status is None:
        return {"snapshot_ts": None, "snapshot_url": None,
                "api_body_len": 0, "error": err or "fetch_failed"}

    api_body_len = len(body)

    try:
        data = json.loads(body)
    except Exception:
        return {"snapshot_ts": None, "snapshot_url": None,
                "api_body_len": api_body_len, "error": "json_parse_error"}

    archived = data.get("archived_snapshots", {}).get("closest", {})
    if not archived or not archived.get("available"):
        return {"snapshot_ts": None, "snapshot_url": None,
                "api_body_len": api_body_len, "error": None}

    snapshot_ts_raw = archived.get("timestamp", "")  # YYYYMMDDHHmmss
    snapshot_url    = archived.get("url", "")

    return {
        "snapshot_ts":  snapshot_ts_raw,
        "snapshot_url": snapshot_url,
        "api_body_len": api_body_len,
        "error":        None,
    }


def parse_wayback_ts(ts_raw: str) -> datetime | None:
    """Parse YYYYMMDDHHmmss → UTC datetime."""
    if not ts_raw or len(ts_raw) < 8:
        return None
    try:
        return datetime.strptime(ts_raw[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None


# ── Per-company worker ────────────────────────────────────────────────────────

def process_company(row: dict) -> dict:
    slug    = row.get("slug", "").strip()
    website = row.get("website", "").strip()
    ts_now  = datetime.now(timezone.utc).isoformat()

    base = {
        "slug":                     slug,
        "source_C_live":            None,
        "source_C_last_snapshot_date": None,
        "source_C_snapshot_body_len":  None,
        "source_C_timestamp":       ts_now,
    }

    if not website or not website.lower().startswith("http"):
        return base

    time.sleep(random.uniform(0, JITTER_S))

    result = query_wayback(website)
    snapshot_ts_raw = result.get("snapshot_ts")
    api_body_len    = result.get("api_body_len", 0)
    error           = result.get("error")

    base["source_C_snapshot_body_len"] = api_body_len

    if error and not snapshot_ts_raw:
        # fetch failed entirely — leave null
        return base

    if not snapshot_ts_raw:
        # Wayback has never archived this site
        base["source_C_live"] = None
        return base

    snapshot_dt = parse_wayback_ts(snapshot_ts_raw)
    if snapshot_dt is not None:
        base["source_C_last_snapshot_date"] = snapshot_dt.strftime("%Y-%m-%d")

    # Classify
    # live: snapshot within 180 days AND response body >= 500 chars
    if snapshot_dt is None:
        base["source_C_live"] = False
    elif snapshot_dt >= CUTOFF and api_body_len >= SNAPSHOT_BODY_MIN:
        base["source_C_live"] = True
    else:
        base["source_C_live"] = False

    return base


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
    print(f"Querying Wayback for {len(pending)} companies (max {MAX_WORKERS} concurrent)...")

    if not pending:
        print("Nothing to do.")
        return

    new_results: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(process_company, row): row for row in pending}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Source C"):
            try:
                new_results.append(future.result())
            except Exception as e:
                row = futures[future]
                new_results.append({
                    "slug":                     row.get("slug", ""),
                    "source_C_live":            None,
                    "source_C_last_snapshot_date": None,
                    "source_C_snapshot_body_len":  None,
                    "source_C_timestamp":       datetime.now(timezone.utc).isoformat(),
                })

    all_results = existing_rows + new_results
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(all_results)

    live_n  = sum(1 for r in all_results if str(r.get("source_C_live")) == "True")
    dead_n  = sum(1 for r in all_results if str(r.get("source_C_live")) == "False")
    null_n  = sum(1 for r in all_results if r.get("source_C_live") is None or str(r.get("source_C_live")) == "None" or r.get("source_C_live") == "")
    elapsed = time.time() - t0

    print(f"\nWrote {len(all_results)} rows to {OUTPUT_CSV}")
    print(f"  source_C_live=True:  {live_n}")
    print(f"  source_C_live=False: {dead_n}")
    print(f"  null (never archived or fetch failed): {null_n}")
    print(f"  Runtime: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
