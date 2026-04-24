"""
07_merge_shuttered.py — 2-of-3 shuttered label merge.

Joins:
  - data/processed/outcomes_browser.csv    (Source A: browser fetch)
  - data/processed/outcomes_yc_status.csv  (Source B: YC self-reported status)
  - data/processed/outcomes_wayback.csv    (Source C: Wayback recency)

Merge logic for shuttered_v2:
  - Live      if ≥2 sources say live
  - Shuttered if ≥2 sources say shuttered
  - Ambiguous if 1 says live, 1 says shuttered, 1 is null
  - No-label  if ≥2 sources are null

shuttered_v2_confidence:
  - high = all 3 non-null sources agree
  - low  = 2 of 3 agree (1 disagrees or is null)

Output: data/processed/shuttered_v2.csv
Columns: slug, source_A_live, source_B_live, source_C_live,
         shuttered_v2, shuttered_v2_confidence,
         sources_n_live, sources_n_dead, sources_n_null
"""

import csv
import os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_A = os.path.join(BASE, "data", "processed", "outcomes_browser.csv")
SOURCE_B = os.path.join(BASE, "data", "processed", "outcomes_yc_status.csv")
SOURCE_C = os.path.join(BASE, "data", "processed", "outcomes_wayback.csv")
YC_CSV   = os.path.join(BASE, "data", "processed", "yc_companies.csv")
OUTPUT   = os.path.join(BASE, "data", "processed", "shuttered_v2.csv")

OUTPUT_COLUMNS = [
    "slug",
    "source_A_live", "source_B_live", "source_C_live",
    "shuttered_v2", "shuttered_v2_confidence",
    "sources_n_live", "sources_n_dead", "sources_n_null",
]


def parse_bool(val) -> bool | None:
    """Parse CSV boolean string → Python bool or None."""
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    return None  # 'none', '', 'null', etc.


def load_index(path: str, key_col: str, val_col: str) -> dict[str, bool | None]:
    """Load a CSV into slug → bool|None dict."""
    result: dict[str, bool | None] = {}
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found — source will be all-null")
        return result
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            slug = row.get(key_col, "").strip()
            if slug:
                result[slug] = parse_bool(row.get(val_col))
    return result


def classify(a: bool | None, b: bool | None, c: bool | None) -> tuple[str, str]:
    """
    Returns (shuttered_v2, shuttered_v2_confidence).
    shuttered_v2 ∈ {live, shuttered, ambiguous, no_label}
    confidence   ∈ {high, low, none}
    """
    votes = [v for v in (a, b, c) if v is not None]
    n_live = sum(1 for v in votes if v is True)
    n_dead = sum(1 for v in votes if v is False)
    n_null = 3 - len(votes)

    if n_null >= 2:
        return "no_label", "none"

    if n_live >= 2:
        label = "live"
    elif n_dead >= 2:
        label = "shuttered"
    else:
        # exactly 1 live, 1 dead, 1 null
        label = "ambiguous"

    # confidence
    if len(votes) == 3 and (n_live == 3 or n_dead == 3):
        conf = "high"
    elif label in ("live", "shuttered"):
        conf = "low"
    else:
        conf = "none"

    return label, conf


def main() -> None:
    # Load all slugs from yc_companies (master list)
    with open(YC_CSV, newline="", encoding="utf-8") as f:
        slugs = [r["slug"].strip() for r in csv.DictReader(f)]
    print(f"Master slug list: {len(slugs)}")

    src_a = load_index(SOURCE_A, "slug", "source_A_live")
    src_b = load_index(SOURCE_B, "slug", "source_B_live")
    src_c = load_index(SOURCE_C, "slug", "source_C_live")

    print(f"  Source A loaded: {len(src_a)} slugs")
    print(f"  Source B loaded: {len(src_b)} slugs")
    print(f"  Source C loaded: {len(src_c)} slugs")

    rows = []
    label_counts: Counter = Counter()

    for slug in slugs:
        a = src_a.get(slug)
        b = src_b.get(slug)
        c = src_c.get(slug)

        n_live = sum(1 for v in (a, b, c) if v is True)
        n_dead = sum(1 for v in (a, b, c) if v is False)
        n_null = sum(1 for v in (a, b, c) if v is None)

        label, conf = classify(a, b, c)
        label_counts[label] += 1

        rows.append({
            "slug":                    slug,
            "source_A_live":           a,
            "source_B_live":           b,
            "source_C_live":           c,
            "shuttered_v2":            label,
            "shuttered_v2_confidence": conf,
            "sources_n_live":          n_live,
            "sources_n_dead":          n_dead,
            "sources_n_null":          n_null,
        })

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUTPUT}")
    print(f"  live:      {label_counts['live']}")
    print(f"  shuttered: {label_counts['shuttered']}")
    print(f"  ambiguous: {label_counts['ambiguous']}")
    print(f"  no_label:  {label_counts['no_label']}")

    # Confidence breakdown for shuttered
    shuttered_high = sum(1 for r in rows if r["shuttered_v2"] == "shuttered"
                         and r["shuttered_v2_confidence"] == "high")
    shuttered_low  = sum(1 for r in rows if r["shuttered_v2"] == "shuttered"
                         and r["shuttered_v2_confidence"] == "low")
    print(f"\n  shuttered high-conf: {shuttered_high}")
    print(f"  shuttered low-conf:  {shuttered_low}")


if __name__ == "__main__":
    main()
