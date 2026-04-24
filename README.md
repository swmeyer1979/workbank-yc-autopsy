# YC × WORKBank Postmortem 2026

> A preregistered empirical test of Stanford SALT Lab's WORKBank 4-zone framework against YC startup outcomes. N=1,223 companies, batches W24–F25. [Findings post →](findings.md)

## One-paragraph summary

Stanford's [WORKBank](https://github.com/SALT-NLP/workbank) paper and its [Oct 2025 followup](https://futureofwork.saltlab.stanford.edu) reported that ~41% of YC AI-company tasks fall in "Red" (high capability × low worker desire) or "Low-Priority" (low × low) zones — the "don't-build-there" zones. Nobody tested whether those startups actually underperform. **Preregistered primary hypotheses are null.** But the zones move in *opposite* directions: **Red-zone YC companies shut down at 3.9% vs 9.0% elsewhere** (Fisher p=0.016) — the reverse of prediction. Low-Priority underperforms (11.0% vs 7.4%, p=0.072). Stanford's Red+Low bundle averages two opposite effects into a null (7.8% vs 8.4%, p=0.83).

## Files

| Path | What |
|---|---|
| [findings.md](findings.md) | Main findings post |
| [docs/preregistration.md](docs/preregistration.md) | Preregistration (commit `b996bfd` + amendment `55ba8d2`) |
| [docs/power_analysis.md](docs/power_analysis.md) | Power analysis, pre-data-pull |
| [docs/h_results_knn.md](docs/h_results_knn.md) | H1′–H5 results (k-NN primary) |
| [docs/h_results_llm.md](docs/h_results_llm.md) | H1′–H5 results (LLM-inferred secondary) |
| [docs/h_results_nonai.md](docs/h_results_nonai.md) | Non-AI placebo subgroup |
| [docs/analysis_limitations.md](docs/analysis_limitations.md) | Limitations, honestly surfaced |
| [docs/named_examples.md](docs/named_examples.md) | Per-zone example companies (factual only) |
| [data/processed/analysis.csv](data/processed/analysis.csv) | Joined analysis table, 1,224 rows × 24 cols |
| [data/processed/company_zone_scores_knn.csv](data/processed/company_zone_scores_knn.csv) | Primary zone scores |
| [data/processed/company_zone_scores.csv](data/processed/company_zone_scores.csv) | LLM-inferred zone scores (secondary) |
| [data/processed/task_extractions.csv](data/processed/task_extractions.csv) | Per-company task extractions |
| [data/processed/outcomes.csv](data/processed/outcomes.csv) | Site-live + drift + content-length outcomes |
| [figures/](figures/) | All figures (300dpi PNGs) |
| [notebooks/analysis.py](notebooks/analysis.py) | Analysis notebook (jupytext-style) |
| [scripts/](scripts/) | Reproducible pipeline: 01 extract → 02 match → 02b kNN → 03 score → 04 outcomes → 05 analyze |
| [dashboard/](dashboard/) | Next.js static dashboard (Vercel-deployable) |
| [marketing/](marketing/) | Substack, LinkedIn, Twitter drafts |

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Pull raw data (YC directory + WORKBank CSVs)
bash scripts/pull_raw.sh

# Pipeline (scripts are idempotent — rerun-safe)
.venv/bin/python scripts/01_extract_tasks.py         # Sonnet 4.6 via claude CLI (~$6)
.venv/bin/python scripts/02_match_to_workbank.py     # embedding match + LLM inferred fallback
.venv/bin/python scripts/02b_knn_zone_scoring.py     # k-NN primary zone scoring
.venv/bin/python scripts/03_company_zone_scores.py   # aggregate to company level (LLM variant)
.venv/bin/python scripts/04_outcome_pulls.py         # ~2.5min, HTTP fetches
.venv/bin/python scripts/05_build_analysis_frame.py  # join
.venv/bin/python notebooks/analysis.py               # hypothesis tests + figures
.venv/bin/python scripts/06_prune_data_for_dashboard.py  # dashboard JSON

cd dashboard && npm install && npm run build         # static export to dashboard/out/
```

Total runtime: ~10 min. Total spend: ~$6 (Sonnet 4.6 via Claude Code CLI).

## Methodology in brief

1. **Sample**: all 1,224 YC companies W24–F25 from [yc-oss/api](https://github.com/yc-oss/api). AI coded by description text (73%).
2. **Task extraction**: Sonnet 4.6 extracts 3–7 primary product-tasks per company, batch of 50 per LLM call.
3. **Zone assignment (primary, k-NN)**: each task embedded with `all-MiniLM-L6-v2`, matched to top-5 nearest in WORKBank. Zone coords = cosine-weighted mean of neighbors' worker-rated desire + expert-rated capability. Median split.
4. **Zone alignment score**: importance-weighted fraction of a company's tasks in high-desire zones (Green + Yellow). Continuous primary predictor.
5. **Outcomes**: site-live, description drift (cosine against current site), content length, careers-page presence. Funding and LinkedIn headcount not available at scale; H1 dropped before outcome collection.
6. **Analysis**: 5 preregistered hypotheses, Holm correction, one-sided tests. k-NN primary, LLM-inferred robustness, non-AI subgroup as placebo.

Full methodology + amendments in [docs/preregistration.md](docs/preregistration.md).

## Headline finding

**Prereg-committed headline (fires):** *Stanford framework does not predict YC startup outcomes in cohorts tested.*

**Exploratory zone-level finding (reported but not claimed as primary):** *The framework's Red zone shows the highest survival rate, directly contradicting the "Red = misaligned" framing. Low-Priority behaves as predicted. Bundling the two hides the signal.*

## Citation

```
Meyer, S. (2026). A preregistered test of Stanford's WORKBank 4-zone framework
on YC startup outcomes (W24–F25, N=1,223). GitHub: [link]. 2026-04-24.
```

## Acknowledgements

Stanford SALT Lab for publishing WORKBank fully ([SALT-NLP/workbank](https://github.com/SALT-NLP/workbank)). yc-oss for the YC directory static API. All Sonnet 4.6 calls routed through the Claude Code CLI (subscription-backed, no API key).

## License

MIT for code. Data derived from:
- YC directory via yc-oss — public.
- Stanford WORKBank — CC-BY-4.0.
- All derived data in this repo is CC-BY-4.0.
