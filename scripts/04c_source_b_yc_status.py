"""
04c_source_b_yc_status.py — Source B for 2-of-3 shuttered label.

YC self-reported status from yc_companies.csv:
  status ∈ {Active, Inactive, Acquired}

source_B_live = (status != 'Inactive')
  - 'Active'   → live
  - 'Acquired' → live  (YC lists acquired separately from dead; acquired ≠ shuttered)
  - 'Inactive' → shuttered

Output: data/processed/outcomes_yc_status.csv
Columns: slug, source_B_status, source_B_live
"""

import csv
import os

BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV  = os.path.join(BASE, "data", "processed", "yc_companies.csv")
OUTPUT_CSV = os.path.join(BASE, "data", "processed", "outcomes_yc_status.csv")

OUTPUT_COLUMNS = ["slug", "source_B_status", "source_B_live"]


def main() -> None:
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        companies = list(csv.DictReader(f))
    print(f"Loaded {len(companies)} companies")

    rows = []
    for c in companies:
        slug   = c.get("slug", "").strip()
        status = c.get("status", "").strip()
        # Acquired counts as live — YC distinguishes acquired from inactive/dead
        live = (status != "Inactive") if status else None
        rows.append({
            "slug":           slug,
            "source_B_status": status or None,
            "source_B_live":  live,
        })

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    live_n    = sum(1 for r in rows if r["source_B_live"] is True)
    dead_n    = sum(1 for r in rows if r["source_B_live"] is False)
    null_n    = sum(1 for r in rows if r["source_B_live"] is None)
    inactive  = sum(1 for r in rows if r["source_B_status"] == "Inactive")
    acquired  = sum(1 for r in rows if r["source_B_status"] == "Acquired")
    active    = sum(1 for r in rows if r["source_B_status"] == "Active")

    print(f"\nWrote {len(rows)} rows to {OUTPUT_CSV}")
    print(f"  Active:   {active} → source_B_live=True")
    print(f"  Acquired: {acquired} → source_B_live=True")
    print(f"  Inactive: {inactive} → source_B_live=False")
    print(f"  null:     {null_n}")
    print(f"  source_B_live=True:  {live_n}")
    print(f"  source_B_live=False: {dead_n}")


if __name__ == "__main__":
    main()
