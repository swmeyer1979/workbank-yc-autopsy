# Tweet thread

---

1/ Stanford SALT Lab said 41% of YC AI startups build software workers don't actually want automated. The "Red Zone."

Nobody tested whether those startups fail more.

I ran that test on 1,223 YC companies (W24-F25). Preregistered.

Result: the opposite of what you'd expect 🧵

---

2/ Method: extracted 3-7 primary tasks per company via Sonnet 4.6. k-NN matched to Stanford's 844-task WORKBank corpus. Zone assigned from worker-grounded desire + expert capability scores.

Task-level rubric reproduces Stanford's 41% Red+Low claim almost exactly (37.6%). Sanity-checked.

---

3/ Shutdown rates by zone (site-live + 2-evidence proxy):

🔴 Red: 3.9% shut down (n=204)
🟢 Green: 6.8% (n=443)
🟡 Yellow: 10.6% (n=321)
⚫ Low-Priority: 11.0% (n=255)

Red — the "avoid this zone" zone — has the LOWEST shutdown rate.

Fisher p=0.016 for Red vs rest.

---

4/ Stanford's rhetorical move: bundle Red + Low-Priority as "41% misaligned."

But those two zones are moving in OPPOSITE directions. Red outperforms. Low-Priority underperforms.

Pool them: null (7.8% vs 8.4% for Green+Yellow, p=0.83).

The headline stat washes out.

---

5/ Preregistered primary hypotheses (continuous: site_live, description_drift, log-content-length) all NULL after Holm correction.

The categorical survival test is significant (log-rank p=0.031) — but the zone ORDERING is reversed from prediction for Red.

---

6/ Why might Red zone survive better? Three stories, can't distinguish with this data:

- Revealed preference beats stated preference
- Worker resistance = moat (pricing power when it works)
- Selection: Red ideas filter for better founders

Needs follow-up. This is hypothesis-generating.

---

7/ Limitations are real and front-loaded in the post:

- Outcomes are weak (no LinkedIn/Crunchbase at scale)
- Small N per zone
- Single-rater (but full data published for replication)
- Stanford's framework is worker-perspective, startup outcomes are market-perspective

---

8/ What's citable:

1. Null on prereg primaries — framework doesn't predict YC outcomes
2. Red/Low direction reversal — lumping them loses the signal
3. LLM scoring of startup pitches is biased vs worker-grounded methods

Full post, data, code, prereg: [github link]

Stanford paper: https://futureofwork.saltlab.stanford.edu
