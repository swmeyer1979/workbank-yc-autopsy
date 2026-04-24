# LinkedIn post

**Stanford's 4-zone AI framework does not predict YC startup survival. The "41% misaligned" stat doesn't translate into failure.**

A year ago Stanford SALT Lab published WORKBank — a grid mapping tasks onto worker-desire × AI-capability. The headline picked up by Forbes: 41% of YC AI-company tasks are in the "Red" (workers don't want) or "Low-Priority" zones.

The implication — that startups in those zones underperform — was never tested.

I ran the test. 1,223 YC companies, batches W24–F25. Preregistered methodology. 2-of-3 source verification for the shutdown label (browser fetch + YC status + Wayback Machine). Full code + data published.

**Preregistered primary hypotheses: all null.** Zone alignment doesn't predict site-live, description drift, or product-surface-area proxies.

Zone-level shutdown rates (2-source verified):

🟢 Green: 1.6% (n=371 labeled)
🟡 Yellow: 2.2% (n=268)
🔴 Red: 1.2% (n=171)
⚫ Low-Priority: 3.5% (n=199)

Red is numerically lowest, Low-Priority numerically highest — but no contrast is statistically significant. 193 companies (15.8% of sample) had disagreeing sources and were excluded from confident labeling.

**What the null tells us:**

Stanford's framework captures worker preferences honestly. It does not, on current evidence, translate into a market-prediction instrument at the 7–27 month cohort age. The "41% misaligned" framing in media coverage makes a prediction the data does not support at this stage.

**Two methodological findings worth sharing with anyone doing this kind of work:**

1. **LLM scoring of startup pitches is biased.** Sonnet 4.6 rated desire a full point higher than workers do (median 4.0 vs 3.0) — it scores marketing copy optimistically. Ground the rubric in the underlying survey data via k-NN, not in LLM judgment on commercial text.

2. **Single-source shutdown labels are ~9× worse than 2-source.** An earlier draft of my findings used single-source HTTP fetch for the shuttered label. Under 2-of-3 verification, 71% of those labels were ambiguous and 19% were confirmed live. The original "Red zone outperforms" headline I almost published was a labeling artifact. Retraction is documented in the repo — keeping it visible because it's the most replicable lesson here.

**What would change the result:**
- 3–5 year horizon (W24 cohort will be 4 years old in 2028)
- Continuous outcomes (funding rounds, LinkedIn headcount) for more statistical power
- Non-YC sample to remove founder-quality compression

Citable result: *Stanford's 4-zone framework does not predict YC startup outcomes at cohort ages 7.7–27.7 months (N=1,223; preregistered tests null after Holm correction).*

Repo + preregistration hashes + retraction record: [github link]
Stanford paper: https://futureofwork.saltlab.stanford.edu

Credit to the SALT Lab team for publishing WORKBank at worker-level granularity — the entire project is possible because of that choice.
