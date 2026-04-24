# Power Analysis

Run: 2026-04-24. Sample frame N=1,224 YC companies W24–F25.

## Assumptions

- AI-coded subset: ~890 companies (73%)
- Zone split (from WORKBank task-level distribution applied as prior): Green 33%, Yellow 23%, Red 19%, Low-Priority 25%
- Mature cohort (W24+S24+F24, seasoning ≥20mo): 593 companies
- Base mortality rate (shuttered+dormant) at 18mo for YC cohorts historically: 20–30% per [YC Top 100 retention studies](https://www.ycombinator.com/topcompanies)

## Binary mortality — AI subset only, mature cohort

N per zone in mature AI subset (~430): Green 143, Yellow 100, Red 80, Low 107. Red+Low pooled = 187.

Test: `P(shuttered | Red+Low) > P(shuttered | Green+Yellow)`

| Base rate | Effect Δ | Power |
|---|---|---|
| 20% | 5pp | 0.19 |
| 20% | 10pp | 0.58 |
| 20% | 15pp | 0.88 |

**MDE at 80%:** ~12.5pp gap. Plausible if framework has real effect, but not if effect is small.

## Continuous — log(post-YC funding)

N per arm in mature AI subset: Green+Yellow ≈243, Red+Low ≈187.

| Cohen's d | Power |
|---|---|
| 0.2 | 0.53 |
| 0.3 | 0.85 |
| 0.5 | 0.99 |

**Well-powered** for d≥0.3.

## Continuous — description-drift cosine

Same N structure. Continuous dependent, continuous independent (zone_alignment_score 0–1). Linear regression r=0.15 detectable at 80% power with N=430. r=0.10 → 55% power. Sufficient for medium effects.

## Kaplan-Meier log-rank, 4 zones, AI subset mature

With N per zone 80–143, log-rank detects hazard ratios ≥1.7 at 80% power. Ratio ≈1.3 underpowered.

## Control arm (non-AI YC)

330 non-AI companies across all cohorts. Acts as placebo: framework shouldn't predict non-AI startup outcomes. If effect appears in control too → framework captures general zone-independent market signal, not AI-specific misalignment.

## Summary

- **Continuous primaries (H1, H2): well-powered** for plausible effects (d≥0.3, r≥0.15).
- **Binary secondary (H4): underpowered for small effects** (<10pp gap), fine for medium.
- **Survival (H3): underpowered** unless zone hazard ratio ≥1.7; treat as descriptive.
- **AI-vs-non-AI subgroup: directional only**, N too small for strong tests.

Null results on H4/H3 will be explicitly framed as "could not rule out null of <13pp effect," not "no effect."
