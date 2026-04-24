# Preregistration — YC × WORKBank Postmortem

**Committed:** 2026-04-24 (before outcome-specific data pulls)
**Author:** Sam Meyer
**OSF mirror:** _pending_

## What is prereg'd here

Hypotheses, sample frame, zone rubric, outcome variables, primary statistical tests, and decision rules — all fixed *before* any outcome-specific data collection (LinkedIn scraping, funding queries, current-site fetches, description-drift computation). Commit hash of this file is the prereg anchor; any change post-outcome-pull must be flagged as exploratory.

## What was observed before commit (disclosure)

Only static YC directory fields from the [yc-oss/api](https://github.com/yc-oss/api) dump:
- Company name, one_liner, long_description, batch, team_size, industry, URL
- YC's self-reported `status` field (Active / Inactive / Acquired): 1186 / 29 / 9

This exposure to YC's `status` is unavoidable since it's in the same static JSON as the base frame. It is **not** used as a primary outcome (self-report by YC lags reality; base Inactive rate of 2.4% across 27mo of seasoning is implausibly low).

WORKBank CSVs were pulled and task-level zones derived, but no company-to-task mapping has been computed.

## Sample frame

- **Frame:** all 1,224 YC companies in batches W24, S24, F24, W25, Sp25, Su25, F25.
- **AI dummy:** `is_ai` = one_liner OR long_description matches `\b(ai|artificial intelligence|llm|gpt|machine learning|ml model|agent|genai|generative|chatbot|copilot)\b`. Not used as a filter; used as a covariate and for stratified subgroup analyses.

## Zone rubric (fixed)

**Task-level zones from WORKBank (n=844 tasks with both axes):**
- `desire_mean` = mean `Automation Desire Rating` across workers per Task ID
- `capability_mean` = mean `Automation Capacity Rating` across experts per Task ID
- Zone = median split on both axes (desire median = 3.00, capability median = 3.50)
- Distribution: Green 281 / Yellow 190 / Red 161 / Low-Priority 212 (Red+Low share = 44.2%, within 3pp of Stanford's 41% report → rubric validated)

**Company-level zone-alignment score:**
1. Extract 3–7 primary product-tasks per company via Sonnet 4.6 on `one_liner + long_description + (landing-page hero text if fetchable)`.
2. Each extracted task → nearest-neighbor in WORKBank via sentence embedding (cosine ≥ 0.70 = matched).
3. Unmatched tasks → Sonnet 4.6 scores desire (1–5) + capability (1–5) using the WORKBank paper's rubric verbatim; zone assigned via same median split.
4. `zone_alignment_score` (continuous, primary) = weighted fraction of company's tasks in Green+Yellow (high-desire zones). Weights = task-importance ranks from extraction step.
5. `zone_category` (categorical, secondary) = modal zone across tasks; ties broken toward Red/Low (biases *against* the thesis).
6. `zone_source` ∈ {matched, inferred, mixed} logged per task for subset analyses.

## Hypotheses (pre-specified, one-sided)

**H1 (primary, continuous):** `log(post-YC $ raised + 1) ~ zone_alignment_score + cohort_FE + is_ai + log(team_size)`. Coefficient on `zone_alignment_score` > 0 (higher alignment → more funding).

**H2 (primary, continuous):** `description_drift_cosine ~ zone_alignment_score + cohort_FE + is_ai`. Coefficient < 0 (higher alignment → less drift from original thesis).

**H3 (secondary, survival):** Kaplan-Meier survival by `zone_category`, log-rank test across 4 zones. Outcome = company-shuttered. Predicted ordering (decreasing survival): Green > Yellow > Red > Low-Priority.

**H4 (secondary, binary):** Pooled `shuttered_OR_dormant ~ zone_alignment_score`, logistic, with cohort FE. Coefficient < 0.

**H5 (secondary, continuous):** `log(LinkedIn_headcount_current / team_size_at_YC) ~ zone_alignment_score + cohort_FE + is_ai`. Coefficient > 0.

## Outcome definitions (to be collected after this commit)

- **site_live** (bool): current-site HTTP fetch returns 2xx AND contains >100 non-boilerplate chars AND domain not parked. Two-fetch verification 48h apart.
- **linkedin_headcount** (int): current employee count from LinkedIn company page; null if page missing.
- **funding_total_post_yc** (USD, log+1): sum of announced rounds post-YC-batch date. Sources: Crunchbase (if key obtained), TechCrunch, VC press coverage, founder tweets. Null if no signal.
- **founder_still_listed** (bool): primary founder LinkedIn headline still references the company.
- **description_drift_cosine** (float, 0–1): cosine distance between YC `long_description` embedding and current-site hero/meta-description embedding (both embedded with `all-MiniLM-L6-v2`).
- **shuttered** (bool): (site_live=False AND linkedin_headcount=null) OR YC status=Inactive AND no funding in 18mo. Two independent evidence sources required.
- **dormant** (bool, for H4): site_live=True AND linkedin_headcount < team_size_at_YC AND no funding in 12mo.
- **t_event** (months): months from batch-start to first of {shuttered, acquired}; right-censored at 2026-04-24.

## Statistical tests

- **H1, H2, H5:** OLS with robust (HC3) SE. Also run with cohort FE + `is_ai × zone_alignment_score` interaction. Report coefficient, 95% CI, one-sided p-value.
- **H3:** Kaplan-Meier + log-rank; Cox PH with `cohort` as frailty.
- **H4:** Logistic, cohort FE, robust SE.
- **Secondary:** AI vs non-AI subgroup analysis (is_ai=0 as natural placebo — framework shouldn't predict non-AI startup survival).
- **Multiple-comparisons:** Holm correction across H1–H5 for the "Stanford framework is predictive" omnibus claim.

## Decision rules

- **Success:** H1 OR H2 significant after Holm correction at α=0.05 **AND** sign consistent with prediction. Headline: "Stanford framework predicts YC AI-startup trajectory."
- **Null:** No H1–H5 significant. Headline: "Stanford framework does not predict YC startup outcomes." Publish anyway.
- **Reversal:** Significant effect in opposite direction on H1 or H2. Headline: "Red-zone YC startups outperform — workers say no, market says yes."

All three headlines are pre-drafted in `marketing/`.

## Inter-rater validation

Single human rater (Sam) for zone extraction. Full rubric + all task-extractions + embedding distances published as CSV for open replication. No second rater (single-rater with transparent rubric > Sonnet-as-rater-2 theater with correlated errors). This choice is a deliberate departure from the more expensive 2-rater design; flagged here so readers can weight accordingly.

## Exclusions & caveats

- Cohorts <12mo seasoned (Summer 2025, Fall 2025) excluded from primary mortality analyses; included in funding/headcount analyses with shorter windows.
- Chinese/non-US-locale companies with LinkedIn unavailable: marked as `linkedin_headcount=null`, excluded from H5 only.
- Companies with `one_liner + long_description < 50 words`: zone-alignment flagged as `low_signal`, excluded from H1–H5 primary, reported separately.
- Task extraction is LLM-based; reproducibility depends on model version (logged). Temperature = 0.

## What is *not* prereg'd (exploratory, will be labeled)

- Any subgroup analysis beyond `is_ai` and `cohort`.
- Named-company examples in findings post (selected after outcomes pulled; factual-only language).
- Any alternative rubric (quartile split, continuous interaction) — flagged exploratory if used.

## Power (from `docs/power_analysis.md`)

Primary continuous H1/H2: Cohen's d=0.3 → 72% power at pooled N≈900. Secondary binary H4: MDE ≈13pp at pooled N. Small-effect (<0.2 d) results underpowered; will be reported with explicit null-finding framing.

## Timestamp + commit hash

This file's git commit hash is the prereg anchor. Any data edit or hypothesis modification after the hash-setting commit is flagged exploratory.
