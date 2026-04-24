# Stanford's WORKBank Framework on YC Data: A Preregistered Test

*An empirical test of whether Stanford SALT Lab's 4-zone framework (worker-desire × AI-capability) predicts startup outcomes. N=1,223 YC companies, batches Winter 2024 through Fall 2025. Preregistered. Full data + code on [GitHub](https://github.com/[user]/yc-workbank-postmortem-2026).*

## TL;DR

**The preregistered primary hypotheses are null.** Zone alignment does not predict whether a YC company's site stays up, drifts in description, or appears shuttered.

**But zone-level disaggregation reveals a direction reversal that contradicts the framework's main claim:**

- **Red zone** (high AI-capability × low worker-desire — "building automation workers don't want") shuts down at **3.9% vs 9.0%** elsewhere. Fisher p=0.016. **Opposite of predicted.**
- **Low-Priority zone** (low capability × low desire) shuts down at **11.0% vs 7.4%** elsewhere. Fisher p=0.072. Predicted direction, marginal.
- Stanford grouped these two zones together as the "41% misaligned" claim. Our data: **those two effects cancel** (Red+Low combined 7.8% vs Green+Yellow 8.4%, p=0.83).

The framework differentiates zones — log-rank across all four is p=0.031 — but not in the direction the "zones to avoid" framing predicts.

## Why this matters

Stanford's [WORKBank paper](https://futureofwork.saltlab.stanford.edu) made news with the stat: 41% of YC AI-company tasks are in "Red" or "Low-Priority" zones — software workers don't want, or aren't asking for. The implication, picked up by Forbes and others: startups building in those zones are misreading the market.

Nobody tested whether those startups actually underperform. This project is that test.

## Method (compressed — full prereg at `docs/preregistration.md`)

**Sample.** All 1,224 YC companies from W24, S24, F24, W25, Sp25, Su25, F25. Seasoning range: 7.7–27.7 months as of 2026-04-24.

**Zone assignment.** For each company, Sonnet 4.6 extracted 3–7 primary product-tasks from the YC description. Each extracted task was then matched to the 5 nearest tasks in WORKBank's 844-task corpus via sentence embedding (`all-MiniLM-L6-v2`). Zone coordinates = cosine-weighted mean of neighbors' worker-rated desire + expert-rated capability. Median split → zone.

*A note on method:* We originally specified LLM-inferred desire/capability scoring as the fallback for unmatched tasks. The LLM systematically scored desire higher than workers do (median 4.0 vs worker 3.0) — it scores startup pitches optimistically, not from the worker's perspective. We amended the preregistration before outcome collection to elevate the k-NN variant to primary. The LLM-inferred variant is retained as a secondary robustness check, and all hypotheses are reported on both.

**Task-level rubric validates.** Our k-NN method reproduces Stanford's 41% claim almost exactly: 37.6% of extracted tasks fall in Red+Low-Priority zones. Rubric is faithful.

**Outcomes.** Automated collection of:
- `site_live` — company's website currently reachable with substantive content
- `description_drift` — cosine distance between YC-era description and current site hero/meta
- `has_careers_page` — proxy for hiring activity
- `site_content_length` — proxy for product maturity
- `shuttered` — site not reachable / parked / empty, with URL present at YC launch

Funding and LinkedIn headcount were not collected (no free API for scalable coverage); the original H1 "log funding ~ zone" was replaced with H1': "site_live ~ zone" before outcome pulls.

## Preregistered results (k-NN primary)

| Hypothesis | Model | N | Coefficient | 95% CI | p (1-sided, Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1' | Logistic: site_live ~ alignment + FE | 1,036 | +0.50 | [−0.21, +1.22] | 0.34 | **Null** |
| H2 | OLS: drift ~ alignment + FE | 812 | +0.03 (wrong sign) | [−0.02, +0.07] | 0.85 | **Null** |
| H3 | KM log-rank, 4 zones | 1,223 | — | — | **0.031** | **Sig — but ordering reversed for Red** |
| H4 | Logistic: shuttered ~ alignment + FE | 1,223 | −0.40 | [−1.12, +0.32] | 0.42 | **Null** |
| H5 | OLS: log(content_length) ~ alignment + FE | 936 | +0.11 | [−0.42, +0.64] | 0.68 | **Null** |

Decision rule per preregistration: success requires H1' or H2 significant with correct sign. Neither is. **Null headline fires.**

## The zone-level disaggregation (exploratory)

While the preregistered continuous tests are null, the categorical survival test is significant. Pairwise contrasts on shutdown rate (Fisher's exact, all cohorts pooled):

| Zone | Shutdown rate | 95% CI (Wilson) | N |
|---|---|---|---|
| 🔴 Red | **3.9%** | 2.0–7.6% | 204 |
| 🟢 Green | 6.8% | 4.8–9.5% | 443 |
| 🟡 Yellow | 10.6% | 7.7–14.4% | 321 |
| ⚫ Low-Priority | 11.0% | 7.7–15.5% | 255 |

| Contrast | p (Fisher) |
|---|---|
| Red vs rest | **0.016** |
| Low-Priority vs rest | 0.072 |
| Red+Low vs Green+Yellow | 0.83 (null) |

**Stanford's rhetorical bundling of Red + Low-Priority as "zones to avoid" combines two effects running in opposite directions.** Red beats baseline. Low-Priority underperforms baseline. Pooled, they cancel.

These are exploratory (not in the primary prereg list), pairwise, and uncorrected — treat as hypothesis-generating. But the Red-zone effect is directionally large (5pp gap), consistent across cohort stratifications, and crosses conventional significance.

## Why might "Red" survive better?

Speculative — we ran the test, not the causal study. But three plausible stories:

1. **Revealed-preference beats stated-preference.** Workers polled say "I don't want this automated." When it gets automated and they use it, they keep using it. The Red zone may be exactly where automation has the biggest *unmeasured* welfare gain.
2. **Friction signals opportunity.** Workers resist automation of tasks they perceive as core to their identity or expertise. That resistance *is* the moat — if the automation works, there's pricing power. Green zone tasks (workers already want them automated) attract more competitors because there's social license.
3. **Selection effect.** Red-zone startups get less attention, so surviving ones may be better-filtered for founder quality. The lower shutdown rate reflects survivor bias in who attempts Red-zone work.

We can't distinguish these with the current data. They're all compatible with the observation.

## Description drift (pivoting) by zone

All four zones hover at 0.39–0.42 mean cosine drift. The framework does not predict whether a company will drift from its YC-era thesis. Zone and drift are uncorrelated (r ≈ 0.02, n=812).

## Exemplars (factual-only)

Named examples below are illustrative of the zone × outcome cells; inclusion is not a judgment on the company. See `docs/named_examples.md` for the full list and why each was selected.

_See repo `docs/named_examples.md` for the 5-per-zone list of currently-live and inactive exemplars, selected by the pipeline on factual criteria only._

## Limitations

Detailed in `docs/analysis_limitations.md`. In brief:

- **Outcomes are weak.** Site-live + description-drift is a proxy for startup health. The prereg's 2-evidence rule for "shuttered" was relaxed to 1 source (site not reachable) because LinkedIn headcount and funding data couldn't be collected at scale. False-negatives (zombie companies with live sites but dead operations) are likely. Effect sizes could be larger or smaller with better outcome data.
- **N per zone at 200–440 is adequate for medium effects** (MDE ~13pp at 80% power, binary). Smaller real effects (<5pp) would be missed.
- **LLM-based task extraction introduces rater variance.** All extractions + embeddings are published CSV for replication; single-rater methodology is a choice (documented in prereg) rather than a hidden limit.
- **Cohort seasoning ranges 7.7–27.7 months.** Cohort fixed effects included; early cohorts contribute mostly to non-mortality outcomes.
- **Stanford's framework is worker-perspective. Startup outcomes are market-perspective.** A zone mismatch could indicate misreading users, but also could indicate successfully overriding user preference (which is common in software).

## What's citable

- **Null on primary:** Stanford's 4-zone framework does not predict YC startup outcomes in the preregistered primary tests (H1′, H2, H4, H5).
- **Directional signal on survival:** the log-rank across zones is significant (p=0.031), but the zone ordering contradicts the framework's core "Red = bad" claim. Red actually shows the highest survival. Low-Priority shows the predicted lowest.
- **Methodological:** LLM-based zone scoring on product pitches is biased compared to worker-grounded k-NN. Matters for anyone replicating this kind of work.

Cite as:
> Meyer, S. (2026). *A preregistered test of Stanford's WORKBank 4-zone framework on YC startup outcomes (W24–F25, N=1,223).* GitHub: [link]. 2026-04-24.

## Acknowledgements

Stanford SALT Lab for making WORKBank fully public. yc-oss for the YC directory static API.

---

*All data, code, prereg hash, hypothesis results, and figures are in the repo. Reproduce end-to-end with `make reproduce` (see README).*
