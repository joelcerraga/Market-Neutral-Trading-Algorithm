# Milestone 4: topology descriptors and simpler controls

The frozen protocol evaluates four features at 63, 126 and 252 sessions on 2,516 identical decision dates. The primary window remains 126 sessions. No trading overlay was introduced.

## Primary-window correlations with mean correlation

| Feature | Development Spearman | Validation Spearman |
| --- | ---: | ---: |
| H0 mean merger distance | -0.935 | -0.968 |
| H0 final merger distance | -0.879 | -0.890 |
| H1 total persistence | -0.593 | -0.667 |
| H1 maximum persistence | -0.463 | -0.421 |

## Approximation using the three simpler controls

Ordinary least squares uses an intercept, mean correlation, mean stock volatility and SPY volatility. All centring, scaling and coefficients use development only. R² scores the topology feature, not a trading return.

| Feature | Development R² | Validation R² |
| --- | ---: | ---: |
| H0 mean merger distance | 0.959 | 0.563 |
| H0 final merger distance | 0.810 | -0.195 |
| H1 total persistence | 0.345 | 0.343 |
| H1 maximum persistence | 0.223 | 0.303 |

A negative validation R² means that the transferred development model has larger squared error than a constant equal to the validation feature mean. That mean is used only as a scoring benchmark. Unexplained variation is not evidence of predictive or economic value.

All window comparisons, fit coefficients, row-level residuals and numerical stability checks are retained in the companion CSV/JSON files. Overlapping windows make these observations dependent; no independent-observation significance claims are made.
