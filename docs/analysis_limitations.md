# Analysis Limitations

## Sample

YC-funded companies only (W24–F25, n=1,224). Not representative of the broader AI startup market. YC selects for high-quality teams and ideas; base rates (survival, pivot frequency) likely more favorable than the general early-stage population.

## Statistical power

N per zone ranges ~200–440. Sufficient for effects >= Cohen's d=0.3 (pre-specified power target, ~72%). Effects smaller than ~10pp in binary outcomes are underpowered. Null findings on H1', H2, H4, H5 should be read as "no detectable effect at current N" not "confirmed no effect."

## Shuttered proxy (1-source relaxation)

Pre-registration specified two independent evidence sources required to code shuttered=True (site_live=False AND linkedin_headcount=null). LinkedIn headcount was not collected. The operational definition used here is site_live=False AND fetch_skipped_reason is null — a single-source proxy. This understates shuttered rate (many parked/down domains are not truly defunct; many defunct companies leave sites up). Understating shuttered=True biases H3 and H4 toward null. 2-source verification recommended for publication.

Additionally, site_live=False accounts for only 100 companies (9.6% of fetchable sites). True mortality for these cohorts (7.7-27.7 months seasoning) is plausibly higher.

## H1 to H1' substitution

Original H1 tested funding as outcome. Funding data was not collected (no Crunchbase API key; press-coverage scraping out of scope). Replaced with site_live as the viability proxy. site_live is a weaker signal than funding (a live site != a live company; an acquired company may redirect). H1' should not be interpreted as a funding-predictor test.

## LLM zone scoring bias

LLM-inferred scores (secondary variant) exhibit systematic optimism bias: Sonnet 4.6 scores startup product-pitch tasks from the customer perspective ("people want this"), not the worker perspective required by the WORKBank rubric. This collapses 83% of companies to Green and destroys treatment variance. LLM variant results are included for robustness only; k-NN primary is authoritative.

## k-NN threshold sensitivity

k-NN grounding uses top-5 nearest WORKBank tasks by cosine distance. The cosine >= 0.70 threshold for "matched" classification was not hard-tuned via held-out validation — it was selected to reproduce Stanford's 41% Red+Low benchmark (k-NN yields 37.6%). Top-5 neighbors can span multiple zones for ambiguous tasks. k=3 or k=10 sensitivity check not run (flagged as exploratory if needed).

## Cohort seasoning heterogeneity

Cohorts range from 7.7 months (Fall 2025) to 27.7 months (Winter 2024) at observation date. Cohort fixed effects control for level differences but do not model the interaction between zone and seasoning. Younger cohorts may not have had time to shutter even if misaligned. H3 (survival) is most affected; Red's low shuttered rate (3.9%) may partly reflect recency of younger cohorts.

## Single rater; no inter-rater kappa

Task extraction is LLM-based (Sonnet 4.6, temperature=0). No second human or model rater. Reproducibility depends on model version (logged as claude-sonnet-4-6 at extraction time). All task-level extractions and zone assignments published as CSV for open replication.

## H3 ordering anomaly

Observed zone shuttered rates (Red=3.9%, Green=6.8%, Yellow=10.6%, Low-Priority=11.0%) do not match the predicted ordering Green > Yellow > Red > Low-Priority. Red's anomalously low shuttered rate may reflect cohort age confound or the single-source shuttered proxy masking true mortality. The log-rank test is significant (p=0.031 after Holm), but the ordering finding is exploratory, not confirmed.
