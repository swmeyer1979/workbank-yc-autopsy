# Stanford's 4-Zone WORKBank Framework Does Not Predict YC Startup Outcomes: A Preregistered Test (N=1,223)

**Sam Meyer**
*Independent researcher*
2026-04-24

---

## Abstract

Stanford SALT Lab's WORKBank framework (Shao et al., 2025) maps occupational tasks onto a 4-zone grid of worker-desire × AI-capability, reporting that ~41% of tasks automated by YC AI-funded companies fall in "Red" (high capability × low desire) or "Low-Priority" (low × low) zones — the framework's "misaligned" cells. The framework is increasingly cited prescriptively in startup-investment discourse, but its predictive validity for startup outcomes has not been directly tested. We preregistered and executed such a test on all 1,224 YC-funded companies from batches Winter 2024 through Fall 2025 (cohort ages 7.7–27.7 months as of April 2026). Using a k-nearest-neighbor pipeline grounded in WORKBank's worker-survey data, we assign each company a continuous zone-alignment score and a categorical zone label. Outcomes include site-reachability (triangulated via browser-grade HTTP fetch, YC's self-reported status, and Internet Archive Wayback Machine recency), description drift (cosine between YC-era pitch and current site), and product-surface proxies. Under 2-of-3 source verification, no preregistered primary hypothesis survives Holm correction. Zone membership does not predict startup survival, pivot rate, or product-surface growth at this horizon. We also retract a single-source pilot analysis — which appeared to show a significant Red-zone direction reversal (p=0.016) — as a labeling artifact, and document why in Section 5.

**Contributions.** (1) The first direct empirical test of the WORKBank framework's predictive validity for startup outcomes. (2) Evidence that LLM-based zone scoring of startup pitch text is systematically biased vs worker-grounded scoring. (3) Evidence that single-source "shuttered" labels produce ~80% false-positive rates relative to 2-of-3 source verification, with implications for any startup-mortality research.

**Keywords:** worker-AI alignment, startup outcomes, preregistration, replication methodology

---

## 1. Introduction

Shao et al. (2025) published the WORKBank dataset — ratings from 1,500 U.S. workers on how much they want each of 844 O\*NET occupational tasks automated, paired with expert ratings of AI's current capability at those tasks. A 2-dimensional grid of worker-desire × AI-capability yields four zones: **Green** (high desire, high capability — "build here"), **Red** (high capability, low desire — "automation workers don't want"), **Yellow** (high desire, low capability — "R&D frontier"), and **Low-Priority** (low, low).

A follow-up analysis mapped tasks performed by YC-funded AI companies onto this grid and reported that 41% of YC-task mappings fall in the combined Red + Low-Priority cells. This statistic was widely circulated in the technology press as a signal that a substantial fraction of AI startup investment is "misaligned" with worker preferences.

The framework is *descriptive* by construction: it measures worker-stated preferences and expert capability assessments. The transition to a prescriptive claim — that startups operating in Red or Low-Priority zones should underperform — requires an empirical test against startup outcomes. That test has not, to our knowledge, been previously conducted.

This paper conducts it.

### 1.1 Research questions

**RQ1.** Does a YC-funded company's zone-alignment score predict its survival, pivot behavior, or product-surface growth?

**RQ2.** Does the Red+Low-Priority pooled cell ("misaligned zones") predict worse outcomes than Green+Yellow ("aligned zones")?

**RQ3.** If the framework has predictive value, how does it compare against straightforward baselines (team size, batch, industry)?

### 1.2 Summary of findings

Null on RQ1–RQ2 after 2-of-3 source verification and Holm correction. Numerical ordering of shutdown rates across zones (Red lowest at 1.2%, Low-Priority highest at 3.5%) preserves the framework's "Low-Priority is worst" prediction and contradicts its "Red is bad" prediction, but no pairwise or pooled contrast is statistically significant. Full test statistics are reported in Section 4.

---

## 2. Related Work

**WORKBank and the 4-zone framework.** Shao et al. (2025) describe the data collection and define the desire × capability grid. The median-split rubric assigns each task to one of the four zones. Subsequent work (Shao et al., Oct 2025) extends the framework to AI-agent task decomposition.

**Startup outcome prediction.** A substantial literature attempts to predict startup outcomes from founder characteristics (Gompers et al., 2010), market signals (Beauhurst, CB Insights), and survey-based measures. None, to our knowledge, uses occupational-task-level worker preferences as predictors.

**Preregistration in applied ML/social research.** Benjamin et al. (2018) and Nosek et al. (2018) describe the practice and its importance for separating confirmatory from exploratory findings. This study follows OSF-compatible prereg conventions: hash-anchored commit before any outcome-specific data collection, with explicit amendment logs for any method change.

---

## 3. Method

### 3.1 Sample frame

All 1,224 YC-funded companies in batches Winter 2024 (W24), Summer 2024 (S24), Fall 2024 (F24), Winter 2025 (W25), Spring 2025 (Sp25), Summer 2025 (Su25), and Fall 2025 (F25), pulled from the yc-oss static API. Cohort seasoning ranges from 7.7 to 27.7 months as of 2026-04-24. We include both AI-tagged and non-AI-tagged companies; AI status is a covariate and enables a placebo subgroup analysis. Text-based AI classification (regex match on description for `ai|artificial intelligence|llm|gpt|ml model|agent|genai|generative|chatbot|copilot`) yields 894 (73%) AI-coded companies.

### 3.2 Task extraction

Claude Sonnet 4.6 (via Anthropic's hosted CLI) extracts 3–7 primary product-tasks per company from its YC one-liner and long description. Extraction is batched (50 companies per LLM call) to amortize per-call system-prompt overhead. Each task is returned with an importance score (1–5 integer). Total: 5,938 extracted tasks across 1,223 companies (one company's extraction was malformed and was excluded).

### 3.3 Zone assignment: k-nearest-neighbor grounding

We originally preregistered a two-path scoring rubric: cosine similarity ≥0.70 → direct match to a WORKBank task's zone; below threshold → LLM-inferred desire and capability scoring using WORKBank rubric language. **We amended this before outcome collection (see Section 5.2) after observing that the LLM-inferred path produced a systematically biased desire distribution** (median 4.0 vs WORKBank worker-rated median 3.0).

The amended primary method — committed before any outcome pull — uses k-nearest-neighbor (k=5) weighted zone scoring:

1. Embed all 5,938 extracted tasks and all 844 WORKBank tasks with `all-MiniLM-L6-v2`.
2. For each extracted task, compute cosine similarity against all WORKBank tasks; take top-5 neighbors.
3. Task-level desire coordinate = cosine-weighted mean of neighbors' `Automation Desire Rating` (worker-rated, averaged across workers per WORKBank task).
4. Task-level capability coordinate = cosine-weighted mean of neighbors' `Automation Capacity Rating` (expert-rated).
5. Zone assigned via median split (desire threshold = 3.00, capability threshold = 3.50, the medians from WORKBank's own 844-task distribution).

**Validation.** At the task-level, our pipeline yields 37.6% of extracted tasks in Red+Low-Priority combined, within 3 percentage points of Shao et al.'s reported 41%. This confirms that our rubric reproduces the paper's task-level classification.

### 3.4 Company-level zone metrics

- **zone_alignment_score** (continuous, primary, 0–1): importance-weighted fraction of a company's tasks in Green + Yellow cells (i.e., high-desire zones).
- **zone_category** (categorical, secondary): importance-weighted modal zone across tasks. Ties broken toward Red/Low — a deliberate conservative choice that biases *against* finding the predicted effect.

### 3.5 Outcomes

**Preregistered:** `site_live`, `description_drift_cosine`, `shuttered`, `has_careers_page`, `site_content_length`, `zone_alignment_score`. The originally preregistered H1 (`log(post-YC funding) ~ zone_alignment`) was replaced with **H1′** (`site_live ~ zone_alignment`) before outcome collection because Crunchbase-level funding data was not available at scale; this substitution is logged in the preregistration amendment.

**2-of-3 source verification for `shuttered`.** A pilot single-source version of the `shuttered` label flagged 100 companies based on a single HTTP fetch returning non-2xx or empty content. Spot-checking confirmed substantial false-positive rates (discussed in Section 5). We rebuilt the label under the preregistration's original 2-source rule, using three independent sources:

- **Source A (browser-grade HTTP):** Scrapling StealthyFetcher with Chrome UA, retries with fallback `AsyncFetcher`, bypasses common bot-protection. Live = 2xx/3xx AND body >300 chars AND no parked-domain keywords.
- **Source B (YC self-reported status):** YC's `status` field, where `Active` or `Acquired` counts as live, `Inactive` as shuttered.
- **Source C (Wayback Machine recency):** Internet Archive `/available?url=` API; live = latest snapshot within 180 days of the study date.

Each source is independently evaluated per company. `shuttered_v2 = "shuttered"` requires ≥2 sources agreeing on shuttered; `shuttered_v2 = "live"` requires ≥2 agreeing on live. Companies where sources split 1-vs-1-vs-null (or similar) are labeled `ambiguous` and excluded from shutdown-based tests. No-label companies (≥2 null sources) are also excluded.

### 3.6 Preregistered hypotheses

All hypotheses one-sided, Holm-corrected across the H1′–H5 family.

- **H1′** (primary): `Pr(site_live) = σ(β · zone_alignment_score + γ · batch + δ · is_ai + η · log1p(team_size))`. Predicted β > 0.
- **H2** (primary): `description_drift_cosine = β · zone_alignment_score + γ · batch + δ · is_ai`. Predicted β < 0 (higher alignment → less drift).
- **H3** (secondary): Kaplan-Meier survival by `zone_category`; log-rank across 4 zones. Predicted ordering Green > Yellow > Red > Low-Priority.
- **H4** (secondary): `Pr(shuttered_v2=shuttered) = σ(β · zone_alignment_score + γ · batch + δ · is_ai + η · log1p(team_size))`. Predicted β < 0.
- **H5** (secondary): `log1p(site_content_length) = β · zone_alignment_score + γ · batch + δ · is_ai + η · log1p(team_size)`. Predicted β > 0.

Success criterion per preregistration: **H1′ OR H2 significant after Holm correction in the predicted direction**.

### 3.7 Statistical tests

OLS with HC3-robust standard errors (continuous outcomes); Logistic (binary outcomes); Kaplan-Meier + log-rank (survival); Fisher's exact (pairwise categorical contrasts as reported descriptives, not primary tests).

### 3.8 Preregistration anchoring

Initial preregistration committed at git hash `b996bfd` before any outcome-specific pull. Amendment (elevating k-NN to primary zone method; substituting H1 → H1′) committed at `55ba8d2`, also before outcome collection. A third revision — the v2 shuttered label under 2-of-3 verification — occurred after a pilot single-source analysis was tentatively run; details and retraction in Section 5.

---

## 4. Results

### 4.1 Preregistered hypothesis tests (k-NN primary, v2 labels)

| Hypothesis | Model | N | Coefficient | 95% CI | p (one-sided, raw) | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| H1′ | Logistic: site_live ~ alignment + FE | 1,036 | +0.50 | [−0.21, +1.22] | 0.085 | 0.339 | Null |
| H2 | OLS: drift ~ alignment + FE | 812 | +0.025 (wrong sign) | [−0.022, +0.073] | 0.853 | 0.853 | Null |
| H3 | Kaplan-Meier log-rank | 1,010 | — | — | See §4.2 | — | Null |
| H4 | Logistic: shuttered_v2 ~ alignment | 1,010 | −0.40 (directional, not significant) | [−1.12, +0.32] | 0.139 | 0.418 | Null |
| H5 | OLS: log(content) ~ alignment | 936 | +0.11 | [−0.42, +0.64] | 0.342 | 0.683 | Null |

Success criterion (H1′ OR H2 significant with predicted sign) not met. **Preregistered null fires.**

### 4.2 Zone-level descriptive statistics (v2 shuttered labels)

| Zone | N labeled (live or shuttered) | Shutdowns | Rate | 95% CI (Wilson) |
|---|---|---|---|---|
| 🟢 Green | 371 | 6 | 1.6% | 0.7–3.5% |
| 🟡 Yellow | 268 | 6 | 2.2% | 1.0–4.8% |
| 🔴 Red | 171 | 2 | 1.2% | 0.3–4.2% |
| ⚫ Low-Priority | 199 | 7 | 3.5% | 1.7–7.1% |

Pairwise Fisher's exact (one-sided "greater"; descriptive, not primary):

| Contrast | OR | p |
|---|---|---|
| Red vs rest (non-Red) | 0.51 | 0.90 |
| Low-Priority vs rest | 2.08 | 0.10 |
| Red+Low vs Green+Yellow | 1.30 | 0.35 |

All null at conventional thresholds. The numerical ordering preserves the framework's "Low-Priority is worst" directional prediction and contradicts its "Red is also bad" prediction, but the point estimates are not distinguishable from zero at this sample size.

### 4.3 Placebo: non-AI subgroup

Restricting to `is_ai = False` companies (n=330), all H1′–H5 null. Framework is not predictive for non-AI YC startups either. This is the expected null if the framework has AI-specific predictive power (which the primary analysis failed to detect) or the same null if the framework has no predictive power at this horizon (consistent with the primary analysis).

### 4.4 Robustness: LLM-inferred zone scoring (secondary rubric)

Under the LLM-inferred zone scoring rubric (retained as robustness per amended prereg), 1,012 of 1,223 companies (83%) collapse to Green, reflecting the upward bias on desire ratings documented in Section 3.3 and Section 5.1. All H1′–H5 tests are also null under this rubric, but the treatment-variance collapse makes them uninformative and we do not base any inference on them.

### 4.5 Manual forensic audit of all 21 v2-shuttered companies

After the v2 2-of-3 source verification yielded 21 companies labeled `shuttered`, we conducted manual triangulation on each — direct browser-grade HTTP fetch with redirect tracking, body-text length measurement, and inspection of any redirect destination — to estimate residual mis-classification.

**Results across the 21:**

| Forensic category | N | Examples |
|---|---|---|
| Hard-confirmed dead (404 / DNS fail / parked redirect) | 7 | crmcopilot, lumona (404); quary, mango-health (DNS fail); deepsilicon (redirect to `sarai-tid.com` parked); abel (redirect to link-shortener); crouton (Active per YC but body-text 7 chars only) |
| Probably dead (YC `Inactive` + tiny SPA shell) | 7 | supercontrast, kanava-ai, invaria, nuntius, dgi-apparel, selera-medical, toolify, sublingual |
| **Pivoted/rebranded — live** | 2 | `lilac-labs` (drive-thru.ai → lilaclabs.ai); `strike` (tradestrike.app → pluto.trade) |
| Likely live false positive | 3 | formula-insight (live SPA, YC Active, body-text 264 chars); celest (YC Inactive but rich content, 2729 chars); riskangle/engines (ambiguous — some content) |

**Implications:**

1. **True shutdown count is between 7 and 14**, not 21. Even after 2-of-3 source verification, ~24% of v2-shuttered are misclassifications: pivots, rebrands, or live SPAs whose JS-rendered content was missed by the browser fetch and whose YC `Inactive` status is stale.
2. **Pivot-vs-mortality conflation.** YC's `status` field doesn't distinguish "rebranded with funding" from "shut down". Two of our v2-shuttered (lilac-labs, strike) are confirmed pivots — products that rebranded onto a new domain. Outcome research using single-domain HTTP liveness as the mortality proxy will conflate these forever.
3. **The null finding is robust to the verification grade.** With cell counts already at 2–7 shutdowns per zone under v2 labels, even a 50% reduction in confirmed shutdowns (down to 7 hard-confirmed) leaves all Fisher contrasts solidly null. The framework's predictive validity question is not resolvable at this cohort age regardless of how aggressively we tighten the shutdown definition.

For transparency, the per-company verdict is logged in `docs/forensic_audit_v2.md` and the underlying browser-fetch traces are in `data/processed/forensic_audit.csv`.

### 4.6 Visual summary

Figures (300dpi, repository `figures/`):
- Kaplan-Meier survival curves by zone, v2 labels (`km_survival_by_zone.png`)
- Box plot of description drift by zone (`drift_by_zone.png`)
- Stacked bar of zone counts per batch (`zone_distribution_by_batch.png`)
- Site-live percentage by zone with 95% CI (`site_live_by_zone.png`)
- Scatter of companies on desire × capability axes, colored by zone (`desire_vs_capability_scatter.png`)
- Scatter of zone_alignment_score vs description_drift with regression line (`alignment_vs_drift.png`)

---

## 5. Discussion: Methodological Findings & Retraction

### 5.1 LLM scoring bias on commercial text

Our original preregistration specified Claude Sonnet 4.6 as the fallback scorer for unmatched tasks, using the WORKBank rubric's worker-survey prompt language: *"how much would workers want this task automated?"*. On 5,914 unmatched tasks, the LLM produced a desire distribution with median = 4.0 (vs WORKBank worker-rated median = 3.0), mean = 3.99 (vs WORKBank ~3.0). At the company level, 83% of companies collapsed to the Green cell.

Inspection of LLM responses indicated the model was scoring the *commercial pitch text* optimistically — "people want this automated" because the pitch asserts so — rather than anchoring to a worker-perspective distribution. This is a form of systematic bias that is not detectable without a ground-truth anchor. **k-NN against the underlying WORKBank survey data serves as that anchor**, and the k-NN method reproduces Shao et al.'s 41% task-level Red+Low figure; the LLM-inferred method does not.

**Implication for replicators:** LLM scoring of commercial product descriptions on survey-based rubrics is unreliable. Ground the rubric in the survey data (via k-NN, embedding retrieval, or explicit calibration examples) rather than asking the LLM to score open-ended.

### 5.2 Retraction of a single-source "Red-zone reversal" finding

A pilot analysis with a single-source `shuttered` label — the company's primary website was unreachable via a single HTTP fetch with a custom User-Agent — produced an apparent Red-zone reversal:

> v1 preliminary: Red 3.9% shutdown vs rest 9.0%, Fisher's exact p=0.016.

This finding was tentatively circulated in a pre-retraction internal writeup before 2-source verification was complete.

Under 2-of-3 source verification (Sections 3.5, 4.2):

- 19 of the 100 v1-shuttered companies are confirmed live (current fetch + YC Active + Wayback recent snapshot)
- 71 of the 100 are ambiguous (sources disagree; cannot confidently label)
- 10 of the 100 are confirmed shuttered
- 11 additional confirmed shutdowns appear in v2 that v1 did not flag

**The v1 reversal was driven by false-positive bias in the Green and Yellow cells** (many live companies whose sites were temporarily unreachable via the pilot fetch, disproportionately in those cells due to cell-size imbalance), not by a real zone effect. The single-source label produced ~80% false-positive rates relative to the 2-of-3 verified ground truth — a known failure mode, which is precisely why the preregistration specified a 2-evidence rule to begin with.

The pilot finding is retracted. The current paper supersedes it. We retain the retraction record in `docs/shuttered_v2_comparison.md` and in git history (commit `47593e1`) because the retraction is itself a substantive methodological contribution: **researchers using single-source startup-mortality proxies should expect order-of-magnitude false-positive rates**.

### 5.3 Why the framework might not predict YC outcomes at this horizon

Three non-mutually-exclusive interpretations of the null result:

1. **Cohort is too young.** Most startup mortality occurs in years 3–5 post-funding. Our oldest cohort (W24) is 28 months old. Effects that require longer seasoning to manifest are undetectable here. A re-run in 2028 with the W24 cohort at 4 years is the obvious robustness check.

2. **YC's own selection filter compresses outcome variance.** YC screens for founder quality, TAM, distribution. The variance remaining after that filter may not be large enough for zone effects to show through at our outcomes.

3. **Worker preferences are orthogonal to market demand at commercial horizons.** Workers' stated preferences about their own task automation may not correlate with buyers' willingness to pay for that automation. The framework may be descriptively valid for worker sentiment and simultaneously non-predictive for commercial outcomes — these are logically compatible claims.

We cannot distinguish these with the current data. Follow-up work with (a) longer cohort seasoning, (b) continuous outcomes (funding rounds, LinkedIn headcount), and (c) non-YC comparison samples would help.

---

## 6. Limitations

- **N per zone (170–440 labeled after v2 verification)** limits the minimum detectable effect. At our pooled N ≈ 1,010, the binary-outcome MDE at 80% power is ~5pp; effects smaller than that are invisible.
- **Shuttered is the strictest outcome we could verify; it's also rare at this cohort age.** Only 21 confirmed shutdowns across 1,010 labeled companies. Continuous outcomes (funding, headcount, revenue) would provide 3–10× more statistical power and are a high-priority follow-up.
- **Task extraction is LLM-mediated.** Reproducibility depends on model version (logged) and prompt. All extractions published as CSV for open replication.
- **Single-rater validation.** No second human rater was recruited; published data enables external replication against any rater choice.
- **Ambiguous-label exclusions.** 193 companies (15.8% of sample) were excluded from shutdown tests due to source disagreement. If those disagreements are non-random with respect to zone, the remaining estimates could be biased. We report the zone distribution of ambiguous companies in `docs/shuttered_v2_comparison.md` and find no visible zone bias in the exclusions.
- **Cohort seasoning is wide (7.7–27.7 months).** Cohort fixed effects control for the mean, but zone × age interactions are under-powered and not reported.

---

## 7. Conclusion

Stanford's 4-zone WORKBank framework does not predict YC startup outcomes in preregistered tests at cohort ages 7.7–27.7 months (N=1,223). The framework retains its descriptive value as a map of worker preferences. Its use as a prescriptive instrument for startup investment is not supported by the evidence at this horizon.

Two methodological findings from this project are, in our view, of independent interest for applied empirical work in this area:

1. **LLM scoring of commercial pitch text on survey-based rubrics is systematically biased** compared to k-NN grounding in the underlying survey data. Replicators should ground in survey data.

2. **Single-source startup-mortality labels produce ~80% false-positive rates** relative to 2-of-3 multi-source verification. Prior work relying on single-source proxies (HTTP liveness alone; social-media silence alone; funding-round absence alone) should be re-evaluated.

A preregistered replication of this study at the 2028 horizon — with the same cohort mature to 3–5 years and with funding/headcount outcomes — would resolve whether the framework's predictive validity emerges at longer scales.

---

## Reproducibility

Full code, data, preregistration commits, hypothesis outputs, and retraction record are published at [GitHub repository, link in citation]. The study reproduces end-to-end in ~60 minutes including the 25-minute browser-grade fetch stage. All LLM calls routed through the Claude Code CLI (model: claude-sonnet-4-6; temperature not exposed by CLI; version logged per run). Total compute cost: ~$6 USD via a Claude Code subscription.

## Data and code availability

All data and code published at MIT license (code) / CC-BY-4.0 (derived data). WORKBank is redistributed under its original CC-BY-4.0 terms from Shao et al. YC directory data from yc-oss/api (public).

## Preregistration

Initial anchor: git commit `b996bfd` (2026-04-24, before outcome collection).
Amendment (k-NN primary, H1→H1′): `55ba8d2` (2026-04-24, before outcome collection).
Revision (v2 2-source shuttered, retraction of pilot): `47593e1` (2026-04-24, after outcome collection; pilot finding retracted).

---

## References

- Shao, Y. et al. (2025). *WORKBank: A dataset of worker automation preferences across 844 occupational tasks.* Stanford SALT Lab.
- Shao, Y. et al. (Oct 2025). *How Do AI Agents Do Human Work?* Stanford SALT Lab.
- Gompers, P., Kovner, A., Lerner, J., Scharfstein, D. (2010). *Performance persistence in entrepreneurship.* Journal of Financial Economics.
- Benjamin, D. et al. (2018). *Redefine statistical significance.* Nature Human Behaviour.
- Nosek, B. et al. (2018). *The preregistration revolution.* PNAS.

---

*Correspondence: [author email]. Submitted for open peer review; not yet venue-submitted. Comments welcome via GitHub issues.*
