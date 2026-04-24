"""
05_build_analysis_frame.py
Join all source tables into a single analysis.csv for hypothesis testing.
H1 substitution: H1' uses site_live ~ zone_alignment_score (logistic)
because funding data was not collected.

Shuttered label:
  - shuttered_v2  (primary): 2-of-3 sources agree (browser fetch, YC status, Wayback).
    Values: live | shuttered | ambiguous | no_label
  - shuttered_v1_singlesource (legacy, kept for transparency):
    original single-source label (site_live=False AND fetch_skipped_reason is null).
"""

import pandas as pd
import numpy as np
from datetime import date

ANALYSIS_DATE = date(2026, 4, 24)

# ── Load sources ──────────────────────────────────────────────────────────────
yc = pd.read_csv("data/processed/yc_companies.csv")
knn = pd.read_csv("data/processed/company_zone_scores_knn.csv")
llm = pd.read_csv("data/processed/company_zone_scores.csv")
out = pd.read_csv("data/processed/outcomes.csv")

# ── cohort_months / is_mature ─────────────────────────────────────────────────
# cohort_start is YYYY-MM string; compute months to 2026-04-24
def months_since(cohort_str):
    y, m = map(int, cohort_str.split("-"))
    return (ANALYSIS_DATE.year - y) * 12 + (ANALYSIS_DATE.month - m)

yc["cohort_months"] = yc["cohort_start"].apply(months_since)
yc["is_mature"] = yc["cohort_months"] >= 18

# ── knn columns ───────────────────────────────────────────────────────────────
# knn has no low_signal column; derive from llm.low_signal via slug merge
knn_sel = knn.rename(columns={
    "knn_zone_alignment_score": "zone_alignment_score",
    "knn_zone_category":        "zone_category",
    "knn_mean_desire":          "mean_desire",
    "knn_mean_capability":      "mean_capability",
})[[
    "slug", "zone_alignment_score", "zone_category",
    "mean_desire", "mean_capability", "n_tasks",
]]

# low_signal from llm table (both share slug)
low_sig = llm[["slug", "low_signal"]].copy()
knn_sel = knn_sel.merge(low_sig, on="slug", how="left")

# ── llm columns ───────────────────────────────────────────────────────────────
llm_sel = llm[["slug", "zone_alignment_score", "zone_category"]].rename(columns={
    "zone_alignment_score": "zone_alignment_score_llm",
    "zone_category":        "zone_category_llm",
})

# ── outcomes ──────────────────────────────────────────────────────────────────
out_sel = out[[
    "slug", "site_live", "description_drift_cosine",
    "has_careers_page", "site_content_length", "fetch_skipped_reason",
]]

# ── shuttered_v1_singlesource: original 1-source proxy (kept for transparency)
# site_live=False AND fetch_skipped_reason is null
out_sel = out_sel.copy()
out_sel["shuttered_v1_singlesource"] = (
    (out_sel["site_live"] == False) &
    (out_sel["fetch_skipped_reason"].isna())
)

# ── shuttered_v2 (primary): 2-of-3 sources must agree ─────────────────────────
import os as _os
_shuttered_v2_path = "data/processed/shuttered_v2.csv"
if _os.path.exists(_shuttered_v2_path):
    sv2 = pd.read_csv(_shuttered_v2_path)[[
        "slug", "shuttered_v2", "shuttered_v2_confidence",
        "source_A_live", "source_B_live", "source_C_live",
        "sources_n_live", "sources_n_dead", "sources_n_null",
    ]]
else:
    import warnings
    warnings.warn(
        "shuttered_v2.csv not found — run 04b/04c/04d + 07_merge_shuttered.py first. "
        "Falling back to v1 single-source label as shuttered_v2.",
        stacklevel=1,
    )
    sv2 = out_sel[["slug", "shuttered_v1_singlesource"]].copy()
    sv2["shuttered_v2"] = sv2["shuttered_v1_singlesource"].map(
        {True: "shuttered", False: "live"}
    )
    sv2["shuttered_v2_confidence"] = "none"
    for col in ("source_A_live", "source_B_live", "source_C_live",
                "sources_n_live", "sources_n_dead", "sources_n_null"):
        sv2[col] = None

# Primary binary shuttered flag for downstream tests
# shuttered=True iff shuttered_v2 == 'shuttered'
# ambiguous / no_label → NaN (excluded from tests)
sv2 = sv2.copy()
sv2["shuttered"] = sv2["shuttered_v2"].map(
    {"shuttered": True, "live": False}
)  # ambiguous / no_label → NaN

# ── Join ──────────────────────────────────────────────────────────────────────
yc_cols = [
    "slug", "name", "batch", "team_size", "is_ai",
    "website", "one_liner", "long_description",
    "cohort_months", "is_mature",
]
df = (
    yc[yc_cols]
    .merge(knn_sel,  on="slug", how="left")
    .merge(llm_sel,  on="slug", how="left")
    .merge(out_sel,  on="slug", how="left")
    .merge(sv2,      on="slug", how="left")
)

print(f"Analysis frame: {df.shape}")
print(f"  zone_alignment_score non-null: {df['zone_alignment_score'].notna().sum()}")
print(f"  site_live non-null:            {df['site_live'].notna().sum()}")
print(f"  drift non-null:                {df['description_drift_cosine'].notna().sum()}")
print(f"  shuttered_v1 (single-source):  {df['shuttered_v1_singlesource'].sum()}")
print(f"  shuttered_v2=shuttered:        {(df['shuttered_v2'] == 'shuttered').sum()}")
print(f"  shuttered_v2=live:             {(df['shuttered_v2'] == 'live').sum()}")
print(f"  shuttered_v2=ambiguous:        {(df['shuttered_v2'] == 'ambiguous').sum()}")
print(f"  shuttered_v2=no_label:         {(df['shuttered_v2'] == 'no_label').sum()}")
print(f"  shuttered (primary, binary):   {df['shuttered'].sum()}")
print(f"  is_mature:                     {df['is_mature'].sum()}")

df.to_csv("data/processed/analysis.csv", index=False)
print("Saved: data/processed/analysis.csv")
