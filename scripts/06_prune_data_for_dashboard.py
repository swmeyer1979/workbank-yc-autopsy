#!/usr/bin/env python3
"""Prune analysis.csv for dashboard payload."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "processed" / "analysis.csv"
OUT_DIR = ROOT / "dashboard" / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEEP = [
    "slug", "name", "batch", "website", "one_liner", "team_size",
    "is_ai", "cohort_months", "zone_alignment_score", "zone_category",
    "n_tasks", "site_live", "description_drift_cosine", "shuttered",
]

FLOATS = {"zone_alignment_score", "description_drift_cosine", "cohort_months"}

def clean(row):
    out = {}
    for col in KEEP:
        v = row.get(col, "")
        if col in FLOATS:
            try:
                f = float(v)
                out[col] = round(f, 3) if not math.isnan(f) else None
            except (ValueError, TypeError):
                out[col] = None
        elif col == "team_size":
            try:
                out[col] = int(float(v)) if v not in ("", "None") else None
            except (ValueError, TypeError):
                out[col] = None
        elif col == "n_tasks":
            try:
                out[col] = int(float(v)) if v not in ("", "None") else None
            except (ValueError, TypeError):
                out[col] = None
        elif col in ("is_ai", "site_live", "shuttered"):
            out[col] = v.strip().lower() in ("true", "1", "yes")
        else:
            out[col] = v.strip() if v else None
    return out

rows = []
with open(SRC, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(clean(row))

with open(OUT_DIR / "companies.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, separators=(",", ":"))

# summary.json
zone_counts = {}
for r in rows:
    z = r.get("zone_category") or "Unknown"
    zone_counts[z] = zone_counts.get(z, 0) + 1

total = len(rows)
site_live = sum(1 for r in rows if r.get("site_live"))
shuttered = sum(1 for r in rows if r.get("shuttered"))
drifts = [r["description_drift_cosine"] for r in rows if r.get("description_drift_cosine") is not None]
mean_drift = round(sum(drifts) / len(drifts), 3) if drifts else None

batches = sorted(set(r["batch"] for r in rows if r.get("batch")))

summary = {
    "total": total,
    "site_live": site_live,
    "shuttered": shuttered,
    "mean_drift": mean_drift,
    "zone_counts": zone_counts,
    "batches": batches,
}

with open(OUT_DIR / "summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(f"Written {len(rows)} companies to {OUT_DIR / 'companies.json'}")
print(f"Summary: {summary}")
