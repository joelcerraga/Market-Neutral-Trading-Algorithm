# Market-Neutral Trading Algorithm

Graph diffusion, persistent homology and reproducible empirical research

**Joel Cerraga**

Quantitative research project · Final paper · March 2026

Research question

Can relationships between stock returns improve a constrained reversal strategy after trading costs, borrowing costs and market exposure are accounted for?

This paper presents the completed research from numerical foundations through the fixed final evaluation. The milestone record is retained to make the sequence of decisions and the information available at each stage explicit.

## Abstract

This project investigates whether relationships between stock returns can improve a constrained equity reversal strategy after trading and borrowing costs. A reproducible Python framework compares a volatility-scaled baseline with a graph-relative signal formed using correlation networks and Laplacian diffusion. Both portfolios are constrained to approximately zero dollar exposure and estimated market-beta exposure, subject to gross and individual-position ceilings. Decisions, delayed execution, price drift, short borrowing and terminal liquidation are accounted for explicitly.

The study uses a fixed basket of 24 surviving US companies and SPY. Development covers 2010–2016, validation covers 2017–2019, and a separately specified final evaluation covers 1,508 sessions in 2020–2025. At 5 basis points per dollar traded and 2% annual short borrow, the baseline and primary graph strategy produce final-period compound annual growth rates of −5.57% and −4.80%, respectively. The graph-minus-baseline annualised arithmetic mean is +0.73 percentage points, with a fixed-family Bonferroni-adjusted stationary-bootstrap interval from −2.14 to +3.85 percentage points. None of the four necessary evidence conditions specified before final-data acquisition is met. Matched-gross and cost controls retain the negative finding.

A parallel persistent-homology study extracts four descriptors at 63-, 126- and 252-session windows and compares them with ordinary correlation and volatility. H0 mean persistence largely overlaps mean correlation, while H1 descriptors are more sensitive to the estimation horizon. Some development-fitted descriptive relationships transfer poorly, and no topology trading overlay is introduced. Known-shape checks, exposure and accounting tests, dependence-aware uncertainty checks and diagram perturbation bounds support implementation correctness; they do not establish economic profitability.

The principal contribution is a transparent research and verification framework with retained negative results, explicit decision records and interactive companions. The fixed trading hypothesis is not supported under the declared costs and sample. Retrospective survivor selection, current-vintage adjusted prices and simplified execution and borrowing assumptions limit generalisation. The final period has now been observed and cannot serve as an untouched test for future model revisions.

**Keywords:** statistical arbitrage; market neutrality; graph Laplacian; diffusion; persistent homology; historical backtesting; reproducibility.

<!-- GENERATED_NAVIGATION -->

## List of abbreviations

Table 1. Abbreviations used in the paper

| Abbreviation | Meaning |
| --- | --- |
| ACT/365 | Actual calendar days divided by 365 |
| bps | Basis points; one basis point equals 0.01% |
| CAGR | Compound annual growth rate |
| CI | Confidence interval |
| CAPM | Capital Asset Pricing Model |
| CRSP | Center for Research in Security Prices |
| CSCV | Combinatorially symmetric cross-validation |
| CSV | Comma-separated values |
| ETF | Exchange-traded fund |
| H0 / H1 | Homology dimensions zero and one |
| HAC | Heteroskedasticity and autocorrelation consistent |
| NAV | Net asset value |
| OLS | Ordinary least squares |
| P&L | Profit and loss |
| PBO | Probability of backtest overfitting |
| pp | Percentage points |
| SB | Stationary bootstrap |
| PCA | Principal component analysis |
| SHA-256 | Secure Hash Algorithm, 256-bit digest |
| SPY | Ticker used for the S&P 500 ETF benchmark |
| TDA | Topological data analysis |
| USD | US dollars |
| VR | Vietoris–Rips |
| MST | Minimum spanning tree |
| PH | Persistent homology |
| RMSE | Root mean squared error |
| FWER | Family-wise error rate |

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
| G*; B; G | Common gross exposure; baseline/graph superscript labels |
| δ; μ; T | Paired daily difference; annualised arithmetic mean; phase sample size |
| ℓ; I* | Expected bootstrap block length; resampled observation index |
| K; γ; Ω | HAC lag count; lagged covariance; long-run variance |
| SE; λ | Standard error; graph-Laplacian eigenvalue |
| W_len; ε | Trailing topology window length; filtration edge threshold |
| 𝒟_q; b_a; d_a; ℓ_a | Homology-q diagram; interval birth; death; lifetime |
| λ_k(ε) | kth persistence-landscape layer; distinct from Laplacian eigenvalue λ |
| d_B; η | Bottleneck diagram distance; maximum labelled pairwise-distance change |
| z; θ̂; R² | Standardised control vector; fitted control coefficients; coefficient of determination |
| F₂ | Field with two elements, used for homology coefficients |
| α; m_F; I_j | Family error budget; number of declared means; interval for mean j |
| ξ_t; μ_j | Vector of the three final daily comparisons; annualised arithmetic mean j |
| 𝒪 | Set of overlapping 2019 return dates used for the vintage audit |

## 1. Introduction and research context

As Avellaneda and Lee (2010) explain in *Statistical arbitrage in the US equities market*, systematic equity strategies can use factor-adjusted residual behaviour to form market-neutral portfolios. Their PCA- and ETF-based construction provides context for this research. The present baseline and graph residual are different models, and no result from their paper is transferred to this stock basket.

Lo and MacKinlay (1990), in *When Are Contrarian Profits Due to Stock Market Overreaction?*, show that contrarian profits need not arise solely from overreaction. This distinction is relevant because reversing a recent stock movement is a trading hypothesis, not proof that its price is incorrect. Accordingly, the first historical experiment retains a simple baseline and evaluates its costs and exposures before adding graph complexity.

The project builds on the earlier SPX density study in its use of controlled numerical checks, reusable Python modules and explanatory notebooks. Its empirical objective is different: it evaluates a trading rule rather than recovering an option-implied probability density. The reusable source structure and interactive companions support a reproducible public presentation; GitHub and LinkedIn publication remain separate release steps.

### 1.1. Questions and scope

Three questions guide the work. First, does the baseline remain viable after explicit costs? Second, does graph diffusion add information under an otherwise identical experiment? Third, can persistent-homology features add useful regime information beyond simpler measures such as volatility and mean correlation? Milestones 2 and 3 evaluate the first two questions, and Milestone 5 tests the fixed comparison on the reserved period. Milestone 4 studies topology as a descriptor; its incremental financial usefulness remains untested.

The experimental code and the scientific references have separate roles. The references justify established concepts and numerical relationships; parameter settings, the fixed basket and the proposed graph score are choices made for this project. The historical comparison below assesses the fixed graph candidate without claiming that its parameter values are justified by the references.

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

The primary observations are Yahoo Finance (2026a) daily chart responses. The analysis uses the supplied **adjclose** field; close, volume, dividend events and split events are retained for audit. The data are current-vintage vendor observations rather than a point-in-time archive. Historical adjustment accuracy has not been independently certified, and dividends are not added a second time to adjusted-price returns.

Table 4. Chronological allocation fixed before baseline performance was inspected

| Period | Dates | Use |
| --- | --- | --- |
| Warm-up | 2009 | Trailing estimates only |
| Development | 2010-2016 | Baseline construction and diagnostic evaluation |
| Validation | 2017-2019 | Declared chronological check; not a final test |
| Final holdout | 2020-2025 | Reserved in Milestones 2–4; separately released and evaluated in Section 10 |

As White (2000) explains in *A Reality Check for Data Snooping*, repeated model selection on the same observations can create apparently favourable findings by chance. Therefore, the universe, dates, cost scenarios and baseline settings were written to a local protocol and hashed before the equity study was run. This record is not external preregistration, and it does not eliminate knowledge of historical market events.

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

Shumway (1997), in *The Delisting Bias in CRSP Data*, documents the importance of omitted adverse delisting returns. This project has a broader selection limitation: its named basket contains companies that survived to the selection date. It is consequently an exploratory fixed-basket study and cannot establish performance for the historical investable equity universe.

The loader does not silently forward-fill missing prices or intersect mismatched calendars. Positive prices and reported volumes are required throughout. A 20-session close-times-volume proxy is reported, but this is not a calibrated capacity limit. Borrow availability, suspended securities and a complete corporate-action reconstruction remain unresolved for a production equity simulator.

Equation 1. Simple adjusted-price return

$$r_{i,t}=\frac{P_{i,t}}{P_{i,t-1}}-1 \qquad (1)$$

Equation 1 defines the input return. Where: P is the supplied adjusted-price series, i denotes the asset and t denotes the observed session. Avellaneda and Lee (2010) also formulate their historical return analysis using dividend-adjusted prices. Here the resulting return-bearing notionals are an approximation; the ledger does not model raw execution prices and dividend cash flows separately.

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

In *Capital Asset Prices*, Sharpe (1964) develops the relationship between asset risk and market equilibrium. This supplies the context for measuring systematic market sensitivity. The implementation below uses a trailing OLS slope to SPY as an operational estimate; it does not assume that the CAPM describes every stock return.

Equation 4. Trailing market-beta estimate

$$\widehat{\beta}_{i,t}=\frac{\sum_{u=t-m+1}^{t}(r_{i,u}-\bar r_i)(r_{M,u}-\bar r_M)}{\sum_{u=t-m+1}^{t}(r_{M,u}-\bar r_M)^2} \qquad (4)$$

Equation 4 is the intercept-inclusive OLS slope. Where: m = 126, M identifies SPY and the bars denote means within that trailing window. A benchmark window with negligible variance is rejected. Each estimate is available at its decision close and is shifted before execution.

Fama and French (1993), in *Common risk factors in the returns on stocks and bonds*, identify common equity variation beyond the overall market factor. Therefore, neutralising a single SPY beta does not establish neutrality to every economic risk. The portfolios do not constrain sector, size, value or momentum exposure.

## 4. Portfolio construction and exposure limits

Golub and Van Loan (2013) discuss least-squares and rank-deficient problems in *Matrix Computations*, particularly Chapter 5. Using that standard projection framework, this project removes the components of each score that load on the constant vector and the estimated market-beta vector. A least-squares solve is used in the code so that identical beta estimates do not require an invertible normal-equations matrix.

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

As Mantegna (1999) explains in *Hierarchical structure in financial markets*, a stock-return correlation matrix can support a graph representation that reveals an economically meaningful organisation. His minimum-spanning-tree construction is not reproduced here. The project uses a symmetric union of positive-correlation neighbour selections, preserving up to five directed neighbours above 0.20 before symmetrisation.

Chung (1997) introduces graph Laplacians and their spectra in *Spectral Graph Theory*. The distinction between Laplacian conventions matters: Equation 7 uses the combinatorial D - W matrix divided by the mean weighted degree, rather than the symmetric degree-normalised Laplacian emphasised in much of Chung's treatment.

Equation 7. Scaled combinatorial graph Laplacian

$$D_{ii}=\sum_j W_{ij},\qquad L=\frac{D-W}{\bar d} \qquad (7)$$

Equation 7 defines W as the symmetric adjacency matrix and d-bar as the mean weighted degree. An empty graph uses L = 0. The scale choice is specific to this project and gives the diffusion-time parameter a more comparable magnitude as connectivity changes.

Kondor and Lafferty (2002), in *Diffusion Kernels on Graphs and Other Discrete Input Spaces*, construct graph kernels through matrix exponentiation and connect them to heat diffusion. This motivates the smoothing operator in Equation 8. It does not establish that its residual is a profitable financial signal.

Equation 8. Graph heat diffusion

$$\widetilde{x}_t=\exp(-\tau L_t)x_t \qquad (8)$$

Equation 8 smooths the observed shock over the graph. Where: tau = 1 in the primary specification. The implementation uses a symmetric eigendecomposition and has been checked against a direct matrix exponential, constant preservation and decreasing graph energy.

Equation 9. Proposed graph-relative reversal score

$$s_t^{\mathrm{graph}}=-(x_t-\widetilde{x}_t) \qquad (9)$$

Equation 9 is the proposed trading rule. It reverses deviations from the diffused value before applying the same portfolio constraints. The graph score was first checked on synthetic data; its historical comparison is reported in Section 8.

### 5.1. Interactive view of the historical structure

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

Equation 11 solves for NAV after trading fees. Where: c is the per-dollar fee and marked notionals incorporate the day's price changes. NAV before trading already reflects P&L and borrow. The scalar solve makes target weights refer to equity after fees, avoiding a small exposure overshoot caused solely by transaction costs.

Equation 12. Net-return reconciliation

$$R_t^{\mathrm{net}}=\frac{\mathrm{PnL}_t-C_t-B_t}{V_{t-1}^{\mathrm{after}}} \qquad (12)$$

Equation 12 reconciles gross position P&L, trading cost C and borrow cost B to net return. Turnover counts every dollar bought and every dollar sold, divided by start-of-day NAV. Cash interest, financing rebates, margin constraints and nonlinear market impact are not included.

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

Lo (2002), in *The Statistics of Sharpe Ratios*, explains why return dependence and estimation error affect Sharpe-ratio interpretation. The statistic below uses the conventional square-root-of-time scaling and a zero cash rate for descriptive comparison. It is not a dependence-adjusted significance test or a confidence interval.

Equation 13. Descriptive annualised Sharpe statistic

$$\widehat{S}=\sqrt{252}\,\frac{\overline{R^{\mathrm{net}}}}{s(R^{\mathrm{net}})} \qquad (13)$$

Equation 13 uses the sample daily standard deviation. It is labelled as a zero-cash-rate statistic because cash interest is not modelled. Comparisons with an external fund's published Sharpe would require matching return and financing conventions.

Equation 14. Drawdown from the running capital peak

$$DD_t=\frac{V_t}{\max(V_0,V_1,\ldots,V_t)}-1 \qquad (14)$$

Equation 14 includes initial capital in the running peak, so an early loss is counted. The reported maximum drawdown is the most negative observed value, including the final liquidation date.

### 7.1. Capital paths and cost sensitivity

![Figure 2. Baseline capital and drawdown; the holdout annotation records Milestone 2](../outputs/historical/03-historical-baseline.png)

Table 8. All predeclared trading-cost scenarios; short borrow remains 2%

| Cost per dollar | Development CAGR | Validation CAGR |
| --- | --- | --- |
| 0 bps | 2.03% | -1.00% |
| 5 bps | -3.10% | -5.83% |
| 10 bps | -7.98% | -10.41% |
| 20 bps | -17.02% | -18.93% |

The zero-trading-fee scenario is not a costless portfolio: it still pays short borrow. Development is positive under that scenario, whereas validation is negative. Consequently, the validation failure cannot be attributed only to the 5 bps trading-fee assumption. The signal itself requires a stronger empirical comparison.

### 7.2. Interpretation and remaining uncertainty

![Figure 3. Sensitivity to trading costs and rolling realised market beta](../outputs/historical/04-costs-and-beta.png)

Figure 3 demonstrates two separate issues. Net returns decline as the stated cost per dollar increases. Realised beta also varies through time despite the target constraint. The variation reflects an estimated hedge, a finite rolling measurement window and changing returns; it is not a contradiction of the recorded numerical neutrality checks.

Bailey et al. (2017), in *The probability of backtest overfitting*, emphasise that a held-out sample alone does not account for repeated strategy searches. For this reason, the project records each experiment and does not interpret its chronological split as proof against overfitting. No PBO estimate, CSCV analysis or White reality-check statistic is calculated in this study.

The comparison in Section 8 retains these dates, costs, exposure ceilings and execution rules, including the unfavourable results. This requirement was carried into the final protocol in Section 10; no alternative was promoted after the final observations were inspected.

## 8. Historical graph comparison

Milestone 3 evaluates the graph rule in Equation 9 using exactly the acquired observations and accounting conventions from the historical baseline. The baseline outcome was known when this comparison began. The graph settings were inherited from the synthetic prototype, and a separate local protocol was hashed before the first historical graph run. Neither development nor validation is represented as a newly untouched dataset.

Table 9. Predeclared comparison and sensitivity design

| Component | Fixed design |
| --- | --- |
| Primary candidate | 126-session graph; five directed neighbours above 0.20; symmetric union; diffusion time one |
| Trading-fee sensitivity | 0, 5, 10 and 20 bps; 2% annual borrow |
| Diffusion-time sensitivity | 0.5, 1 and 2; every trading-fee combination retained |
| Borrow sensitivity | 0%, 2% and 5%; baseline and primary graph at 5 bps |
| Exposure control | Both primary targets scaled down to their common daily gross exposure; 5 bps and 2% borrow |
| Uncertainty | Paired stationary bootstrap, 5,000 replicates; mean block lengths 5/10/20; HAC with 10 lags |
| Experiment record | 44 distinct backtests completed; no replacement of the primary candidate |
| Holdout at Milestone 3 | 2020–2025 was unacquired; Section 10 records its later release |

As White (2000) argues in *A Reality Check for Data Snooping*, searching across alternatives can produce misleading apparent success. For this reason, all declared sensitivity results are retained and the primary candidate remains tau = 1. This protocol does not implement White's multiple-comparison test or retrospectively remove earlier knowledge of the baseline.

Source: **market_neutral/strategy.py**, function **build_decisions**. Selected executable lines; surrounding input checks remain in the module.

Listing 5. Constructing the graph-relative score from the same observed shock

```python
corr, adjacency, laplacian = correlation_graph(
    r[t + 1 - config.correlation_window:t + 1],
    config.neighbours, config.minimum_correlation)
smooth = heat_diffusion(shock, laplacian, config.diffusion_time)
scores = {"baseline": -shock, "graph": -(shock - smooth)}
```

### 8.1. Primary historical outcomes

Table 10. Primary strategies at 5 bps trading fees and 2% borrow

| Phase / model | Ann. net return | Ann. volatility | Max. drawdown | Mean gross | Mean turnover |
| --- | --- | --- | --- | --- | --- |
| Development / Baseline | -3.10% | 3.17% | -24.99% | 62.78% | 41.00% |
| Development / Graph, tau = 1 | -4.37% | 2.89% | -27.97% | 62.18% | 40.44% |
| Validation / Baseline | -5.83% | 3.35% | -18.49% | 61.29% | 39.62% |
| Validation / Graph, tau = 1 | -5.27% | 2.92% | -16.20% | 60.63% | 39.73% |

The graph candidate earns -4.37% annualised in development, compared with -3.10% for the baseline. In validation, the corresponding values are -5.27% and -5.83%. The graph-minus-baseline CAGR differences are therefore -1.26 and +0.55 percentage points. Both strategies lose money at the default costs.

![Figure 4. Baseline and graph capital paths under identical accounting conventions](../outputs/comparison/06-graph-comparison.png)

The graph portfolio has somewhat lower realised volatility and lower mean gross exposure. Equal exposure ceilings do not force equal realised capital utilisation. Therefore, the return comparison alone cannot isolate the effect of the graph signal from the portfolio scaling that follows it.

### 8.2. A causal control for gross exposure

The control below matches the two portfolios at the decision close. It reduces both targets to the smaller of their gross exposures, then applies the original execution delay. It does not scale a portfolio upward, use realised future volatility or relax a name limit. This is a project-specific diagnostic, not a claim that equal gross exposure implies equal risk.

Equation 15. Matching the gross exposure of the two decision portfolios

$$G_t^*=\min(\|w_t^B\|_1,\|w_t^G\|_1),\qquad w_t^{j,*}=w_t^j\frac{G_t^*}{\|w_t^j\|_1} \qquad (15)$$

Equation 15 defines the control for j equal to baseline B or graph G. A zero denominator gives a flat vector. Uniform shrinking preserves dollar and estimated-beta neutrality and cannot increase any absolute name weight. Risk and sector composition can still differ.

Source: **market_neutral/comparison.py**, function **match_gross_exposure**. Selected executable lines; surrounding input checks remain in the module.

Listing 6. Matching exposure without levering either portfolio upward

```python
gross_baseline = baseline.abs().sum(axis=1)
gross_graph = graph.abs().sum(axis=1)
common = np.minimum(gross_baseline, gross_graph)
controls = []
for weights, gross in [(baseline, gross_baseline), (graph, gross_graph)]:
    factor = common.div(gross.where(gross > 1e-14)).fillna(0.)
    controls.append(weights.mul(factor, axis=0))
```

Table 11. Separate backtests of the matched-gross controls

| Phase | Baseline CAGR | Graph CAGR | Difference (pp) | Common mean gross |
| --- | --- | --- | --- | --- |
| Development | -3.03% | -4.05% | -1.03 | 57.65% |
| Validation | -5.16% | -4.95% | +0.22 | 56.38% |

The validation advantage becomes smaller when gross exposure is matched, while the development disadvantage remains. This reinforces the need to discuss exposure and volatility alongside return. The controls are fully rerun portfolios, not an after-the-fact division of the original returns by average exposure.

### 8.3. Paired uncertainty with dependent observations

The uncertainty calculation concerns the paired daily net-return difference at the primary cost settings. Both strategies experience the same dates and market observations. Resampling their paired difference preserves that contemporaneous comparison; resampling the two strategies independently would discard it.

Equation 16. Paired daily difference and annualised arithmetic mean

$$\delta_t=R_t^{G,\mathrm{net}}-R_t^{B,\mathrm{net}},\qquad \widehat{\mu}_{\mathrm{ann}}=252\,\bar\delta \qquad (16)$$

Equation 16 defines the estimated annualised arithmetic difference. It is not the difference between the two compounded annual growth rates. The uncertainty intervals below refer to this mean, so their estimate should not be substituted for the CAGR difference in the performance table.

Politis and Romano (1994) introduce the stationary bootstrap in *The Stationary Bootstrap*. Nordman (2009) restates its geometric-block construction in Section 2.1 of *A note on the stationary bootstrap's variance*. Following that construction, this implementation restarts at a uniformly chosen observed date or continues circularly from the preceding sampled index.

Equation 17. Random restarts and circular continuation in the stationary bootstrap

$$\Pr(\mathrm{restart})=\ell^{-1},\qquad I_{k+1}^*=1+(I_k^*\ \mathrm{mod}\ T) \qquad (17)$$

Equation 17 gives the restart probability and the continuation rule when no restart occurs. Here ell is the expected block length, T is the phase sample size and the mathematical indices run from 1 to T. On a restart, a new index is uniform on that range. Python uses the equivalent zero-based convention.

Source: **market_neutral/inference.py**, function **stationary_indices**. Selected executable lines; surrounding input checks remain in the module.

Listing 7. Preserving blocks through random restarts and circular continuation

```python
indices = np.empty((replicates, observations), dtype=np.int32)
indices[:, 0] = rng.integers(0, observations, size=replicates)
for t in range(1, observations):
    restart = rng.random(replicates) < 1.0 / mean_block_length
    new_start = rng.integers(0, observations, size=replicates)
    indices[:, t] = np.where(restart, new_start, (indices[:, t - 1] + 1) % observations)
```

The primary interval uses 5,000 replicates and expected block length 10; lengths 5 and 20 are retained as sensitivity checks. The reported bounds are the 2.5th and 97.5th percentiles of the bootstrap mean, multiplied by 252. Seeds are specified in the protocol and derive deterministically from phase and block length. No block length is chosen because it yields a preferred conclusion.

### 8.4. HAC cross-check and interpretation

Newey and West (1987), in *A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix*, develop a covariance estimator using weighted lagged covariances. Their 1986 working-paper version was consulted for the Bartlett weights. Here the intercept-only special case supplies a second estimate of uncertainty for the paired mean.

Equation 18. Bartlett-weighted long-run variance of the paired difference

$$\widehat{\Omega}=\widehat{\gamma}_0+2\sum_{k=1}^{K}\left(1-\frac{k}{K+1}\right)\widehat{\gamma}_k \qquad (18)$$

Equation 18 uses K = 10 lags. Each gamma-hat is the sum of products of mean-centred paired differences k observations apart, divided by the full phase length T. The same T denominator is used at every lag. This convention is checked against the equivalent Bartlett quadratic form.

Equation 19. HAC standard error of the annualised arithmetic difference

$$\widehat{\mathrm{SE}}(\widehat{\mu}_{\mathrm{ann}})=252\sqrt{\widehat{\Omega}/T} \qquad (19)$$

Equation 19 scales the standard error of the sample mean by 252. It does not use square-root-of-252 volatility scaling. The approximate 95% HAC interval adds and subtracts the standard-normal critical value times this standard error.

Source: **market_neutral/inference.py**, function **hac_mean_interval**. Selected executable lines; surrounding input checks remain in the module.

Listing 8. Accumulating serial covariance with Bartlett weights

```python
centered = x - x.mean()
n = len(x)
long_run_variance = float(centered @ centered / n)
for lag in range(1, lags + 1):
    covariance = float(centered[lag:] @ centered[:-lag] / n)
    long_run_variance += 2 * (1 - lag / (lags + 1)) * covariance
```

Table 12. Pointwise uncertainty for the primary paired-return difference

| Phase | Mean difference (pp) | 95% bootstrap interval (pp) | 95% HAC interval (pp) |
| --- | --- | --- | --- |
| Development | -1.32 | [-2.18, -0.47] | [-2.15, -0.49] |
| Validation | +0.57 | [-1.16, +2.37] | [-1.16, +2.30] |

The development intervals lie below zero, while every validation interval spans zero. Thus the modest positive validation point estimate does not establish a reliable graph advantage. These are approximate, pointwise intervals conditional on the observed policies and basket. They assume adequate stationarity and weak dependence, do not refit signals on bootstrapped price paths, and cannot correct survivorship bias, historical selection or repeated model searching.

### 8.5. Sensitivity and the economic effect of costs

![Figure 5. Stationary-bootstrap and HAC intervals for the paired mean](../outputs/comparison/08-paired-uncertainty.png)

![Figure 6. Graph-minus-baseline CAGR across every declared fee and diffusion time](../outputs/comparison/07-diffusion-and-costs.png)

Every tested diffusion time underperforms the baseline in development and improves its validation CAGR slightly. None is profitable in validation, even when trading fees are zero and borrow remains 2%. This pattern is retained without promoting a different diffusion time to the primary specification. The complete scenario values and calendar-year returns are supplied as machine-readable outputs.

### 8.6. Gross contribution, borrow and turnover

![Figure 7. Annualised arithmetic return contributions and recurring charges](../outputs/comparison/09-return-and-cost-components.png)

For the primary graph in development, the positive gross arithmetic contribution is insufficient to cover trading and borrowing charges. In validation its gross contribution is smaller still. This diagnosis is more informative than reporting a Sharpe statistic alone: the graph changes the relative allocation, but the observed gross signal does not finance the declared turnover cost.

Table 13. Borrow sensitivity: CAGR with trading fees fixed at 5 bps

| Annual borrow | Dev. baseline | Dev. graph | Val. baseline | Val. graph |
| --- | --- | --- | --- | --- |
| 0% | -2.49% | -3.77% | -5.25% | -4.69% |
| 2% | -3.10% | -4.37% | -5.83% | -5.27% |
| 5% | -4.01% | -5.25% | -6.69% | -6.13% |

The zero-borrow case retains transaction fees. It is a sensitivity scenario, not an assertion that every short can be financed for free. Likewise, a uniform 5% borrow rate does not represent security-specific availability or a stressed lending book. These tests describe the assumed ledger, not executable brokerage terms.

### 8.7. Interpreting diffusion through an interactive graph

Equation 20. Spectral gain applied to the unsmoothed residual

$$g_{\tau}(\lambda)=1-\exp(-\tau\lambda) \qquad (20)$$

Equation 20 follows directly from Equation 8: an eigenvector of L with eigenvalue lambda is multiplied by this factor in x minus its diffused value. The zero-eigenvalue component is removed. Changing tau changes the relative treatment of graph modes; the subsequent exposure projection and scaling remain separate operations.

![Figure 8. A historical graph and the resulting unconstrained scores](../outputs/comparison/10-graph-signal-snapshot.png)

The companion **Graph-Diffusion-Explorer.html** shows 120 monthly graph snapshots, with a rotatable 3D network, date slider and paired score bars. Horizontal node coordinates are a fixed arrangement of the six research groups for display. Lines on the zero plane show retained connections; height shows the graph score. Neither drawing coordinates nor rendered interpolation enter the trading algorithm.

A positive plotted graph score proposes a long direction before the constraints are applied. The final projected weight may have a different sign. This distinction helps connect the mathematical operator to the implementation without presenting raw scores as actual trades or interpreting an attractive network visual as evidence of financial value.
