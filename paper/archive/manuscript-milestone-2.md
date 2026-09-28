Historical baseline, graph diffusion and a reproducible research protocol

**Joel Cerraga**

Quant Projects<br/>Milestone 2 working paper<br/>21 September 2026

Research question

Can relationships between stock returns improve a constrained reversal strategy after trading costs, borrowing costs and market exposure are accounted for?

This version establishes the historical baseline. Graph-strategy comparison, persistent homology and final holdout evaluation are subsequent milestones.

## Abstract

This project develops a Python framework for a market-neutral equity trading study. A baseline reversal signal is constructed from recent volatility-scaled returns, and portfolios are constrained to approximately zero dollar exposure and zero exposure to estimated market beta. A weighted correlation graph and Laplacian diffusion provide the proposed extension. The present milestone moves from synthetic verification to an exploratory historical study of 24 surviving US companies, with SPY as the benchmark.

The acquired dataset contains 2,768 aligned sessions from 2 January 2009 to 31 December 2019. The year 2009 supplies estimation history; 2010-2016 is the development period and 2017-2019 is validation. The final period, 2020-2025, has not been acquired or evaluated. At 5 basis points per dollar traded and 2% annual short borrow, the baseline produces annualised net returns of -3.10% in development and -5.83% in validation. The corresponding maximum drawdowns are -24.99% and -18.49%.

These findings establish a demanding baseline rather than evidence of profitable trading. Current-vintage adjusted data and a fixed survivor basket limit generalisation. The deliverables include an auditable price cache, a frozen local protocol, focused tests, an explanatory notebook, numbered equations, selected source-code excerpts and a standalone interactive 3D correlation explorer. The next milestone will test the graph signal under the same conditions.

**Keywords:** statistical arbitrage; market neutrality; graph Laplacian; diffusion; historical backtesting; reproducibility.

## Table of contents

## List of tables and figures

Tables

Figures

## List of equations and code listings

Equations

Code listings

## List of abbreviations

Table 1. Abbreviations used in the working paper

| Abbreviation | Meaning |
| --- | --- |
| ACT/365 | Actual calendar days divided by 365 |
| bps | Basis points; one basis point equals 0.01% |
| CAGR | Compound annual growth rate |
| CAPM | Capital Asset Pricing Model |
| CRSP | Center for Research in Security Prices |
| CSCV | Combinatorially symmetric cross-validation |
| CSV | Comma-separated values |
| ETF | Exchange-traded fund |
| H0 / H1 | Homology dimensions zero and one |
| NAV | Net asset value |
| OLS | Ordinary least squares |
| P&L | Profit and loss |
| PBO | Probability of backtest overfitting |
| PCA | Principal component analysis |
| SHA-256 | Secure Hash Algorithm, 256-bit digest |
| SPY | Ticker used for the S&P 500 ETF benchmark |
| TDA | Topological data analysis |
| USD | US dollars |

## List of mathematical symbols

Table 2. Mathematical symbols and definitions

| Symbol | Definition |
| --- | --- |
| i, j; t; n | Asset indices; session index; number of assets |
| P; r | Input adjusted price; simple holding-period return |
| h; σ̂ | Signal horizon; estimated daily return standard deviation |
| x; s | Volatility-scaled shock; unnormalised trading score |
| β; β̂ | Market sensitivity; its trailing estimate |
| A; A⁺ | Exposure matrix; Moore-Penrose pseudoinverse |
| q; w | Projected score; portfolio weights relative to post-cost NAV |
| G; b | Maximum gross exposure; maximum absolute name weight |
| ρ; W; D | Pairwise correlation; adjacency matrix; degree matrix |
| d̄; L; τ | Mean weighted degree; scaled Laplacian; diffusion time |
| x̃; d(i,j) | Diffused signal; correlation-derived distance |
| v; V; c | Signed asset notional; NAV; cost per dollar traded |
| a; Δ | Annual borrow rate; elapsed calendar days |
| B; C | Borrow cost; transaction cost |
| R; S; DD | Portfolio return; descriptive Sharpe statistic; drawdown |

## 1. Introduction and research context

As Avellaneda and Lee explain in *Statistical arbitrage in the US equities market* (2010), systematic equity strategies can use factor-adjusted residual behaviour to form market-neutral portfolios [1]. Their PCA- and ETF-based construction provides context for this research. The present baseline and graph residual are different models, and no result from their paper is transferred to this stock basket.

Lo and MacKinlay, in *When Are Contrarian Profits Due to Stock Market Overreaction?* (1990), show that contrarian profits need not arise solely from overreaction [2]. This distinction is relevant because reversing a recent stock movement is a trading hypothesis, not proof that its price is incorrect. Accordingly, the first historical experiment retains a simple baseline and evaluates its costs and exposures before adding graph complexity.

The project builds on the earlier SPX density study in its use of controlled numerical checks, reusable Python modules and explanatory notebooks. Its empirical objective is different: it evaluates a trading rule rather than recovering an option-implied probability density. The final research presentation will include a reproducible GitHub repository and an interactive companion page suitable for sharing through LinkedIn.

### 1.1. Questions and scope

Three questions guide the work. First, does the baseline remain viable after explicit costs? Second, does graph diffusion add information under an otherwise identical experiment? Third, can persistent-homology features add useful regime information beyond simpler measures such as volatility and mean correlation? Milestone 2 answers only the first question and establishes the protocol for the others.

The experimental code and the scientific references have separate roles. The references justify established concepts and numerical relationships; parameter settings, the fixed basket and the proposed graph score are choices made for this project. Their effectiveness remains subject to the subsequent comparison.

## 2. Historical data and experimental protocol

Table 3. Declared equity universe; research groups are not historical index classifications

| Research group | Stock tickers |
| --- | --- |
| Technology | AAPL, MSFT, IBM, ORCL |
| Financials | JPM, BAC, WFC, GS |
| Energy | XOM, CVX, COP, SLB |
| Healthcare | JNJ, PFE, MRK, UNH |
| Consumer retail | WMT, COST, TGT, HD |
| Consumer brands | KO, PEP, MCD, SBUX |

The primary observations are Yahoo Finance daily chart responses [15]. The analysis uses the supplied **adjclose** field; close, volume, dividend events and split events are retained for audit. The data are current-vintage vendor observations rather than a point-in-time archive. Historical adjustment accuracy has not been independently certified, and dividends are not added a second time to adjusted-price returns.

Table 4. Chronological allocation fixed before baseline performance was inspected

| Period | Dates | Use |
| --- | --- | --- |
| Warm-up | 2009 | Trailing estimates only |
| Development | 2010-2016 | Baseline construction and diagnostic evaluation |
| Validation | 2017-2019 | Declared chronological check; not a final test |
| Final holdout | 2020-2025 | Reserved; no bars acquired or strategy results inspected in this milestone |

As White explains in *A Reality Check for Data Snooping* (2000), repeated model selection on the same observations can create apparently favourable findings by chance [9]. Therefore, the universe, dates, cost scenarios and baseline settings were written to a local protocol and hashed before the equity study was run. This record is not external preregistration, and it does not eliminate knowledge of historical market events.

## 2.1. Data audit and sample limitations

Table 5. Data audit for 24 stocks and the SPY benchmark

| Audit item | Observed result |
| --- | --- |
| Sessions per series | 2768 |
| First / last session | 2 January 2009 / 31 December 2019 |
| Exact calendar agreement | All 25 series match SPY observations |
| Missing values | 0 |
| Nonpositive volume | 0 |
| Absolute adjusted returns above 40% | 0 |
| Longest unchanged-price run | 2 sessions |
| Dividend / split events | 1081 / 4 retained provider events |
| Final holdout | Absent from the permitted historical cache |

Shumway, in *The Delisting Bias in CRSP Data* (1997), documents the importance of omitted adverse delisting returns [5]. This project has a broader selection limitation: its named basket contains companies that survived to the selection date. It is consequently an exploratory fixed-basket study and cannot establish performance for the historical investable equity universe.

The loader does not silently forward-fill missing prices or intersect mismatched calendars. Positive prices and reported volumes are required throughout. A 20-session close-times-volume proxy is reported, but this is not a calibrated capacity limit. Borrow availability, suspended securities and a complete corporate-action reconstruction remain unresolved for a production equity simulator.

Equation 1. Simple adjusted-price return

$$r_{i,t}=\frac{P_{i,t}}{P_{i,t-1}}-1 \qquad (1)$$

Equation 1 defines the input return. Where: P is the supplied adjusted-price series, i denotes the asset and t denotes the observed session. Avellaneda and Lee also formulate their historical return analysis using dividend-adjusted prices [1]. Here the resulting return-bearing notionals are an approximation; the ledger does not model raw execution prices and dividend cash flows separately.

## 3. Baseline signal and market sensitivity

Table 6. Baseline settings retained from the synthetic prototype

| Setting | Value |
| --- | --- |
| Recent-movement horizon | 5 sessions |
| Volatility estimate | 63 sessions; sample standard deviation |
| Market beta / correlation window | 126 sessions |
| Shock clipping | -5 to +5 scaling units |
| Gross / name exposure ceilings | 100% / 8% of post-cost NAV |
| Base trading cost | 5 bps per dollar bought or sold |
| Alternative trading costs | 0, 10 and 20 bps |
| Annual short borrow | 2%, ACT/365 |
| Initial capital per phase | USD 100,000 |
| Execution | Decision at t; trade at t+1 close; first new-position P&L at t+2 |

Equation 2. Volatility-scaled recent movement

$$x_{i,t}=\operatorname{clip}\left(\frac{\sum_{u=t-h+1}^{t}\log(1+r_{i,u})}{\widehat{\sigma}_{i,t}\sqrt{h}},-5,5\right) \qquad (2)$$

Equation 2 scales recent movement by trailing volatility. Where: h = 5 and sigma-hat is the 63-session daily sample standard deviation. This is a project scaling rule, not a calibrated normal-distribution z-score. The five-day horizon and clipping bounds were not inferred from the cited papers or optimised on these historical results.

Equation 3. Baseline reversal score

$$s^{\mathrm{base}}_{i,t}=-x_{i,t} \qquad (3)$$

Equation 3 assigns a negative raw score to a positive recent movement. The sign expresses the reversal hypothesis discussed in Section 1; it is followed by portfolio construction rather than interpreted directly as an order.

Source: **market_neutral/historical.py**, function **baseline_decisions**. Selected executable lines; surrounding input checks remain in the module.

Listing 1. Constructing the historical reversal score

```python
volatility = r[t + 1 - config.volatility_window:t + 1].std(axis=0, ddof=1)
if (volatility <= 1e-12).any():
    raise ValueError("A constant stock return series needs an explicit eligibility rule")
shock = np.log1p(r[t + 1 - config.signal_window:t + 1]).sum(axis=0)
shock = np.clip(shock / (volatility * np.sqrt(config.signal_window)), -5, 5)
weights.iloc[t] = neutral_weights(-shock, beta, config.gross_limit, config.position_limit)
```

### 3.1. Beta estimation and interpretation

In *Capital Asset Prices* (1964), Sharpe develops the relationship between asset risk and market equilibrium [3]. This supplies the context for measuring systematic market sensitivity. The implementation below uses a trailing OLS slope to SPY as an operational estimate; it does not assume that the CAPM describes every stock return.

Equation 4. Trailing market-beta estimate

$$\widehat{\beta}_{i,t}=\frac{\sum_{u=t-m+1}^{t}(r_{i,u}-\bar r_i)(r_{M,u}-\bar r_M)}{\sum_{u=t-m+1}^{t}(r_{M,u}-\bar r_M)^2} \qquad (4)$$

Equation 4 is the intercept-inclusive OLS slope. Where: m = 126, M identifies SPY and the bars denote means within that trailing window. A benchmark window with negligible variance is rejected. Each estimate is available at its decision close and is shifted before execution.

Fama and French, in *Common risk factors in the returns on stocks and bonds* (1993), identify common equity variation beyond the overall market factor [4]. Therefore, neutralising a single SPY beta does not establish neutrality to every economic risk. This milestone does not constrain sector, size, value or momentum exposure.

## 4. Portfolio construction and exposure limits

Golub and Van Loan discuss least-squares and rank-deficient problems in *Matrix Computations* (2013), particularly Chapter 5 [14]. Using that standard projection framework, this project removes the components of each score that load on the constant vector and the estimated market-beta vector. A least-squares solve is used in the code so that identical beta estimates do not require an invertible normal-equations matrix.

Equation 5. Projection away from dollar and estimated-beta exposure

$$A_t=[\mathbf{1},\widehat{\beta}_t],\qquad q_t=s_t-A_t A_t^{+}s_t \qquad (5)$$

Equation 5 defines the projected score q. Where: A contains the two exposure directions and A+ denotes the Moore-Penrose pseudoinverse. The final weights are obtained by uniform rescaling. An effectively zero projected score gives a flat portfolio.

Equation 6. Target portfolio constraints

$$\mathbf{1}^{T}w_t=0,\quad \widehat{\beta}_t^{T}w_t=0,\quad \|w_t\|_1\leq G,\quad \|w_t\|_{\infty}\leq b \qquad (6)$$

Equation 6 states the operational definition of neutrality and the exposure ceilings. Where: G = 1 and b = 0.08. At full utilisation, gross exposure is approximately 50% long plus 50% short. If the name limit binds, all positions shrink by the same factor; clipping names independently would generally disturb the exposure constraints.

Source: **market_neutral/portfolio.py**, function **neutral_weights**. Selected executable lines; surrounding input checks remain in the module.

Listing 2. Preserving neutrality while enforcing a position ceiling

```python
exposures = np.column_stack([np.ones(len(score)), beta])
neutral = score - exposures @ np.linalg.lstsq(exposures, score, rcond=None)[0]
gross = np.abs(neutral).sum()
if gross <= 1e-10 * max(1.0, np.linalg.norm(score)):
    return np.zeros_like(score)
weights = neutral * (gross_limit / gross)
weights *= min(1.0, position_limit / np.abs(weights).max())
```

The constraints apply to post-cost target weights at the rebalance. The beta vector is an estimate from the previous decision close. Subsequent price drift and estimation error can produce realised beta even when the recorded estimated exposure is numerically zero.

## 5. Graph relationships and diffusion

As Mantegna explains in *Hierarchical structure in financial markets* (1999), a stock-return correlation matrix can support a graph representation that reveals an economically meaningful organisation [6]. His minimum-spanning-tree construction is not reproduced here. The project uses a symmetric union of positive-correlation neighbour selections, preserving up to five directed neighbours above 0.20 before symmetrisation.

Chung introduces graph Laplacians and their spectra in *Spectral Graph Theory* (1997) [7]. The distinction between Laplacian conventions matters: Equation 7 uses the combinatorial D - W matrix divided by the mean weighted degree, rather than the symmetric degree-normalised Laplacian emphasised in much of Chung's treatment.

Equation 7. Scaled combinatorial graph Laplacian

$$D_{ii}=\sum_j W_{ij},\qquad L=\frac{D-W}{\bar d} \qquad (7)$$

Equation 7 defines W as the symmetric adjacency matrix and d-bar as the mean weighted degree. An empty graph uses L = 0. The scale choice is specific to this project and gives the diffusion-time parameter a more comparable magnitude as connectivity changes.

Kondor and Lafferty, in *Diffusion Kernels on Graphs and Other Discrete Input Spaces* (2002), construct graph kernels through matrix exponentiation and connect them to heat diffusion [8]. This motivates the smoothing operator in Equation 8. It does not establish that its residual is a profitable financial signal.

Equation 8. Graph heat diffusion

$$\widetilde{x}_t=\exp(-\tau L_t)x_t \qquad (8)$$

Equation 8 smooths the observed shock over the graph. Where: tau = 1 in the current prototype. The implementation uses a symmetric eigendecomposition and has been checked against a direct matrix exponential, constant preservation and decreasing graph energy.

Equation 9. Proposed graph-relative reversal score

$$s_t^{\mathrm{graph}}=-(x_t-\widetilde{x}_t) \qquad (9)$$

Equation 9 is the proposed trading rule. It reverses deviations from the diffused value before applying the same portfolio constraints. The graph score has been implemented on synthetic data, but its historical performance is intentionally not evaluated in Milestone 2.

## 5.1. Interactive view of the historical structure

![Figure 1. Historical 126-session correlation matrix at the last validation date](../outputs/historical/05-correlation-snapshot.png)

Figure 1 gives a static view of the last validation snapshot. The companion **Historical-Correlation-Explorer.html** contains 120 monthly frames, with rotation, zoom, a date slider and playback. Each frame uses trailing observations through the displayed date; no final-holdout data enter the surface.

The surface height is correlation, not expected return. Asset order remains fixed and the asset axes are discrete. The mesh joins neighbouring cells only for display, so values between stock labels should not be interpreted as estimated relationships between intermediate assets. The full correlation matrix is also distinct from the thresholded neighbour graph used by the strategy.

## 6. Execution timing and portfolio accounting

The accounting convention is deliberately explicit: a close-t observation produces a decision, the decision trades at close t+1, and the newly formed position first earns the return ending at close t+2. This is a modelling convention chosen to avoid obtaining a close price and simultaneously earning the return ending at that same close. It remains an approximation to executable orders.

Source: **market_neutral/historical.py**, function **phase_inputs**. Selected executable lines; surrounding input checks remain in the module.

Listing 3. Delaying decisions before slicing the evaluation phase

```python
execution = weights.shift(1, fill_value=0.)
exposure = betas.shift(1)
mask = (returns.index >= pd.Timestamp(start)) & (returns.index <= pd.Timestamp(end))
```

Listing 3 shows why the shift occurs before period slicing. The first execution in a phase may use the preceding session's valid decision, but each phase begins with a flat book and fresh capital. The final close liquidates positions. Thus neither entry costs nor terminal closing costs disappear at an evaluation boundary.

Equation 10. Short-borrow accrual

$$B_t=a\frac{\Delta_t}{365}\sum_i\max(-v_{i,t-1},0) \qquad (10)$$

Equation 10 charges the annual rate a on the prior close's absolute short notional v. Delta counts elapsed calendar days, including weekends. This uniform borrow assumption is illustrative; it is not a historical security-level borrow series.

Equation 11. Post-cost NAV and drift-aware trading cost

$$V_t^{\mathrm{after}}+c\sum_i|w_{i,t}V_t^{\mathrm{after}}-v_{i,t}^{\mathrm{marked}}|=V_t^{\mathrm{before}} \qquad (11)$$

Equation 11 solves for NAV after trading fees. Where: c is the per-dollar fee and marked notionals incorporate the day's price changes. NAV before trading already reflects P&amp;L and borrow. The scalar solve makes target weights refer to equity after fees, avoiding a small exposure overshoot caused solely by transaction costs.

Equation 12. Net-return reconciliation

$$R_t^{\mathrm{net}}=\frac{\mathrm{PnL}_t-C_t-B_t}{V_{t-1}^{\mathrm{after}}} \qquad (12)$$

Equation 12 reconciles gross position P&amp;L, trading cost C and borrow cost B to net return. Turnover counts every dollar bought and every dollar sold, divided by start-of-day NAV. Cash interest, financing rebates, margin constraints and nonlinear market impact are not included.

Source: **market_neutral/backtest.py**, function **execute_targets**. Selected executable lines; surrounding input checks remain in the module.

Listing 4. Solving for equity after transaction costs

```python
def balance(after):
    return after + cost_rate * np.abs(w * after - marked).sum() - nav_before_trade
if balance(0) >= 0:
    raise ValueError("Cannot fund trading costs")
nav = float(brentq(balance, 0, nav_before_trade, xtol=1e-10)) if cost_rate else nav_before_trade
```

## 7. Historical baseline results

Table 7. Baseline performance at 5 bps and 2% annual short borrow

| Metric | Development | Validation |
| --- | --- | --- |
| Total net return | -19.79% | -16.44% |
| Annualised net return | -3.10% | -5.83% |
| Annualised volatility | 3.17% | 3.35% |
| Zero-cash-rate Sharpe | -0.98 | -1.78 |
| Maximum drawdown | -24.99% | -18.49% |
| Realised SPY beta | 0.0202 | 0.0169 |
| Mean daily turnover | 41.00% | 39.62% |
| Mean gross exposure | 62.78% | 61.29% |
| Maximum absolute dollar exposure | 2.41e-15 | 3.52e-15 |
| Maximum absolute estimated beta | 2.29e-15 | 3.39e-15 |

Table 7 reports a negative annualised return in both phases: -3.10% in development and -5.83% in validation. The numerical exposure constraints are satisfied, but these constraints do not imply a viable strategy. The practical issue is whether the signal can earn enough before costs to support its turnover.

Lo, in *The Statistics of Sharpe Ratios* (2002), explains why return dependence and estimation error affect Sharpe-ratio interpretation [11]. The statistic below uses the conventional square-root-of-time scaling and a zero cash rate for descriptive comparison. It is not a dependence-adjusted significance test or a confidence interval.

Equation 13. Descriptive annualised Sharpe statistic

$$\widehat{S}=\sqrt{252}\,\frac{\overline{R^{\mathrm{net}}}}{s(R^{\mathrm{net}})} \qquad (13)$$

Equation 13 uses the sample daily standard deviation. It is labelled as a zero-cash-rate statistic because cash interest is not modelled. Comparisons with an external fund's published Sharpe would require matching return and financing conventions.

Equation 14. Drawdown from the running capital peak

$$DD_t=\frac{V_t}{\max(V_0,V_1,\ldots,V_t)}-1 \qquad (14)$$

Equation 14 includes initial capital in the running peak, so an early loss is counted. The reported maximum drawdown is the most negative observed value, including the final liquidation date.

### 7.1. Capital paths and cost sensitivity

![Figure 2. Net historical capital and drawdown; phases start with separate capital](../outputs/historical/03-historical-baseline.png)

Table 8. All predeclared trading-cost scenarios; short borrow remains 2%

| Cost per dollar | Development CAGR | Validation CAGR |
| --- | --- | --- |
| 0 bps | 2.03% | -1.00% |
| 5 bps | -3.10% | -5.83% |
| 10 bps | -7.98% | -10.41% |
| 20 bps | -17.02% | -18.93% |

The zero-trading-fee scenario is not a costless portfolio: it still pays short borrow. Development is positive under that scenario, whereas validation is negative. Consequently, the validation failure cannot be attributed only to the 5 bps trading-fee assumption. The signal itself requires a stronger empirical comparison.

## 7.2. Interpretation and remaining uncertainty

![Figure 3. Sensitivity to trading costs and rolling realised market beta](../outputs/historical/04-costs-and-beta.png)

Figure 3 demonstrates two separate issues. Net returns decline as the stated cost per dollar increases. Realised beta also varies through time despite the target constraint. The variation reflects an estimated hedge, a finite rolling measurement window and changing returns; it is not a contradiction of the recorded numerical neutrality checks.

Bailey and colleagues, in *The probability of backtest overfitting* (2017), emphasise that a held-out sample alone does not account for repeated strategy searches [10]. For this reason, the project records each experiment and does not interpret its chronological split as proof against overfitting. No PBO estimate, CSCV analysis or White reality-check statistic has been calculated in this milestone.

The next comparison will retain these dates, costs, exposure ceilings and execution rules. Graph performance will be shown beside the baseline, including unfavourable results. Any subsequent tuning must be confined to the development process and documented before the reserved final test is released.

## 8. Planned persistent-homology extension

Edelsbrunner, Letscher and Zomorodian formalise feature persistence through a filtration in *Topological Persistence and Simplification* (2002) [12]. Their framework motivates measuring how connected components and loops appear and disappear as a scale changes. Persistence is a mathematical description of structure, not by itself a financial prediction.

Equation 15. Correlation-derived distance for the proposed topology study

$$d_{ij,t}=\sqrt{2(1-\rho_{ij,t})} \qquad (15)$$

Equation 15 relates correlation to a distance between standardised return series, following the financial correlation-distance construction associated with Mantegna [6]. It will use a complete valid correlation matrix; the sparse positive-neighbour adjacency matrix must not be substituted for that metric space.

Gidea and Katz, in *Topological data analysis of financial time series: Landscapes of crashes* (2018), study persistence landscapes from sliding-window point clouds of market-index returns [13]. That is relevant precedent, but the planned asset correlation-distance construction here is different. Their findings do not establish that our proposed H0/H1 features will improve trading performance.

The extension will require numerical checks on known shapes, explicit treatment of infinite H0 bars, stable feature definitions and training-only thresholds. Mean correlation and realised volatility will serve as simpler controls. The persistent-homology module remains unimplemented in this milestone.

## 9. Reproducibility and subsequent milestones

Table 9. Research artifacts and completion state

| Artifact | Current status |
| --- | --- |
| Historical data and protocol | Cached inputs, source metadata, SHA-256 hashes and guarded period boundaries |
| Baseline backtest | Development and validation completed; all four fee scenarios retained |
| Graph trading comparison | Synthetic prototype exists; historical comparison next |
| Interactive 3D explorer | Standalone HTML with 120 monthly correlation frames |
| Persistent homology | Planned; no extracted features or regime results claimed |
| Final holdout | 2020-2025 reserved; not acquired or evaluated |
| GitHub readiness | Requirements, tests, notebook, source, rebuild scripts and CI configuration |
| Public repository / LinkedIn page | Planned for final presentation; not published by this milestone |

The private research bundle retains the acquired observations for exact offline replay. A public GitHub checkout will exclude provider input caches and regenerate them through the acquisition script. Provider revisions can change a fresh download, so the recorded hashes distinguish exact snapshot reproduction from rerunning the same method on a new data vintage. Permission to redistribute vendor data is not inferred from its technical accessibility.

The paper builder extracts its code excerpts directly from the research modules and generates the contents and lists from captions. Future versions will retain the title page, abstract, abbreviations, symbol definitions, numbered equations, figure and table lists, code listings and author-led references. The final public presentation will explain both the results and the limits of the evidence.

## References

[1] M. Avellaneda and J.-H. Lee (2010). *Statistical arbitrage in the US equities market*. Quantitative Finance, 10(7), 761-782. <link href="https://doi.org/10.1080/14697680903124632" color="#176960">DOI: 10.1080/14697680903124632</link>.

[2] A. W. Lo and A. C. MacKinlay (1990). *When Are Contrarian Profits Due to Stock Market Overreaction?*. The Review of Financial Studies, 3(2), 175-205. <link href="https://doi.org/10.1093/rfs/3.2.175" color="#176960">DOI: 10.1093/rfs/3.2.175</link>.

[3] W. F. Sharpe (1964). *Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk*. The Journal of Finance, 19(3), 425-442. <link href="https://doi.org/10.1111/j.1540-6261.1964.tb02865.x" color="#176960">DOI: 10.1111/j.1540-6261.1964.tb02865.x</link>.

[4] E. F. Fama and K. R. French (1993). *Common risk factors in the returns on stocks and bonds*. Journal of Financial Economics, 33(1), 3-56. <link href="https://doi.org/10.1016/0304-405X(93)90023-5" color="#176960">DOI: 10.1016/0304-405X(93)90023-5</link>.

[5] T. Shumway (1997). *The Delisting Bias in CRSP Data*. The Journal of Finance, 52(1), 327-340. <link href="https://doi.org/10.1111/j.1540-6261.1997.tb03818.x" color="#176960">DOI: 10.1111/j.1540-6261.1997.tb03818.x</link>.

[6] R. N. Mantegna (1999). *Hierarchical structure in financial markets*. The European Physical Journal B, 11, 193-197. <link href="https://doi.org/10.1007/s100510050929" color="#176960">DOI: 10.1007/s100510050929</link>.

[7] F. R. K. Chung (1997). *Spectral Graph Theory*. CBMS Regional Conference Series in Mathematics, vol. 92, American Mathematical Society. <link href="https://doi.org/10.1090/cbms/092" color="#176960">DOI: 10.1090/cbms/092</link>.

[8] R. I. Kondor and J. D. Lafferty (2002). *Diffusion Kernels on Graphs and Other Discrete Input Spaces*. Proceedings of the 19th International Conference on Machine Learning, 315-322. <link href="https://dl.acm.org/doi/10.5555/645531.655996" color="#176960">DOI: 10.5555/645531.655996</link>.

[9] H. White (2000). *A Reality Check for Data Snooping*. Econometrica, 68(5), 1097-1126. <link href="https://doi.org/10.1111/1468-0262.00152" color="#176960">DOI: 10.1111/1468-0262.00152</link>.

[10] D. H. Bailey, J. M. Borwein, M. Lopez de Prado and Q. J. Zhu (2017). *The probability of backtest overfitting*. The Journal of Computational Finance, 20(4), 39-69. <link href="https://doi.org/10.21314/JCF.2016.322" color="#176960">DOI: 10.21314/JCF.2016.322</link>.

[11] A. W. Lo (2002). *The Statistics of Sharpe Ratios*. Financial Analysts Journal, 58(4), 36-52. <link href="https://doi.org/10.2469/faj.v58.n4.2453" color="#176960">DOI: 10.2469/faj.v58.n4.2453</link>.

[12] H. Edelsbrunner, D. Letscher and A. Zomorodian (2002). *Topological Persistence and Simplification*. Discrete &amp; Computational Geometry, 28, 511-533. <link href="https://doi.org/10.1007/s00454-002-2885-2" color="#176960">DOI: 10.1007/s00454-002-2885-2</link>.

[13] M. Gidea and Y. Katz (2018). *Topological data analysis of financial time series: Landscapes of crashes*. Physica A: Statistical Mechanics and its Applications, 491, 820-834. <link href="https://doi.org/10.1016/j.physa.2017.09.028" color="#176960">DOI: 10.1016/j.physa.2017.09.028</link>.

[14] G. H. Golub and C. F. Van Loan (2013). *Matrix Computations*. 4th ed., Johns Hopkins University Press; Chapter 5: Orthogonalization and Least Squares. <link href="https://www.press.jhu.edu/books/title/10678/matrix-computations" color="#176960">DOI: 10.56021/9781421407944</link>.

[15] Yahoo Finance (2026). *Historical daily chart responses for the declared stock basket and SPY*. Primary data source, accessed 21 September 2026; per-symbol URLs and hashes in data/download-manifest.json. <link href="https://query1.finance.yahoo.com/v8/finance/chart/SPY?period1=1230768000&amp;period2=1577836800&amp;interval=1d&amp;events=div%2Csplits" color="#176960">Primary data record</link>.

References 1-14 are journal articles, scholarly books or a peer-reviewed conference paper. Reference 15 identifies the primary data service. The source register records the accessed version and the role of each reference. No citation is intended to imply that another author tested this project's exact strategy.