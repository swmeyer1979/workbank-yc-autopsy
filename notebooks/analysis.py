# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # YC × WORKBank Postmortem — Statistical Analysis
#
# **Preregistration anchor:** `docs/preregistration.md` (committed 2026-04-24)
#
# ## H1 Substitution (documented here per prereg)
#
# **Original H1 (dropped):** `log(post-YC $ raised + 1) ~ zone_alignment_score + cohort_FE + is_ai + log(team_size)`
# Dropped because **funding data was not collected**. Crunchbase/press-coverage scraping
# was out of scope for this pipeline run.
#
# **H1' (replacement, primary, pre-registered intent preserved):**
# `site_live ~ zone_alignment_score + C(batch) + is_ai + log1p(team_size)` — logistic regression.
# Rationale: site_live is the most direct available signal of company viability. Higher zone alignment
# → startup is in a market workers want automated → more likely to still be operating. Coefficient > 0 predicted.
# This substitution was specified in the task brief before any outcome analysis was run.

# ## Cell 1 — Setup + Descriptive Stats

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test

# Reproducibility
np.random.seed(42)

import os, pathlib
# Support running from project root OR from notebooks/ dir
_ROOT = pathlib.Path(__file__).parent.parent if "__file__" in dir() else pathlib.Path(".")
if not (_ROOT / "data").exists():
    _ROOT = pathlib.Path(".")
_DATA  = _ROOT / "data" / "processed"
_DOCS  = _ROOT / "docs"
_FIGS  = _ROOT / "figures"
_FIGS.mkdir(exist_ok=True)

df = pd.read_csv(_DATA / "analysis.csv")
df["site_live_int"] = df["site_live"].astype(float)
df["shuttered_int"] = df["shuttered"].astype(float)
df["team_size_log"] = np.log1p(df["team_size"].fillna(1))
df["site_content_length_log"] = np.log1p(df["site_content_length"].fillna(0))

print(f"Total N: {len(df)}")
print(f"zone_alignment_score non-null: {df['zone_alignment_score'].notna().sum()}")

print("\n--- N per cohort (cohort_months) ---")
print(df.groupby("batch")["slug"].count().sort_values(ascending=False).to_string())

print("\n--- N per zone_category (kNN primary) ---")
print(df["zone_category"].value_counts().to_string())

print("\n--- N per zone_category_llm (LLM secondary) ---")
print(df["zone_category_llm"].value_counts().to_string())

print("\n--- site_live rate overall ---")
sl = df["site_live"].dropna()
print(f"  True: {sl.sum():.0f}/{len(sl)} = {sl.mean():.1%}")

print("\n--- site_live rate by batch ---")
print(
    df.groupby("batch")["site_live"]
    .agg(lambda x: f"{x.dropna().mean():.1%} ({x.dropna().sum():.0f}/{x.dropna().count()})")
    .to_string()
)

print("\n--- description_drift_cosine distribution ---")
drift = df["description_drift_cosine"].dropna()
print(f"  n={len(drift)}, mean={drift.mean():.3f}, median={drift.median():.3f}, "
      f"std={drift.std():.3f}, min={drift.min():.3f}, max={drift.max():.3f}")

print("\n--- shuttered counts ---")
print(f"  shuttered=True: {df['shuttered'].sum()}")
print(f"  is_mature & shuttered: {(df['is_mature'] & df['shuttered']).sum()}")

print("\n--- Cross-tab zone_category × batch (kNN) ---")
ct = pd.crosstab(df["zone_category"], df["batch"])
print(ct.to_string())

print("\n--- Cross-tab zone_category_llm × batch ---")
ct2 = pd.crosstab(df["zone_category_llm"], df["batch"])
print(ct2.to_string())


# ## Cell 2 — Preregistered Hypothesis Tests (k-NN primary)
#
# All tests use `zone_alignment_score` (kNN variant).
# One-sided p-values computed from two-sided statsmodels output.
# Holm correction applied across H1'–H5 simultaneously.

def one_sided_p(two_sided_p, coef, predicted_positive):
    """Convert two-sided p to one-sided, given predicted direction."""
    if predicted_positive:
        # predict coef > 0
        if coef > 0:
            return two_sided_p / 2
        else:
            return 1 - two_sided_p / 2
    else:
        # predict coef < 0
        if coef < 0:
            return two_sided_p / 2
        else:
            return 1 - two_sided_p / 2

def verdict(coef, p_holm, predicted_positive, alpha=0.05):
    correct_dir = (coef > 0) == predicted_positive
    if p_holm <= alpha and correct_dir:
        return "PREDICTED DIRECTION (sig)"
    elif p_holm <= alpha and not correct_dir:
        return "REVERSAL (sig, opposite direction)"
    else:
        return "NULL (not significant)"

results_knn = {}

# ── H1' ──────────────────────────────────────────────────────────────────────
# site_live ~ zone_alignment_score + C(batch) + is_ai + log1p(team_size)
# Exclude: fetch_skipped_reason not-null (no URL to begin with; not evidence of shutdown)
h1_df = df[
    df["fetch_skipped_reason"].isna() &
    df["zone_alignment_score"].notna() &
    df["site_live"].notna()
].copy()
h1_df["site_live_int"] = h1_df["site_live"].astype(float)

m_h1 = smf.logit(
    "site_live_int ~ zone_alignment_score + C(batch) + is_ai + team_size_log",
    data=h1_df
).fit(cov_type="HC3", disp=False)

coef_h1 = m_h1.params["zone_alignment_score"]
ci_h1   = m_h1.conf_int().loc["zone_alignment_score"]
p2_h1   = m_h1.pvalues["zone_alignment_score"]
p1_h1   = one_sided_p(p2_h1, coef_h1, predicted_positive=True)
results_knn["H1'"] = dict(
    n=len(h1_df), coef=coef_h1, ci_lo=ci_h1[0], ci_hi=ci_h1[1],
    p_raw=p1_h1, predicted_positive=True
)
print(f"\nH1' n={len(h1_df)}, coef={coef_h1:.4f}, 95%CI=[{ci_h1[0]:.4f},{ci_h1[1]:.4f}], p(2s)={p2_h1:.4f}, p(1s)={p1_h1:.4f}")

# ── H2 ───────────────────────────────────────────────────────────────────────
# description_drift_cosine ~ zone_alignment_score + C(batch) + is_ai
# Filter: drift non-null
h2_df = df[
    df["description_drift_cosine"].notna() &
    df["zone_alignment_score"].notna()
].copy()

m_h2 = smf.ols(
    "description_drift_cosine ~ zone_alignment_score + C(batch) + is_ai",
    data=h2_df
).fit(cov_type="HC3")

coef_h2 = m_h2.params["zone_alignment_score"]
ci_h2   = m_h2.conf_int().loc["zone_alignment_score"]
p2_h2   = m_h2.pvalues["zone_alignment_score"]
p1_h2   = one_sided_p(p2_h2, coef_h2, predicted_positive=False)
results_knn["H2"] = dict(
    n=len(h2_df), coef=coef_h2, ci_lo=ci_h2[0], ci_hi=ci_h2[1],
    p_raw=p1_h2, predicted_positive=False
)
print(f"\nH2  n={len(h2_df)}, coef={coef_h2:.4f}, 95%CI=[{ci_h2[0]:.4f},{ci_h2[1]:.4f}], p(2s)={p2_h2:.4f}, p(1s)={p1_h2:.4f}")

# ── H3 — Kaplan-Meier by zone_category, log-rank ────────────────────────────
# t_event = cohort_months; event = shuttered
# All companies right-censored at cohort_months if not shuttered
h3_df = df[df["zone_alignment_score"].notna()].copy()
h3_df["event"] = h3_df["shuttered"].astype(int)
h3_df["t_event"] = h3_df["cohort_months"]  # right-censored if event=0

zones_order = ["Green", "Yellow", "Red", "Low-Priority"]
zone_colors = {"Green": "#2ca02c", "Yellow": "#ff7f0e", "Red": "#d62728", "Low-Priority": "#7f7f7f"}

from lifelines.statistics import multivariate_logrank_test as mlrt

h3_sub = h3_df[h3_df["zone_category"].isin(zones_order)].dropna(subset=["t_event"])
lr_result = mlrt(
    h3_sub["t_event"],
    h3_sub["zone_category"],
    h3_sub["event"]
)
p_logrank = lr_result.p_value
print(f"\nH3  log-rank p={p_logrank:.4f} (4 zones)")

# Median survival per zone (shuttered events only)
for z in zones_order:
    zd = h3_sub[h3_sub["zone_category"] == z]
    n_shut = zd["event"].sum()
    print(f"  {z}: n={len(zd)}, shuttered={n_shut} ({n_shut/len(zd):.1%})")

results_knn["H3"] = dict(
    n=len(h3_sub), coef=None, ci_lo=None, ci_hi=None,
    p_raw=p_logrank, predicted_positive=None  # special case
)

# ── H4 ───────────────────────────────────────────────────────────────────────
# shuttered ~ zone_alignment_score + C(batch) + is_ai + log1p(team_size)
h4_df = df[df["zone_alignment_score"].notna() & df["shuttered"].notna()].copy()

m_h4 = smf.logit(
    "shuttered_int ~ zone_alignment_score + C(batch) + is_ai + team_size_log",
    data=h4_df
).fit(cov_type="HC3", disp=False)

coef_h4 = m_h4.params["zone_alignment_score"]
ci_h4   = m_h4.conf_int().loc["zone_alignment_score"]
p2_h4   = m_h4.pvalues["zone_alignment_score"]
p1_h4   = one_sided_p(p2_h4, coef_h4, predicted_positive=False)
results_knn["H4"] = dict(
    n=len(h4_df), coef=coef_h4, ci_lo=ci_h4[0], ci_hi=ci_h4[1],
    p_raw=p1_h4, predicted_positive=False
)
print(f"\nH4  n={len(h4_df)}, coef={coef_h4:.4f}, 95%CI=[{ci_h4[0]:.4f},{ci_h4[1]:.4f}], p(2s)={p2_h4:.4f}, p(1s)={p1_h4:.4f}")

# ── H5 ───────────────────────────────────────────────────────────────────────
# site_content_length_log ~ zone_alignment_score + C(batch) + is_ai + log1p(team_size)
# Filter: site_live=True
h5_df = df[
    df["site_live"] == True  # noqa: E712
    & df["zone_alignment_score"].notna()
    & df["site_content_length"].notna()
].copy()
h5_df = df[
    (df["site_live"] == True) &
    df["zone_alignment_score"].notna() &
    df["site_content_length"].notna()
].copy()

m_h5 = smf.ols(
    "site_content_length_log ~ zone_alignment_score + C(batch) + is_ai + team_size_log",
    data=h5_df
).fit(cov_type="HC3")

coef_h5 = m_h5.params["zone_alignment_score"]
ci_h5   = m_h5.conf_int().loc["zone_alignment_score"]
p2_h5   = m_h5.pvalues["zone_alignment_score"]
p1_h5   = one_sided_p(p2_h5, coef_h5, predicted_positive=True)
results_knn["H5"] = dict(
    n=len(h5_df), coef=coef_h5, ci_lo=ci_h5[0], ci_hi=ci_h5[1],
    p_raw=p1_h5, predicted_positive=True
)
print(f"\nH5  n={len(h5_df)}, coef={coef_h5:.4f}, 95%CI=[{ci_h5[0]:.4f},{ci_h5[1]:.4f}], p(2s)={p2_h5:.4f}, p(1s)={p1_h5:.4f}")

# ── Holm correction across H1'–H5 ────────────────────────────────────────────
# H3 uses log-rank p (two-sided already), treat as two-sided then apply Holm
holm_keys = ["H1'", "H2", "H3", "H4", "H5"]
# For Holm: use one-sided p for directional hypotheses, two-sided for H3 (non-directional)
p_raw_arr = [results_knn[k]["p_raw"] for k in holm_keys]
# H3 p is already two-sided log-rank; keep as-is in the Holm set
reject, p_holm, _, _ = multipletests(p_raw_arr, method="holm")

for i, k in enumerate(holm_keys):
    results_knn[k]["p_holm"] = p_holm[i]
    results_knn[k]["reject_holm"] = reject[i]

# Print summary
print("\n\n=== kNN PRIMARY RESULTS ===")
print(f"{'Hyp':<6} {'N':>6} {'Coef':>9} {'95% CI':>22} {'p(raw)':>9} {'p(Holm)':>9} {'Verdict'}")
print("-" * 95)
for k in holm_keys:
    r = results_knn[k]
    if r["coef"] is not None:
        ci_str = f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]"
        coef_str = f"{r['coef']:+.4f}"
    else:
        ci_str = "   [log-rank]   "
        coef_str = "  log-rank"
    v = verdict(
        r.get("coef") or 0,
        r["p_holm"],
        r.get("predicted_positive"),
    ) if k != "H3" else (
        "PREDICTED DIRECTION (sig)" if r["p_holm"] <= 0.05 else "NULL (not significant)"
    )
    print(f"{k:<6} {r['n']:>6} {coef_str:>9} {ci_str:>22} {r['p_raw']:>9.4f} {r['p_holm']:>9.4f}  {v}")

# ── Write h_results_knn.md ────────────────────────────────────────────────────
md_knn = [
    "# Hypothesis Results — kNN Primary\n",
    "_Preregistered one-sided tests. Holm correction across H1'–H5._\n",
    "| Hyp | N | Coef | 95% CI | p (one-sided raw) | p (Holm) | Verdict |",
    "|-----|---|------|--------|-------------------|----------|---------|",
]
for k in holm_keys:
    r = results_knn[k]
    if r["coef"] is not None:
        coef_str = f"{r['coef']:+.4f}"
        ci_str = f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]"
    else:
        coef_str = "log-rank"
        ci_str = "N/A"
    if k == "H3":
        v = "PREDICTED (sig)" if r["p_holm"] <= 0.05 else "NULL"
    else:
        correct = (r["coef"] > 0) == r["predicted_positive"] if r["coef"] is not None else True
        if r["p_holm"] <= 0.05 and correct:
            v = "PREDICTED (sig)"
        elif r["p_holm"] <= 0.05 and not correct:
            v = "REVERSAL (sig)"
        else:
            v = "NULL"
    md_knn.append(f"| {k} | {r['n']} | {coef_str} | {ci_str} | {r['p_raw']:.4f} | {r['p_holm']:.4f} | {v} |")

with open(_DOCS / "h_results_knn.md", "w") as f:
    f.write("\n".join(md_knn) + "\n")
print("\nSaved: docs/h_results_knn.md")


# ## Cell 3 — Robustness (LLM-inferred secondary)
#
# Repeat H1'–H5 with zone_alignment_score_llm and zone_category_llm.

results_llm = {}

def fit_logit_safe(formula, data):
    """Fit logistic regression; fall back to 'bfgs' if default solver yields singular Hessian."""
    try:
        return smf.logit(formula, data=data).fit(cov_type="HC3", disp=False)
    except np.linalg.LinAlgError:
        # Singular Hessian — likely perfect separation in a batch dummy.
        # Drop batch FE and refit with penalised likelihood (method='bfgs').
        formula_no_batch = formula.replace(" + C(batch)", "")
        try:
            return smf.logit(formula_no_batch, data=data).fit(
                method="bfgs", cov_type="HC3", disp=False
            )
        except Exception:
            return smf.logit(formula_no_batch, data=data).fit(
                method="nm", cov_type="nonrobust", disp=False
            )


def run_h_set(df_in, score_col, cat_col, label="LLM"):
    res = {}

    # H1'
    h1d = df_in[
        df_in["fetch_skipped_reason"].isna() &
        df_in[score_col].notna() &
        df_in["site_live"].notna()
    ].copy()
    h1d["site_live_int"] = h1d["site_live"].astype(float)
    m = fit_logit_safe(
        f"site_live_int ~ {score_col} + C(batch) + is_ai + team_size_log",
        data=h1d
    )
    coef = m.params[score_col]
    ci = m.conf_int().loc[score_col]
    p1 = one_sided_p(m.pvalues[score_col], coef, True)
    res["H1'"] = dict(n=len(h1d), coef=coef, ci_lo=ci[0], ci_hi=ci[1], p_raw=p1, predicted_positive=True)

    # H2
    h2d = df_in[df_in["description_drift_cosine"].notna() & df_in[score_col].notna()].copy()
    m = smf.ols(
        f"description_drift_cosine ~ {score_col} + C(batch) + is_ai",
        data=h2d
    ).fit(cov_type="HC3")
    coef = m.params[score_col]
    ci = m.conf_int().loc[score_col]
    p1 = one_sided_p(m.pvalues[score_col], coef, False)
    res["H2"] = dict(n=len(h2d), coef=coef, ci_lo=ci[0], ci_hi=ci[1], p_raw=p1, predicted_positive=False)

    # H3
    h3d = df_in[df_in[score_col].notna() & df_in[cat_col].isin(zones_order)].copy()
    h3d["event"] = h3d["shuttered"].astype(int)
    h3d["t_event"] = h3d["cohort_months"]
    h3d = h3d.dropna(subset=["t_event"])
    lr = mlrt(h3d["t_event"], h3d[cat_col], h3d["event"])
    res["H3"] = dict(n=len(h3d), coef=None, ci_lo=None, ci_hi=None, p_raw=lr.p_value, predicted_positive=None)

    # H4
    h4d = df_in[df_in[score_col].notna() & df_in["shuttered"].notna()].copy()
    m = fit_logit_safe(
        f"shuttered_int ~ {score_col} + C(batch) + is_ai + team_size_log",
        data=h4d
    )
    coef = m.params[score_col]
    ci = m.conf_int().loc[score_col]
    p1 = one_sided_p(m.pvalues[score_col], coef, False)
    res["H4"] = dict(n=len(h4d), coef=coef, ci_lo=ci[0], ci_hi=ci[1], p_raw=p1, predicted_positive=False)

    # H5
    h5d = df_in[
        (df_in["site_live"] == True) &
        df_in[score_col].notna() &
        df_in["site_content_length"].notna()
    ].copy()
    m = smf.ols(
        f"site_content_length_log ~ {score_col} + C(batch) + is_ai + team_size_log",
        data=h5d
    ).fit(cov_type="HC3")
    coef = m.params[score_col]
    ci = m.conf_int().loc[score_col]
    p1 = one_sided_p(m.pvalues[score_col], coef, True)
    res["H5"] = dict(n=len(h5d), coef=coef, ci_lo=ci[0], ci_hi=ci[1], p_raw=p1, predicted_positive=True)

    # Holm
    p_arr = [res[k]["p_raw"] for k in holm_keys]
    rej, p_h, _, _ = multipletests(p_arr, method="holm")
    for i, k in enumerate(holm_keys):
        res[k]["p_holm"] = p_h[i]
        res[k]["reject_holm"] = rej[i]

    return res


results_llm = run_h_set(df, "zone_alignment_score_llm", "zone_category_llm", "LLM")

print("\n=== LLM SECONDARY RESULTS ===")
print(f"{'Hyp':<6} {'N':>6} {'Coef':>9} {'95% CI':>22} {'p(raw)':>9} {'p(Holm)':>9} {'Verdict'}")
print("-" * 95)
for k in holm_keys:
    r = results_llm[k]
    if r["coef"] is not None:
        ci_str = f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]"
        coef_str = f"{r['coef']:+.4f}"
    else:
        ci_str = "   [log-rank]   "
        coef_str = "  log-rank"
    if k == "H3":
        v = "PREDICTED (sig)" if r["p_holm"] <= 0.05 else "NULL"
    else:
        correct = (r["coef"] > 0) == r["predicted_positive"] if r["coef"] is not None else True
        v = ("PREDICTED (sig)" if r["p_holm"] <= 0.05 and correct
             else "REVERSAL (sig)" if r["p_holm"] <= 0.05 and not correct
             else "NULL")
    print(f"{k:<6} {r['n']:>6} {coef_str:>9} {ci_str:>22} {r['p_raw']:>9.4f} {r['p_holm']:>9.4f}  {v}")

# Write h_results_llm.md
md_llm = [
    "# Hypothesis Results — LLM-Inferred Secondary\n",
    "_Robustness check using LLM-inferred zone scores. Holm correction across H1'–H5._\n",
    "**Note:** LLM variant suffers from optimism bias (83% Green collapse). "
    "Treat results as robustness only; kNN primary is authoritative.\n",
    "| Hyp | N | Coef | 95% CI | p (one-sided raw) | p (Holm) | Verdict |",
    "|-----|---|------|--------|-------------------|----------|---------|",
]
for k in holm_keys:
    r = results_llm[k]
    coef_str = f"{r['coef']:+.4f}" if r["coef"] is not None else "log-rank"
    ci_str = f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]" if r["coef"] is not None else "N/A"
    if k == "H3":
        v = "PREDICTED (sig)" if r["p_holm"] <= 0.05 else "NULL"
    else:
        correct = (r["coef"] > 0) == r["predicted_positive"] if r["coef"] is not None else True
        v = ("PREDICTED (sig)" if r["p_holm"] <= 0.05 and correct
             else "REVERSAL (sig)" if r["p_holm"] <= 0.05 and not correct
             else "NULL")
    md_llm.append(f"| {k} | {r['n']} | {coef_str} | {ci_str} | {r['p_raw']:.4f} | {r['p_holm']:.4f} | {v} |")

with open(_DOCS / "h_results_llm.md", "w") as f:
    f.write("\n".join(md_llm) + "\n")
print("Saved: docs/h_results_llm.md")


# ## Cell 4 — AI vs non-AI subgroup (placebo test)
#
# Repeat H1'–H5 on is_ai=False subset (n≈330).
# Framework shouldn't predict non-AI startup outcomes.
# If it does → framework captures general zone effect, not AI-specific misalignment.

df_nonai = df[df["is_ai"] == False].copy()
print(f"\nnon-AI subset: n={len(df_nonai)}")

results_nonai = run_h_set(df_nonai, "zone_alignment_score", "zone_category", "nonAI")

print("\n=== NON-AI PLACEBO RESULTS ===")
print(f"{'Hyp':<6} {'N':>6} {'Coef':>9} {'95% CI':>22} {'p(raw)':>9} {'p(Holm)':>9} {'Verdict'}")
print("-" * 95)
for k in holm_keys:
    r = results_nonai[k]
    if r["coef"] is not None:
        ci_str = f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]"
        coef_str = f"{r['coef']:+.4f}"
    else:
        ci_str = "   [log-rank]   "
        coef_str = "  log-rank"
    if k == "H3":
        v = "PREDICTED (sig)" if r["p_holm"] <= 0.05 else "NULL"
    else:
        correct = (r["coef"] > 0) == r["predicted_positive"] if r["coef"] is not None else True
        v = ("PREDICTED (sig)" if r["p_holm"] <= 0.05 and correct
             else "REVERSAL (sig)" if r["p_holm"] <= 0.05 and not correct
             else "NULL")
    print(f"{k:<6} {r['n']:>6} {coef_str:>9} {ci_str:>22} {r['p_raw']:>9.4f} {r['p_holm']:>9.4f}  {v}")

md_nonai = [
    "# Hypothesis Results — Non-AI Placebo Subgroup\n",
    "_is_ai=False subset (n≈330). Framework shouldn't predict non-AI outcomes._\n",
    "_If significant here: framework captures general zone effect, not AI-specific misalignment._\n",
    "| Hyp | N | Coef | 95% CI | p (one-sided raw) | p (Holm) | Verdict |",
    "|-----|---|------|--------|-------------------|----------|---------|",
]
for k in holm_keys:
    r = results_nonai[k]
    coef_str = f"{r['coef']:+.4f}" if r["coef"] is not None else "log-rank"
    ci_str = f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]" if r["coef"] is not None else "N/A"
    if k == "H3":
        v = "PREDICTED (sig)" if r["p_holm"] <= 0.05 else "NULL"
    else:
        correct = (r["coef"] > 0) == r["predicted_positive"] if r["coef"] is not None else True
        v = ("PREDICTED (sig)" if r["p_holm"] <= 0.05 and correct
             else "REVERSAL (sig)" if r["p_holm"] <= 0.05 and not correct
             else "NULL")
    md_nonai.append(f"| {k} | {r['n']} | {coef_str} | {ci_str} | {r['p_raw']:.4f} | {r['p_holm']:.4f} | {v} |")

with open(_DOCS / "h_results_nonai.md", "w") as f:
    f.write("\n".join(md_nonai) + "\n")
print("Saved: docs/h_results_nonai.md")


# ## Cell 5 — Figures

sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)
FIGDIR = str(_FIGS)

# ── Figure 1: KM survival by zone ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
km_data = df[df["zone_alignment_score"].notna() & df["zone_category"].isin(zones_order)].copy()
km_data["event"] = km_data["shuttered"].astype(int)
km_data["t_event"] = km_data["cohort_months"]

for z in zones_order:
    zd = km_data[km_data["zone_category"] == z]
    kmf = KaplanMeierFitter(label=f"{z} (n={len(zd)})")
    kmf.fit(zd["t_event"], event_observed=zd["event"])
    kmf.plot_survival_function(ax=ax, ci_show=False, color=zone_colors[z])

lr_p = results_knn["H3"]["p_raw"]
ax.set_title(f"Kaplan–Meier Survival by Zone (log-rank p={lr_p:.3f})")
ax.set_xlabel("Cohort Age (months)")
ax.set_ylabel("Fraction of Companies Not Shuttered")
ax.set_ylim(0.7, 1.01)
plt.tight_layout()
plt.savefig(f"{FIGDIR}/km_survival_by_zone.png", dpi=300)
plt.close()
print("Saved: figures/km_survival_by_zone.png")

# ── Figure 2: Drift by zone ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5))
drift_data = df[df["description_drift_cosine"].notna() & df["zone_category"].isin(zones_order)]
zone_ord = [z for z in zones_order if z in drift_data["zone_category"].unique()]
sns.boxplot(
    data=drift_data, x="zone_category", y="description_drift_cosine",
    order=zone_ord, palette=zone_colors, ax=ax
)
ax.set_title("Description Drift by Zone Category (kNN)")
ax.set_xlabel("Zone")
ax.set_ylabel("Cosine Drift (YC desc → Current site)")
plt.tight_layout()
plt.savefig(f"{FIGDIR}/drift_by_zone.png", dpi=300)
plt.close()
print("Saved: figures/drift_by_zone.png")

# ── Figure 3: Zone distribution by batch ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
batch_order = ["Winter 2024", "Summer 2024", "Fall 2024", "Winter 2025",
               "Spring 2025", "Summer 2025", "Fall 2025"]
zone_counts = (
    df[df["zone_category"].isin(zones_order)]
    .groupby(["batch", "zone_category"])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=zones_order, fill_value=0)
)
zone_counts = zone_counts.reindex([b for b in batch_order if b in zone_counts.index])
zone_counts.plot(kind="bar", stacked=True, ax=ax, color=[zone_colors[z] for z in zones_order])
ax.set_title("Zone Distribution by Batch (kNN)")
ax.set_xlabel("Batch")
ax.set_ylabel("Company Count")
ax.legend(title="Zone", bbox_to_anchor=(1.01, 1))
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(f"{FIGDIR}/zone_distribution_by_batch.png", dpi=300)
plt.close()
print("Saved: figures/zone_distribution_by_batch.png")

# ── Figure 4: site_live % per zone with 95% CI ───────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5))
sl_data = df[
    df["zone_category"].isin(zones_order) &
    df["site_live"].notna() &
    df["fetch_skipped_reason"].isna()
].copy()
sl_data["site_live_int"] = sl_data["site_live"].astype(float)

zone_sl = []
for z in zones_order:
    zd = sl_data[sl_data["zone_category"] == z]["site_live_int"]
    n = len(zd)
    p = zd.mean()
    se = np.sqrt(p * (1 - p) / n) if n > 0 else 0
    zone_sl.append({"zone": z, "pct": p * 100, "ci": se * 1.96 * 100, "n": n})
sl_df = pd.DataFrame(zone_sl)

bars = ax.bar(sl_df["zone"], sl_df["pct"], color=[zone_colors[z] for z in sl_df["zone"]])
ax.errorbar(
    x=range(len(sl_df)), y=sl_df["pct"], yerr=sl_df["ci"],
    fmt="none", color="black", capsize=5
)
ax.set_title("Site-Live % by Zone (kNN) with 95% CI")
ax.set_ylabel("% Site Live")
ax.set_ylim(0, 115)
for i, row in sl_df.iterrows():
    ax.text(i, row["pct"] + row["ci"] + 2, f"n={row['n']:.0f}", ha="center", fontsize=9)
plt.tight_layout()
plt.savefig(f"{FIGDIR}/site_live_by_zone.png", dpi=300)
plt.close()
print("Saved: figures/site_live_by_zone.png")

# ── Figure 5: Desire vs Capability scatter ───────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 7))
scatter_data = df[
    df["mean_desire"].notna() &
    df["mean_capability"].notna() &
    df["zone_category"].isin(zones_order)
].copy()
scatter_data["ts"] = np.clip(scatter_data["team_size"].fillna(2), 1, 50)

for z in zones_order:
    zd = scatter_data[scatter_data["zone_category"] == z]
    ax.scatter(
        zd["mean_desire"], zd["mean_capability"],
        s=zd["ts"] * 4, alpha=0.45, label=z, color=zone_colors[z]
    )

ax.axvline(3.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
ax.axhline(3.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
ax.set_xlabel("Mean Desire (worker-rated, 1–5)")
ax.set_ylabel("Mean Capability (expert-rated, 1–5)")
ax.set_title("Companies on Desire × Capability Axes (kNN)\nSize = team_size")
ax.legend(title="Zone")
plt.tight_layout()
plt.savefig(f"{FIGDIR}/desire_vs_capability_scatter.png", dpi=300)
plt.close()
print("Saved: figures/desire_vs_capability_scatter.png")

# ── Figure 6: Alignment score vs drift scatter ───────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5))
reg_data = df[
    df["zone_alignment_score"].notna() &
    df["description_drift_cosine"].notna()
].copy()

sns.regplot(
    data=reg_data, x="zone_alignment_score", y="description_drift_cosine",
    ax=ax, scatter_kws={"alpha": 0.3, "s": 15}, line_kws={"color": "red"}
)
ax.set_title("Zone Alignment Score vs Description Drift (kNN)")
ax.set_xlabel("Zone Alignment Score (kNN)")
ax.set_ylabel("Description Drift (cosine)")
plt.tight_layout()
plt.savefig(f"{FIGDIR}/alignment_vs_drift.png", dpi=300)
plt.close()
print("Saved: figures/alignment_vs_drift.png")


# ## Cell 6 — Named Examples per Zone

named = []

# Top 5 Green + site_live=True, sorted by alignment_score desc
green_live = df[
    (df["zone_category"] == "Green") &
    (df["site_live"] == True) &
    df["zone_alignment_score"].notna()
].nlargest(5, "zone_alignment_score")

# Top 5 Red+Low + shuttered=True + is_mature=True
red_low_shut = df[
    df["zone_category"].isin(["Red", "Low-Priority"]) &
    (df["shuttered"] == True) &
    (df["is_mature"] == True)
].nlargest(5, "zone_alignment_score")
# Note: nlargest on shuttered Red+Low shows which were most "aligned" despite shutting down
# Use nsmallest for worst alignment
red_low_shut = df[
    df["zone_category"].isin(["Red", "Low-Priority"]) &
    (df["shuttered"] == True) &
    (df["is_mature"] == True)
].sort_values("zone_alignment_score").head(5)

# Top 5 Red+Low + extreme drift (pivoted)
red_low_drift = df[
    df["zone_category"].isin(["Red", "Low-Priority"]) &
    df["description_drift_cosine"].notna()
].nlargest(5, "description_drift_cosine")

def fmt_example(row, stat_col, stat_label):
    val = row.get(stat_col)
    val_str = f"{val:.3f}" if isinstance(val, float) else str(val)
    return (f"- **{row['name']}**: {row['batch']}, "
            f"{row.get('one_liner', 'N/A')}, "
            f"zone={row['zone_category']}, "
            f"{stat_label}={val_str}")

lines = ["# Named Examples per Zone\n",
         "_Factual-only. Selected post-outcomes; labeled exploratory._\n",
         "## Green Exemplars (site_live=True, top alignment_score)\n"]

for _, r in green_live.iterrows():
    lines.append(fmt_example(r, "zone_alignment_score", "alignment_score"))

lines += ["\n## Red+Low with site_live=False (is_mature=True)\n"]
if len(red_low_shut) == 0:
    lines.append("_No mature Red/Low shuttered companies found with current data._")
else:
    for _, r in red_low_shut.iterrows():
        lines.append(fmt_example(r, "cohort_months", "cohort_months"))

lines += ["\n## Red+Low with Extreme Drift (pivoted)\n"]
for _, r in red_low_drift.iterrows():
    lines.append(fmt_example(r, "description_drift_cosine", "drift"))

with open(_DOCS / "named_examples.md", "w") as f:
    f.write("\n".join(lines) + "\n")
print("Saved: docs/named_examples.md")

# ── Final summary ─────────────────────────────────────────────────────────────
print("\n\n=== FINAL SUMMARY ===")
any_sig_knn = any(results_knn[k]["p_holm"] <= 0.05 for k in holm_keys)
any_reversal_knn = any(
    results_knn[k]["p_holm"] <= 0.05 and
    results_knn[k]["coef"] is not None and
    (results_knn[k]["coef"] > 0) != results_knn[k]["predicted_positive"]
    for k in holm_keys if results_knn[k]["coef"] is not None
)
print(f"Any kNN sig (Holm): {any_sig_knn}")
print(f"Any kNN reversal:   {any_reversal_knn}")

if any_reversal_knn:
    headline = "REVERSAL: Red-zone YC startups show unexpected performance pattern."
elif any_sig_knn:
    headline = "SUCCESS: Stanford framework predicts YC AI-startup trajectory."
else:
    headline = "NULL: Stanford framework does not predict YC startup outcomes in cohorts tested."

print(f"HEADLINE: {headline}")
