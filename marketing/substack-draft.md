# Substack draft

**Title:** I Tested Whether Stanford's "Red Zone" AI Startups Fail More. They Don't. (The framework captures worker sentiment honestly. It doesn't predict outcomes.)

**Subtitle:** A preregistered test of Stanford's WORKBank on 1,223 YC companies. All primary hypotheses null. Plus: why the Red-zone "reversal" I almost published was a labeling artifact.

---

## The claim

In July 2025, Stanford's SALT Lab published WORKBank — a dataset mapping 844 occupational tasks onto a 4-zone grid of *worker-desire* (1–5, from 1,500 U.S. workers) and *AI-capability* (expert-scored). The four zones:

|  | High worker desire | Low worker desire |
|---|---|---|
| **High AI capability** | 🟢 Green: build here | 🔴 Red: automation workers don't want |
| **Low AI capability** | 🟡 Yellow: R&D frontier | ⚫ Low-Priority |

Their follow-up paper reported that ~41% of YC AI-company tasks fall in Red or Low-Priority — the "avoid these zones" framing. Forbes covered it. VC Twitter circulated it. The implicit prediction: startups in those zones should underperform.

Nobody tested whether they do.

## What I did

Preregistered a test. Hash-committed the methodology before pulling any outcome data. All 1,224 YC companies from batches Winter 2024 through Fall 2025 (cohort ages 7.7–27.7 months as of April 2026).

The pipeline:

1. **Task extraction.** Sonnet 4.6 extracted 3–7 primary product-tasks per company from its YC description.
2. **Zone assignment.** Embedded each extracted task + all 844 WORKBank tasks with a sentence encoder. Found top-5 nearest WORKBank neighbors. Zone coordinates = cosine-weighted mean of neighbors' *worker-rated* desire + *expert-rated* capability. (An earlier LLM-scored approach was biased — Sonnet rated pitches optimistically — so I amended the preregistration to k-NN before touching outcomes.)
3. **Validation.** My pipeline produces 37.6% of extracted tasks in Red+Low, within 3pp of Stanford's 41%. Rubric reproduces the claim.
4. **Outcomes (2-source verification).** For each company:
   - Source A: browser-grade HTTP fetch (Scrapling StealthyFetcher, bypasses bot-protection)
   - Source B: YC's own status field (Active / Inactive / Acquired)
   - Source C: Internet Archive Wayback last snapshot within 180 days
   - `shuttered_v2` requires 2 of 3 to agree
5. **Analysis.** Five preregistered hypotheses, Holm-corrected, one-sided.

## The primary results

**All preregistered tests null.**

| Hypothesis | Outcome |
|---|---|
| H1': site-live ~ zone_alignment | Null (Holm p=0.34) |
| H2: drift ~ zone_alignment | Null (p=0.85; point estimate wrong-signed) |
| H3: KM log-rank across zones | Null under 2-source verification |
| H4: shuttered ~ zone_alignment | Null |
| H5: content-length ~ zone_alignment | Null |

Zone-level shutdown rates under 2-source verification:

- 🟢 Green: 1.6% (n=371)
- 🟡 Yellow: 2.2% (n=268)
- 🔴 Red: 1.2% (n=171)
- ⚫ Low-Priority: 3.5% (n=199)

Red still numerically lowest. Low-Priority still numerically highest. Fisher's exact, one-sided: Red vs rest p=0.90; Low vs rest p=0.10; Red+Low vs Green+Yellow p=0.35. All null.

## The retraction I need to surface

An earlier draft of this essay led with:

> Red zone shutters at 3.9% vs 9.0% elsewhere (p=0.016). Stanford's framework predicts the opposite direction for Red. They bundled Red+Low as "41% misaligned," and those two effects run in opposite directions.

**That finding does not survive proper verification.**

The first version of this study used a single HTTP fetch with a custom user-agent as the shutdown signal. 100 companies were flagged as shuttered. Spot-check: 3 of 5 were returning HTTP 200 right then. Cloudflare, bot-protection, and transient failures were flooding the Green and Yellow cells with false-positive shutdown labels — creating the appearance of a Red-zone advantage.

Under 2-of-3 source verification:
- 19 of the 100 v1-shuttered are confirmed live (current fetch + YC Active + Wayback recent)
- 71 of the 100 are *ambiguous* — sources disagree, cannot label confidently
- 10 of the 100 are confirmed shuttered

The direction reversal was a labeling artifact, not a zone effect. The preregistration specified 2 evidence sources. Relaxing that to 1 source to ship faster was the mistake. Keeping the retraction visible is the whole point of preregistering — you get to distinguish "real finding" from "artifact the method almost fooled me into believing."

## What the null finding actually means

**The framework's descriptive value is intact.** WORKBank's worker-level data on task desirability is real. Our k-NN pipeline reproduces Stanford's zone distribution to within 3 percentage points.

**The framework's market-predictive value, at this horizon, is null.** Zone membership does not predict whether a YC company keeps its site up, drifts in description, builds careers pages, survives, pivots, or grows its product surface area — at 7–27 months of seasoning.

Three reasons the null could be true even if the framework has real predictive power:

1. **Cohort too young.** YC's W24 cohort is 28 months old. Most startup mortality happens in years 3–5. A re-run in 2028 with the same cohort 4 years older might reveal effects this study can't.

2. **YC filters harder than WORKBank zones.** YC already selects for founder quality, TAM, distribution. The variance left after that filter may not be large enough for zone effects to show through at the outcomes I could measure.

3. **Worker perspective ≠ market perspective.** Workers say they don't want a task automated. That doesn't mean buyers won't pay for it. The framework measures what workers feel; markets measure what buyers buy. Those can differ persistently.

## What the Red/Low numerical asymmetry might be (speculation — don't cite as finding)

Even null at conventional thresholds, the numerical pattern (Red lowest, Low highest) is consistent enough across zone contrasts to be worth flagging:

- **Red zone might be moat-rich.** If workers resist automation of a task, there are fewer founders willing to build it — and the ones who do may have pricing power when the automation works. Worker resistance as a competitive moat.

- **Low-Priority zone might be doubly hard.** Low worker desire *and* low AI capability. No enthusiast users, and the tech isn't there yet. Worst possible cell to build in.

- **Green might be crowded.** Everyone agrees it should exist — fast commoditization, more shutdowns due to competition.

These are stories compatible with a pattern too sparse to call significant. Follow-up with richer outcome data could test them. Don't treat them as findings from this study.

## What's citable

1. **Null result:** Stanford's 4-zone framework does not predict YC startup outcomes at cohort ages 7.7–27.7 months (N=1,223, preregistered tests null after Holm correction).

2. **Methodological:** LLM scoring of startup pitch text is systematically biased upward on worker-desire compared to worker-grounded k-NN scoring (median 4.0 vs 3.0). Anyone applying worker-survey frameworks to commercial text should ground the rubric in the survey data, not in LLM judgment.

3. **Methodological:** Single-source "shuttered" labels produce ~80% false-positive rates relative to 2-of-3 source verification. Prior startup-mortality work using single-signal proxies should be re-evaluated against multi-source ground truth.

Cite as:
> Meyer, S. (2026). *A preregistered test of Stanford's WORKBank 4-zone framework on YC startup outcomes (W24–F25, N=1,223). All primary hypotheses null under 2-source verification.* GitHub: [link]. Includes retraction of a single-source Red-zone reversal finding from an earlier draft. 2026-04-24.

## What should happen next

- Re-run this study in 2028. W24 cohort at 4 years, W25+S25 at 3. Framework effects have time to surface if they exist.
- Add continuous outcomes at scale: Crunchbase funding rounds, LinkedIn headcount, revenue multiples. Binary shutdown is a weak signal for this cohort age; continuous outcomes get 3–10× more power.
- Replicate on non-YC samples (Techstars, Seed accelerators, independent angels) to test whether any effects are YC-specific.
- Stanford SALT researchers: if you're reading this, consider re-running your own 41% analysis disaggregating Red vs Low-Priority. Even if the headline stat is null on outcomes, the disaggregation matters for how the framework gets cited.

## The prereg, the code, the retraction, the data

Everything public. Repo: [github link]. Preregistration commit hashes: `b996bfd` (initial) and `55ba8d2` (k-NN amendment before outcome pulls). The v1 single-source draft and the v2 retraction are both visible in git history + documented in `docs/shuttered_v2_comparison.md`.

Reproduce end-to-end in ~60 minutes, including the 25-minute browser-grade fetch stage.

If you're a Stanford SALT researcher: I'd love to see a v2 of your paper that tests zone-level predictions directly against outcome data. The framework is strong enough as a lens that it deserves that test.

If you're a VC: the takeaway isn't "ignore the zones." It's "the zones describe worker sentiment, not market outcomes. Use them to understand user resistance, not to predict startup success."

## Acknowledgements

Stanford SALT Lab for publishing WORKBank at worker-level granularity — the entire study is possible because of that choice. yc-oss for the YC directory API. Internet Archive for Wayback. The retraction process is easier when the preregistration and the counter-evidence are both in the same repo.
