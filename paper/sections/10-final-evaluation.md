## 10. Final evaluation on the reserved 2020–2025 period

The final experiment evaluates the fixed primary graph strategy against the original baseline. It does not introduce a topology trading overlay. That decision was made before acquisition: the completed descriptor study showed substantial overlap with simple correlation for H0 and material window sensitivity for H1, without establishing a defensible trading direction or threshold. Retaining the simpler trading comparison is a research decision recorded in the final protocol, not a claim that topology can never be useful.

As White (2000) explains in *A Reality Check for Data Snooping*, searching across alternatives changes the interpretation of apparent success. Bailey et al. (2017), in *The probability of backtest overfitting*, also discuss the risk associated with repeated selection. The final protocol therefore fixes the comparison, finite scenario set, uncertainty procedure and evidence conditions before the reserved observations are acquired. Neither cited procedure is implemented as a retrospective correction for every decision made in this project.

### 10.1. Release, data audit and interpretation of “reserved”

The final protocol is `protocol/final-evaluation-v1.json`, SHA-256 `8fdee505de9ceaa8e4a2951deba29c1305eb12ee64d2d42467a978e2805c2acd`. Its lock precedes acquisition. The previous three protocols and the original observations are preserved, and the existing strategy, graph, portfolio, accounting, inference and topology calculation files are checked against their frozen source hashes.

Table 18. Final design and evidence conditions fixed before acquisition

| Item | Frozen decision |
| --- | --- |
| Primary comparison | Graph, τ = 1, against the baseline on 2020–2025 |
| Data and warm-up | Separate coherent adjusted-price vintage; 2019 returns with a 31 December 2018 anchor |
| Universe | Same 24 stocks and SPY; no stock/date substitution |
| Primary costs | 5 bps per dollar traded and 2% annual short borrow |
| Finite scenario set | 16 model/fee cases, four additional borrow cases and two matched-gross cases |
| Primary uncertainty | 10,000 paired stationary-bootstrap replicates; mean block length 10 |
| Inference family | Baseline mean, graph mean and graph-minus-baseline mean; Bonferroni adjustment for these three |
| Secondary checks | Block lengths 5/20, HAC with ten lags, matched-gross paired intervals and every calendar year |
| Necessary condition 1 | Primary graph CAGR is positive at default costs |
| Necessary condition 2 | Adjusted lower bound for the graph's arithmetic mean is positive |
| Necessary condition 3 | Adjusted lower bound for the graph-minus-baseline mean is positive |
| Necessary condition 4 | Matched-gross paired 95% lower bound is positive |
| Topology | Descriptors and development-fitted control relationships only; no new overlay |

The new Yahoo Finance (2026b) responses contain 1,761 aligned price observations per series from 31 December 2018 through 31 December 2025. There are 1,508 evaluation sessions, from 2 January 2020 to 31 December 2025. Every series exactly matches the observed SPY calendar; missing values, nonpositive reported volumes and adjusted-return moves above the predeclared 40% audit threshold are absent. The earlier Yahoo Finance (2026a) cache remains unchanged.

Adjusted-price levels can differ across retrievals. Comparing levels alone could mistake a constant adjustment factor for a meaningful return revision. Equation 28 instead checks the common 2019 return history before evaluation. The new calculation uses its own complete warm-up and test vintage; it does not splice a price from the old cache into a new adjusted series.

Equation 28. Overlapping-return vintage audit

$$\max_{t\in\mathcal O}\left|\left(\frac{P^{\mathrm{new}}_t}{P^{\mathrm{new}}_{t-1}}-1\right)-\left(\frac{P^{\mathrm{old}}_t}{P^{\mathrm{old}}_{t-1}}-1\right)\right|\leq 10^{-5} \qquad (28)$$

Where: O is the 252-return overlap in 2019. The tolerance is 0.1 basis points per daily return and was fixed before the download. The observed maximum across the 25 series is approximately 1.154×10⁻⁶, or 0.0115 basis points, within that tolerance. The final processed snapshot hash is `040f3199669d24009b848b5d1112321a70b7cb8084cb84fce6d6878a33abdcdd`. A retained snapshot guard prevents a later acquisition from silently becoming the same experiment. Its timestamp records the audited vintage for replay and is distinct from the earlier protocol lock.

Listing 13. Auditing return changes rather than adjusted-price level changes

Source: `market_neutral/final_data.py`, `overlap_audit`; selected executable lines. The complete function rejects mismatched dates and deviations above the frozen tolerance.

<!-- CODE:final_data.overlap_audit:    old =:    ratios = -->

“Reserved” describes the order of work inside this project. These are publicly known historical years, and the basket was selected retrospectively from surviving companies. As Shumway (1997) explains in *The Delisting Bias in CRSP Data*, omitted adverse outcomes can matter for historical inference. This project's broader survivor-selection limitation affects the final period too. A pre-acquisition hash does not transform the study into a prospective blind experiment or repair the absence of a point-in-time universe.

### 10.2. Primary performance and the accounting explanation

<!-- FINAL_TABLE: primary -->

Both strategies lose money at the default costs. The graph loses less over the full period, but its −4.80% CAGR is still negative. Its lower volatility and smaller drawdown are descriptive findings under the stated constraints and data; they do not establish a profitable or superior risk-adjusted policy. Estimated neutrality remains numerically satisfied, while realised market beta can differ from zero.

![Figure 13. Final-test capital, drawdown, annual returns and realised beta](../outputs/final/13-final-performance.png)

The zero-cash-rate no-trade line in Figure 13 is an accounting comparator consistent with the omitted cash-interest model. It is not a historical risk-free return series. The ledger starts flat with USD 100,000, uses the preceding close's decision for first execution, and includes entry fees and liquidation at the last test close. Calendar-year summaries do not reset the book or remove losses at year boundaries.

The primary graph's annualised arithmetic gross contribution is approximately +1.00%, compared with 5.18% trading drag and 0.64% borrow drag, leaving −4.81% net. The baseline has +0.37% gross contribution, 5.25% trading drag and 0.67% borrow drag, leaving −5.55% net. These components reconcile arithmetically under Equation 12. Their scaling is different from CAGR, and summing them should not be represented as a compounded-return decomposition.

### 10.3. Joint uncertainty for three explicit comparisons

Politis and Romano (1994), in *The Stationary Bootstrap*, provide the dependence-preserving resampling construction. Nordman (2009), in *A note on the stationary bootstrap's variance*, provides the algorithmic and finite-variance relationship used by the earlier numerical checks. The final calculation applies one index matrix to the paired daily returns so that each bootstrap replicate preserves their contemporaneous relationship.

Equation 29. Three predeclared daily comparisons

$$\xi_t=\begin{pmatrix}R^{B,\mathrm{net}}_t\\R^{G,\mathrm{net}}_t\\R^{G,\mathrm{net}}_t-R^{B,\mathrm{net}}_t\end{pmatrix},\qquad \widehat\mu_j=252\,\overline{\xi}_j,\quad j=1,2,3 \qquad (29)$$

The first two means compare with the zero-cash-rate no-trade reference; the third measures incremental arithmetic return. The stationary bootstrap uses 10,000 replicates, primary expected block length ten and fixed seeds. All declared block-length results and the Newey and West (1987) HAC cross-check are retained. No estimator is selected because it gives the preferred conclusion.

Listing 14. Applying identical resampling blocks to all paired comparisons

Source: `market_neutral/final_inference.py`, `fixed_family_intervals`; selected executable lines. The assertion checks the pairing identity within each replicate.

<!-- CODE:final_inference.fixed_family_intervals:        indices =:        np.testing.assert_allclose -->

As Lehmann and Romano (2005) explain in *Testing Statistical Hypotheses*, Chapter 9, considering several hypotheses requires distinguishing an individual error probability from a family-wise error probability. The present family has three predeclared means. Equation 30 states the union-bound argument used to allocate the error budget; it does not require independence between the three comparisons.

Equation 30. Bonferroni allocation for the fixed three-mean family

$$\Pr\!\left(\bigcup_{j=1}^{m_F}\{\mu_j\notin I_j\}\right)\leq\sum_{j=1}^{m_F}\Pr(\mu_j\notin I_j)\leq\alpha,\qquad m_F=3,\quad\alpha=0.05,\quad\Pr(\mu_j\in I_j)\geq1-\frac{\alpha}{m_F}=0.98333\ldots \qquad (30)$$

For the bootstrap, Equation 30 is an approximate-coverage design because each marginal interval is itself approximate. The percentile bounds use the 0.008333… and 0.991666… quantiles; the pointwise 95% intervals are also shown. Bonferroni controls only the stated family conditional on adequate marginal coverage. It does not correct survivorship, structural changes, data revisions or an unlimited history of model searches. HAC intervals share the same reporting levels but rely on their own asymptotic approximation.

<!-- FINAL_TABLE: inference -->

![Figure 14. Pointwise and family-adjusted intervals for the final arithmetic comparisons](../outputs/final/14-final-inference.png)

The graph-minus-baseline point estimate is +0.73 percentage points per year in arithmetic terms. Its adjusted interval spans −2.14 to +3.85 percentage points, so the sign of the incremental mean is unresolved by this procedure. It would be incorrect to replace this estimand with the +0.76-percentage-point CAGR difference or to describe either statistic as evidence of a positive absolute return.

The primary graph's adjusted mean interval remains below zero under the chosen bootstrap settings. The overall evidence decision nevertheless uses the four frozen necessary conditions in Table 18 rather than a favourable reinterpretation of individual intervals. None of those four conditions is met.

### 10.4. Exposure and cost controls retain the negative finding

<!-- FINAL_TABLE: matched -->

At matched gross, baseline and graph CAGR are approximately −4.94% and −4.69%. The arithmetic paired difference is +0.21 percentage points, with a pointwise 95% stationary-bootstrap interval from −1.97 to +2.44. Equal gross does not equal equal risk, but this control again reduces the observed performance difference without establishing a reliable improvement.

<!-- FINAL_TABLE: fees -->

<!-- FINAL_TABLE: borrow -->

The zero-trading-fee primary graph case has a small positive CAGR of approximately +0.25%, with borrow still charged. That scenario does not justify discarding the specified 5 bps fee: at default costs the same candidate loses 4.80% annually. Nor is diffusion time 0.5 promoted because it looks slightly better. Every sensitivity case remains a reported check of the original primary design.

![Figure 15. Final-test fee sensitivity and arithmetic cost decomposition](../outputs/final/15-final-costs.png)

<!-- FINAL_TABLE: annual -->

Both primary strategies have negative net returns in each of the six calendar years. The table is descriptive; annual observations are neither independent experiment replications nor a reason to drop a difficult year. Borrow availability, funding rebates, nonlinear impact and raw corporate-action cash flows remain outside the simplified ledger.

### 10.5. Topology transfer without refitting or a new trading rule

The final topology extraction retains four descriptors at all three windows: 4,524 rows on 1,508 common dates. The same development-fitted control means, scales and coefficients from Milestone 4 are applied unchanged. There is no fitting on the final period and no return target.

Listing 15. Transferring the saved development-only control model

Source: `market_neutral/final_evaluation.py`, `final_topology`; selected executable lines.

<!-- CODE:final_evaluation.final_topology:            model =:            fitted = -->

<!-- FINAL_TABLE: topology -->

The 126-session H1-total and H1-maximum control approximations give negative final-period R², −0.217 and −0.088. This does not establish profitable information in their residuals: the models can fail to transfer because of changing relationships, a limited linear specification or noise. H1-maximum rankings also remain sensitive to the window, with final-period correlations approximately 0.205 and 0.325 against the primary for the 63- and 252-session windows.

![Figure 16. Frozen control-model transfer and topology window sensitivity](../outputs/final/16-final-topology-transfer.png)

All 288 final monthly diagram-bound checks pass. As Chazal et al. (2014) explain in *Persistence stability for geometric complexes*, a metric stability relationship controls diagram changes; it does not imply financial usefulness or horizon-invariant descriptors. The distinction identified in Milestone 4 remains material here.

Following the landscape representation discussed by Bubenik (2015) in *Statistical topological data analysis using persistence landscapes*, the final companion contains 72 monthly 3D landscapes and paired diagrams. Its axes and first-five-layer display convention are fixed across frames. The file `outputs/final/topology/Final-Test-Landscape-Explorer.html` explains observed structure, not a trade recommendation. Numerical frame values and controls are checked; live browser interaction is not claimed as tested in the build environment.

### 10.6. Research conclusion

The fixed strategy comparison fails its predefined positive-evidence criterion. The implementation and mathematical checks are completed, but profitability and a reliable incremental graph advantage are not demonstrated in this survivor-basket study. Topology contributes a verified descriptive analysis with explicit redundancy and stability limitations. The reserved period is now observed and cannot be reused as a fresh test for subsequent model changes.
