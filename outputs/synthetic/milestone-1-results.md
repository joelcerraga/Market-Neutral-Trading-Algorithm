# Market-Neutral Trading Algorithm

## Milestone 1: validation results

**Data: SYNTHETIC — NOT HISTORICAL MARKET DATA.**

This run checks the research implementation. It is not an out-of-sample market study. The synthetic generator deliberately includes mean reversion, so favourable results cannot establish an investment edge.

| Measure | Baseline reversal | Graph diffusion |
| --- | ---: | ---: |
| Simulated total return | 3.96% | 8.37% |
| Simulated Sharpe (zero cash rate) | 0.58 | 1.27 |
| Simulated maximum drawdown | -2.14% | -1.81% |
| Realised market beta | 0.0103 | 0.0082 |
| Mean daily traded notional / start NAV | 61.73% | 62.48% |
| Trading costs, capital units | 19,622.24 | 20,460.98 |
| Borrow costs, capital units | 2,222.04 | 2,293.48 |
| Largest absolute net dollar exposure | 3.52e-15 | 1.29e-15 |
| Largest absolute estimated beta exposure | 3.69e-15 | 1.46e-15 |
| Largest gross exposure | 100.00% | 100.00% |
| Largest single position | 8.00% | 8.00% |

## Interpretation

Neutrality holds against the lagged beta estimate at each rebalance. It does not imply zero future market covariance, sector exposure, intraday exposure or drawdown. Performance metrics exclude the common estimation warm-up and include entry and terminal liquidation costs.

Assumptions: 5 bps per dollar bought or sold; 2% annual borrow on short notional, ACT/365; 100% gross limit; 8% name limit. Cash interest and financing rebates are zero. Fee settings are examples, not broker quotes.

## Next research gate

Choose and document a historical data source, point-in-time universe, adjustment convention, calendar and liquidity rules. Freeze a chronological evaluation plan before inspecting results. Only then compare the two signals on market data and add persistent-homology regime features.
