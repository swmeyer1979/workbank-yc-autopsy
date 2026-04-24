# LinkedIn post

**Stanford's 4-zone AI framework doesn't predict YC startup survival. Also, the "red zone" has the *highest* survival rate — the opposite of what the framework predicts.**

Last year Stanford SALT Lab published WORKBank: a 4-zone grid of worker-desire × AI-capability. The headline finding picked up by Forbes: 41% of YC AI-company tasks fall in "Red" (high capability, low worker desire) or "Low-Priority" (low capability, low desire) zones. The implication: startups in those zones are building software workers don't actually want, and presumably will struggle.

Nobody tested whether those startups actually struggled.

I ran the test on 1,223 YC companies across 7 batches (W24–F25). Preregistered methodology. Full code + data published.

**Preregistered primary tests: null.** Zone alignment doesn't predict site-live, description drift, or content-length proxy outcomes.

**But disaggregate the zones and a different picture appears:**

🔴 Red: 3.9% shutdown rate (n=204)
🟢 Green: 6.8% (n=443)
🟡 Yellow: 10.6% (n=321)
⚫ Low-Priority: 11.0% (n=255)

Red — the "avoid this" zone — has the lowest shutdown rate across all four. Fisher's exact p=0.016. Low-Priority does underperform, consistent with prediction. But Stanford's rhetorical grouping of Red + Low as "41% misaligned" combines two effects running in opposite directions. They cancel in aggregate (7.8% vs 8.4% for Green+Yellow, p=0.83).

Possible stories for why Red survives better:

1. **Revealed preference beats stated preference.** Workers say they don't want it automated; use it anyway when offered.
2. **Friction is moat.** Worker resistance means less competition and more pricing power.
3. **Selection.** Red-zone ideas attract better founders because weaker founders self-select into "obvious" green-zone ideas.

Can't distinguish these with this data. Needs follow-up.

**Methodological note worth sharing:** I initially used LLM scoring (Sonnet 4.6) on startup pitch text to assign desire/capability ratings. The LLM systematically rated desire higher than real workers do (median 4.0 vs worker 3.0) — it scores pitches optimistically. Switched to a k-NN approach grounded in WORKBank's worker data before pulling outcomes. Anyone doing this kind of work should ground ratings in survey data, not LLM judgment on marketing copy.

**What I'd do next:**
- Same study with real outcome data (LinkedIn headcount, funding rounds) — would turn 5-10% shutdown signal into log-continuous revenue signal, 10x power
- Instrument for founder selection to separate the revealed-preference story from selection
- Compare YC → YC-rejected-but-funded to test whether this is a YC-specific pattern

Repo + preregistration + full results: [github link]
Stanford paper: https://futureofwork.saltlab.stanford.edu

Credit to the SALT Lab team for making WORKBank fully public — couldn't have run this without their task-level data being accessible.
