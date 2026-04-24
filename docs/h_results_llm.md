# Hypothesis Results — LLM-Inferred Secondary

_Robustness check using LLM-inferred zone scores. Holm correction across H1'–H5._

**Note:** LLM variant suffers from optimism bias (83% Green collapse). Treat results as robustness only; kNN primary is authoritative.

| Hyp | N | Coef | 95% CI | p (one-sided raw) | p (Holm) | Verdict |
|-----|---|------|--------|-------------------|----------|---------|
| H1' | 1036 | +0.6611 | [-0.4123, +1.7345] | 0.1137 | 0.2274 | NULL |
| H2 | 812 | -0.1086 | [-0.2061, -0.0110] | 0.0146 | 0.0730 | NULL |
| H3 | 1223 | log-rank | N/A | 0.0623 | 0.1869 | NULL |
| H4 | 1223 | -0.4951 | [-1.4997, +0.5096] | 0.1671 | 0.2274 | NULL |
| H5 | 936 | +0.9627 | [+0.0155, +1.9099] | 0.0232 | 0.0927 | NULL |
