# Substack draft

**Title:** Stanford Said 41% of YC AI Startups Build What Workers Don't Want. I Tested Whether Those Startups Fail More. They Don't — Some Outperform.

**Subtitle:** A preregistered test of Stanford's WORKBank framework against 1,223 YC companies finds the predicted effect is null overall — and reversed for the "Red Zone."

---

## The claim

In July 2025, Stanford's SALT Lab published WORKBank — a dataset mapping 844 occupational tasks onto a 4-zone grid of *worker-desire* (how much workers want this task automated, 1–5 scale from 1,500 U.S. workers) and *AI-capability* (how capable AI is at the task, scored by experts). The four zones:

|  | High worker desire | Low worker desire |
|---|---|---|
| **High AI capability** | 🟢 Green: build here | 🔴 Red: automation workers don't want |
| **Low AI capability** | 🟡 Yellow: R&D frontier | ⚫ Low-Priority |

In October 2025 they followed up with a paper on AI agents doing human work. The headline that [Forbes covered](https://www.forbes.com/...): **41% of tasks being built by YC AI startups fall in Red or Low-Priority zones.** The rhetorical move: these are the "bad zones" — building where workers don't want or AI isn't ready.

The implicit prediction, never tested: startups in those zones should fail more often.

## What I did

Preregistered a test. Hash-committed the methodology before pulling any outcome data. All 1,224 YC companies from batches Winter 2024 through Fall 2025. Seasoning range 7.7 to 27.7 months as of April 2026.

The pipeline:

1. **Sample frame** — all 1,224 YC companies, not just AI-tagged (AI dummy included as covariate).
2. **Task extraction** — Sonnet 4.6 extracted 3–7 primary product-tasks per company from its YC description.
3. **Zone assignment** — embedded each extracted task + all 844 WORKBank tasks, found top-5 nearest neighbors in WORKBank, computed zone coordinates from cosine-weighted mean of neighbors' *worker-rated* desire + *expert-rated* capability. (An earlier LLM-scored approach was biased — Sonnet rated pitches optimistically — so I amended the prereg to use k-NN before touching outcomes.)
4. **Validation** — the task-level zone distribution from my pipeline: 37.6% Red+Low. Stanford reported 41%. Rubric reproduces the claim.
5. **Outcomes** — automated collection of site-live status, description drift (YC description vs current site hero/meta), content length, careers-page presence. No LinkedIn or Crunchbase data (no free API at scale), so I dropped the original "log funding ~ zone" hypothesis and replaced it with "site_live ~ zone" before looking at outcomes.
6. **Analysis** — five preregistered hypotheses, Holm-corrected, one-sided tests.

## What I found

**The preregistered primary tests are null.**

- H1' (site-live ~ zone_alignment): p=0.34 after correction
- H2 (drift ~ alignment): p=0.85, and the point estimate has the *wrong sign*
- H4 (shuttered ~ alignment): p=0.42
- H5 (content length ~ alignment): p=0.68

Stanford's framework does not predict whether a YC company's site stays up, drifts in mission, or builds out product surface area.

**But the categorical survival test is significant (p=0.031, log-rank across 4 zones) — and the direction contradicts the framework's main rhetorical claim.**

Shutdown rates by zone (pooled across all cohorts):

- 🔴 Red: **3.9%** (n=204, 95% CI 2.0%–7.6%)
- 🟢 Green: 6.8% (n=443, 4.8%–9.5%)
- 🟡 Yellow: 10.6% (n=321, 7.7%–14.4%)
- ⚫ Low-Priority: 11.0% (n=255, 7.7%–15.5%)

Fisher's exact, Red vs rest: **p=0.016.** Red — the "avoid this" zone — has the *lowest* shutdown rate.

Low-Priority vs rest: p=0.072. Directionally matches prediction, marginally significant.

Red + Low-Priority vs Green + Yellow: **p=0.83.** When Stanford's paper bundled these into "41% of the misaligned startups," they combined two effects running in opposite directions. The bundled statistic loses the signal.

## What this means

First the honest caveats:

- This is an exploratory pairwise contrast, not a primary preregistered test. The prereg's primary tests are null.
- Red zone N=204. Effect size is 5 percentage points. Real but modest.
- Outcomes are weak. Site-live as a mortality proxy misses zombie companies (live site, dead operations). Better data — LinkedIn headcount, funding rounds — would either strengthen or reverse this.
- Single-rater pipeline with full publication of extractions. Rater consistency not externally validated.

Given those caveats, three interpretations are live:

**(1) Revealed preference beats stated preference.** Workers polled by WORKBank said they don't want certain tasks automated. When a startup ships the automation and workers actually use it, they may prefer it. Stated preference on surveys is known to diverge from behavior — and Red zone tasks are where the divergence would be largest. If workers use automation they said they didn't want, the startup wins.

**(2) Resistance is moat.** High-capability, low-desire tasks are exactly the ones where workers push back. That resistance is also a signal of reduced competition: fewer founders want to build what users explicitly reject. Surviving in Red zone means pricing power. Green zone is crowded because everyone agrees it should exist — commoditization is fast.

**(3) Selection.** YC-level filtering plus the harder recruitment problem in Red zone may cause those startups to attract better founders. The 3.9% shutdown rate isn't a zone effect — it's a founder-quality effect correlated with zone choice.

Any of the three could explain what I see. None is ruled out. This is hypothesis-generating, not causal.

## Why the Red+Low bundling matters

Stanford's paper doesn't *claim* Red-zone startups fail more. It says 41% are in zones where workers don't want or AI isn't ready. The failure claim is implicit — in media coverage, in VC commentary, in the framing of "41%."

But the rhetorical bundling matters because it transports Stanford's expert-rater framework into a **prescriptive** domain (where should startups build?) without testing whether the two pooled zones behave the same way. They don't. One predicts worse outcomes (Low-Priority). The other predicts better (Red, conditional on data).

**The framework has value as description.** It differentiates zones at p=0.031 across four strata. It just points a different direction than the paper's rhetoric suggests.

## What should happen next

- Run the same test with LinkedIn headcount, funding rounds, and founder status. 10x more statistical power. The directional result either hardens into a real finding or flips.
- Replicate on a non-YC sample. YC selection filters startups before they enter this test; the Red-zone survival advantage could be YC-specific.
- Instrument for founder selection — separate "Red zone attracts better founders" from "Red zone tasks have lower competitive pressure."
- Stanford's team should re-run their own 41% analysis disaggregating Red vs Low-Priority. Their paper is better without that bundling.

## The prereg, the code, the data

Everything is public. Repo: [github link]. Preregistration commit hash: `b996bfd` (with one amendment at `55ba8d2` before outcome pulls, switching zone-scoring to k-NN when I caught LLM bias).

The CSV with per-company zone scores, outcomes, and exemplars is published. Reproduce end-to-end with a single command.

If you're a Stanford SALT researcher reading this: the framework holds up as a lens. The zone-level disaggregation shows where your framing overreaches. I'd love to see a v2 of the paper that tests the zone-level predictions directly.

If you're a VC: the takeaway isn't "build in Red zone." It's "Stanford's map doesn't tell you where to build. Use your own judgment about worker resistance as a moat, not as a warning."

## Citation

> Meyer, S. (2026). *A preregistered test of Stanford's WORKBank 4-zone framework on YC startup outcomes (W24–F25, N=1,223).* GitHub: [link]. 2026-04-24.

Stanford paper: https://futureofwork.saltlab.stanford.edu

---

*Thanks to the SALT Lab team for publishing WORKBank with worker-level granularity — the entire study is possible because of that choice.*
