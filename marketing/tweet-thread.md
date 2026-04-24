# Tweet thread

---

1/ Stanford SALT Lab said 41% of YC AI startups build what workers don't want automated. The "Red Zone."

Nobody tested whether those startups fail more.

I ran that test. 1,223 YC companies, W24-F25. Preregistered.

Result: null. 🧵

---

2/ Method: extracted 3-7 primary tasks per company via Sonnet 4.6. k-NN matched to Stanford's 844-task WORKBank corpus. Zone coords from worker-rated desire + expert capability.

Task-level rubric reproduces Stanford's 41% Red+Low claim (we get 37.6%). Rubric is faithful.

---

3/ Shutdown rates by zone (2-of-3 source verified: browser fetch + YC status + Wayback):

🟢 Green: 1.6%
🟡 Yellow: 2.2%
🔴 Red: 1.2%
⚫ Low-Priority: 3.5%

Red still numerically lowest. Low-Priority still numerically highest.

None of the contrasts are statistically significant.

---

4/ Preregistered continuous tests (site-live, drift, content-length, alignment-score logistics): all NULL after Holm correction.

Stanford's framework does not predict YC startup outcomes at this cohort age.

---

5/ Retraction worth surfacing: an earlier draft of this study reported "Red zone reversal, p=0.016" based on single-source shuttered labels.

Under proper 2-of-3 source verification, 71% of v1-shuttered were ambiguous and 19% were confirmed live.

The "reversal" was a labeling artifact.

---

6/ What the data actually shows:

- Framework's descriptive value: intact (worker preferences are real)
- Framework's market-predictive value at 7-27mo: null
- Stanford's "41% misaligned" framing doesn't translate to "those startups fail more" at this horizon

---

7/ Two methodological notes from this project worth citing:

1. LLM scoring of startup pitches is biased vs worker-grounded scoring (LLM median desire=4.0 vs worker=3.0). Ground the rubric in survey data.

2. Single-source "shuttered" labels inflate false positives ~9x. Require 2 independent streams.

---

8/ What would change this:

- 3-5 year horizon (W24 needs 2+ more years to show framework effects)
- Continuous outcomes (funding rounds, headcount) — not just binary shuttered
- Non-YC sample (removes YC founder-quality filter)

---

9/ Null finding is still citable:

Stanford's 4-zone framework is a useful lens for worker sentiment. It is not, on current evidence, a useful lens for picking startups.

Full post, data, code, preregistration + retraction record: [github link]

Stanford paper: https://futureofwork.saltlab.stanford.edu
