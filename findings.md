# Stanford's WORKBank Framework on YC Data: A Preregistered Test

*An empirical test of whether Stanford SALT Lab's 4-zone framework (worker-desire × AI-capability) predicts YC startup outcomes. N=1,223 YC companies, batches Winter 2024 through Fall 2025. Preregistered. Full data + code on [GitHub](https://github.com/[user]/yc-workbank-postmortem-2026).*

## TL;DR

**Null.** Stanford's 4-zone framework does not predict YC startup outcomes at this cohort age (7.7–27.7 months of seasoning).

- No zone → site-live signal
- No zone → pivot / description-drift signal
- No zone → product-maturity signal
- No zone → mortality signal under 2-source verification

The framework captures worker preferences honestly. It does not translate into a market-prediction instrument at the early-stage YC window.

## The claim under test

Stanford's [WORKBank paper](https://futureofwork.saltlab.stanford.edu) mapped YC AI-company tasks onto a 4-zone grid:

| | High worker desire | Low worker desire |
|---|---|---|
| **High AI capability** | 🟢 Green: build here | 🔴 Red: automation workers don't want |
| **Low AI capability** | 🟡 Yellow: R&D frontier | ⚫ Low-Priority |

Headline stat picked up by Forbes: 41% of YC AI-company tasks fall in Red or Low-Priority — the "avoid these zones" framing. Implicit prediction, never tested: startups in those zones should underperform.

This project is that test.

## Method (full prereg at `docs/preregistration.md`, commit `b996bfd` + amendment `55ba8d2`)

**Sample.** All 1,224 YC companies W24, S24, F24, W25, Sp25, Su25, F25. Seasoning 7.7–27.7 months as of 2026-04-24.

**Zone assignment.** Sonnet 4.6 extracted 3–7 primary product-tasks from each company's YC description. Each task embedded and matched to top-5 nearest tasks in WORKBank's 844-task corpus. Zone coordinates = cosine-weighted mean of neighbors' worker-rated desire + expert-rated capability. Median split → zone.

We originally specified LLM-inferred scoring as the fallback for unmatched tasks. The LLM scored desire systematically higher than workers do (median 4.0 vs worker 3.0) — it scores startup pitches optimistically, not from the worker perspective. We amended the preregistration before outcome collection to elevate a k-NN grounded method to primary. **This methodological note is itself a finding:** LLM scoring of startup product text is unreliable for worker-framework applications. Ground the scoring in survey data throughout.

**Rubric validates Stanford's 41% claim.** Our k-NN pipeline yields 37.6% of extracted tasks in Red+Low at task-level — within 3pp of Stanford's 41%. The rubric is faithful to the paper.

**Outcomes (multi-source verification).**

1. `site_live` — two independent fetches (Scrapling StealthyFetcher + fallback) checking live content >300 chars
2. `yc_status_active` — YC's own self-reported status (Active / Inactive / Acquired); Acquired counts live, Inactive counts shuttered
3. `wayback_recent` — Internet Archive last snapshot within 180 days

**Shuttered label requires 2 of 3 sources to agree.** This is the preregistered 2-evidence rule, restored after a first-pass single-source version inflated the shuttered count with false positives. Details in the "Retraction" section below.

Other outcomes: description drift (cosine between YC-era description and current site meta/hero), content length (proxy for product maturity), careers-page presence.

Funding and LinkedIn headcount were not collected at scale (no free API). The original H1 "log funding ~ zone" was replaced with H1' "site_live ~ zone" before outcome pulls.

## Preregistered results (k-NN primary zone scores, v2 shuttered labels)

| Hypothesis | Model | N | Verdict |
|---|---|---|---|
| H1' | Logistic: site_live ~ zone_alignment + cohort FE + is_ai + log(team_size) | 1,036 | Null (Holm p=0.34) |
| H2 | OLS: drift ~ zone_alignment + cohort FE | 812 | Null (Holm p=0.85); point estimate wrong-signed |
| H3 | Kaplan-Meier log-rank, 4 zones | 1,010 | Null under 2-source; significant under single-source (driven by false-positive bias — see retraction) |
| H4 | Logistic: shuttered ~ zone_alignment + cohort FE + is_ai + log(team_size) | 1,010 | Null (Holm p=0.42+) |
| H5 | OLS: log(content_length) ~ zone_alignment + cohort FE | 936 | Null (Holm p=0.68) |

**All preregistered hypotheses null.** The continuous `zone_alignment_score` does not predict any outcome collected. The categorical zone splits show numerical differences but none survive appropriate verification and correction.

## Zone-level shutdown rates (2-source verified)

| Zone | N confident (live or shuttered) | Shutdown rate | 95% CI (Wilson) |
|---|---|---|---|
| 🟢 Green | 371 | 1.6% | 0.7–3.5% |
| 🟡 Yellow | 268 | 2.2% | 1.0–4.7% |
| 🔴 Red | 171 | 1.2% | 0.3–4.2% |
| ⚫ Low-Priority | 199 | 3.5% | 1.7–7.1% |

Fisher's exact, one-sided:

| Contrast | p |
|---|---|
| Red vs rest | 0.90 |
| Low-Priority vs rest | 0.10 |
| Red+Low vs Green+Yellow | 0.35 |

All null. 193 companies (15.8% of sample) could not be labeled because the 3 sources disagreed — those are excluded from shutdown tests.

**Red zone is still numerically lowest. Low-Priority is still numerically highest.** With N=21 confident shutdowns across 1,010 labeled companies, the sample cannot separate these numerical differences from noise at any conventional threshold.

## Retraction: single-source "Red-zone reversal" finding

An earlier draft of this post reported:

> Red zone shutters at 3.9% vs 9.0% elsewhere, Fisher p=0.016 — opposite of Stanford's prediction

**That finding does not survive 2-source verification.** The single-source label flagged 100 companies as shuttered based on one HTTP fetch failing. Under 2-of-3 verification:

- 19 of the 100 v1-shuttered are confirmed live (current HTTP 200 + YC Active + Wayback recent snapshot)
- 71 of the 100 are ambiguous (sources disagree; cannot label with confidence)
- Only 10 of the 100 are confirmed shuttered
- Plus 11 new confirmed shutdowns not flagged by v1

The v1 Red-zone "reversal" p=0.016 was an artifact of false-positive bias in the Green and Yellow cells (more live companies misread as shuttered) rather than a real zone effect. **The current post supersedes that draft.** The retraction is documented in `docs/shuttered_v2_comparison.md` and in this section for transparency.

This is exactly the failure mode the preregistration's 2-source rule was designed to prevent. The first-pass relaxation to 1 source was expedient but wrong. Keeping the retraction visible is part of the citation value of the project.

## What this means

**For Stanford's WORKBank:**

- The framework's descriptive value is intact. Task-level zone distribution reproduces across independent extractions.
- The framework's *market-predictive* value, at this horizon, is null. Zone membership does not predict startup survival, pivot, or product surface area at 7–27 months of seasoning.
- The "41% misaligned" framing in media coverage makes a prediction the data does not support at this stage. A 3–5 year horizon may reveal effects this study cannot.

**For VCs / operators:**

- Worker desire and AI capability are interesting lenses. They are not, on current evidence, diagnostic of startup outcomes.
- "Red zone" has not been shown to be a bad bet. It has also not been shown to be a good bet. The data is underpowered at this age cohort.

**For replicators:**

- LLM scoring of startup product descriptions is biased vs worker-grounded methods. Use k-NN against a survey-rated corpus.
- Single-source shutdown labels inflate false positives ~9×. Require at least 2 independent evidence streams.
- Cohort seasoning matters. Re-run this in 2028 when the W24 cohort is 4 years old and the failure signal has time to surface.

## Limitations (detailed in `docs/analysis_limitations.md`)

- Sample is YC-funded only, pre-filtered for founder quality. Framework effects may be compressed.
- N per zone at 170–440 supports medium effects (MDE ~5pp under v2 labeling); small effects (<3pp) are invisible.
- Outcomes do not include funding rounds or LinkedIn headcount; a richer outcome set could reveal effects the current proxies miss.
- Zone assignment is LLM-mediated. All extractions published for replication; single-rater choice documented.
- Cohort age range is wide; fixed effects control for batch, but interactions between zone and age are under-powered.

## What's citable

- Stanford's WORKBank 4-zone framework does not predict YC startup outcomes in preregistered tests at cohort ages 7.7–27.7 months (N=1,223).
- LLM scoring of startup pitch text is systematically biased upward on worker-desire compared to worker-grounded k-NN scoring — relevant for anyone applying WORKBank-style frameworks to commercial text.
- Single-source "shuttered" labels produce ~80% false-positive rates compared to 2-source verification. Prior work using single-source proxies for startup mortality should be re-evaluated.

Cite as:
> Meyer, S. (2026). *A preregistered test of Stanford's WORKBank 4-zone framework on YC startup outcomes (W24–F25, N=1,223). All primary hypotheses null under 2-source verification.* GitHub: [link]. 2026-04-24.

## Acknowledgements

Stanford SALT Lab for making WORKBank fully public. yc-oss for the YC directory static API. Internet Archive for the Wayback Machine API.

---

*All data, code, preregistration hashes (`b996bfd`, `55ba8d2`), hypothesis results, retraction record, and figures are in the repo. Reproduce end-to-end in ~60 min including the 25-minute browser-grade fetch stage.*
