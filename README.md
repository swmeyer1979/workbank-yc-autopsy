# YC × WORKBank Postmortem 2026

Empirical test of Stanford SALT Lab's WORKBank framework against YC startup outcomes.

## Thesis

Stanford's [WORKBank](https://github.com/SALT-NLP/workbank) (Jul 2025) and followup ["How Do AI Agents Do Human Work?"](https://futureofwork.saltlab.stanford.edu) (Oct 2025) map tasks onto a 4-zone grid of worker-desire × AI-capability:

| | High desire | Low desire |
|---|---|---|
| **High capability** | 🟢 Green (build here) | 🔴 Red (automation workers don't want) |
| **Low capability** | 🟡 Yellow (R&D frontier) | ⚫ Low-Priority |

Their paper reports that ~41% of YC AI-company tasks fall in Red or Low-Priority zones — implying the market is building software workers actively don't want. **But they never tested whether those startups underperform.**

If the 4-zone framework is predictive, zone membership should correlate with startup survival, pivot rate, and funding trajectory. This repo runs that test.

## Cohorts

All YC batches W24–F25 (7 batches, **1,224 companies**), seasoning range **7.7–27.7 months** as of 2026-04-24.

| Batch | N | Months since start |
|---|---|---|
| Winter 2024 | 251 | 27.7 |
| Summer 2024 | 249 | 22.7 |
| Fall 2024 | 93 | 19.7 |
| Winter 2025 | 167 | 15.7 |
| Spring 2025 | 145 | 13.8 |
| Summer 2025 | 168 | 10.7 |
| Fall 2025 | 151 | 7.7 |

**894 (73%)** code as AI/ML-oriented by description text (YC static dump has no tag field).

## Status

- [x] Scaffolded repo + data pulls
- [x] Task-level zone rubric derived from WORKBank CSVs (844 tasks, median-split; reproduces 44% Red+Low vs Stanford's 41%)
- [x] [Preregistration](docs/preregistration.md)
- [ ] Task extraction per company (Sonnet 4.6)
- [ ] Zone alignment score per company
- [ ] Outcome pulls (site-live, LinkedIn headcount, funding, description drift)
- [ ] Analysis + findings
- [ ] Dashboard

## Citation

Stanford SALT Lab, "Future of Work with AI Agents" (2025). WORKBank dataset. https://futureofwork.saltlab.stanford.edu

## License

MIT. Data files derived from public YC directory + Stanford WORKBank (CC-BY-4.0 per HuggingFace).
