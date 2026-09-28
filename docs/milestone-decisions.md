# Setbacks, decisions and resolutions

This is the project’s problem-solving record. Entries distinguish an observed failure from a design fork or an empirical limitation. No setback has been manufactured to create a success narrative. Milestones 1–3 are documented retrospectively from their retained code, tests and results; Milestones 4 and 5 were documented during the work. Later milestones must add their own entries before completion.

## Milestone 1 — Foundations

### M1.1 — A favourable synthetic result cannot answer the financial question

**Type:** design limitation. The generator deliberately contains a mean-reverting component. A reversal signal can benefit from that assumption, so simulated performance is unsuitable evidence of real-market profitability.

**Decision and mitigation:** use the simulation to verify mechanics, label every synthetic result, and require a separate frozen historical experiment. The synthetic result was not promoted as a demonstrated trading edge.

**Evidence:** `market_neutral/data.py`, `notebooks/01-foundations.ipynb`, and the synthetic outputs under `outputs/`.

**Status:** mitigated for engineering verification; financial validation remained open and was addressed separately in Milestones 2 and 3. **Lesson:** a test fixture can support correctness while being economically favourable by construction.

### M1.2 — Dollar neutrality, beta neutrality and name caps are different constraints

**Type:** mathematical design fork, not an observed live-trading failure. Removing only the mean score would ensure dollar neutrality but would not generally remove estimated market exposure. Clipping each weight independently could then break either linear constraint.

**Decision and mitigation:** project the score away from the constant and beta directions with least squares, then scale the whole vector uniformly to enforce gross and name ceilings. A deficient exposure rank, such as identical betas, is handled by the least-squares solution rather than an inverse of a singular normal matrix. As Golub and Van Loan (2013) explain in *Matrix Computations*, rank-aware least-squares methods provide the relevant numerical framework.

**Evidence:** `market_neutral/portfolio.py` and the projection/cap checks in `tests/test_research.py`.

**Status:** resolved for the declared constraints; realised future beta and other factor exposures remain unconstrained. **Lesson:** feasibility of an estimated constraint is not a guarantee about future risk.

### M1.3 — Timing and cost conventions could otherwise produce misleading backtests

**Type:** implementation design risks. Same-close signal execution, ignoring drift-induced trades, or dropping entry/exit fees would make comparisons depend on accounting choices rather than the intended rule.

**Decision and mitigation:** decide at close t, execute at t+1 and first earn the new-position return at t+2. Mark existing notionals before rebalancing, solve post-cost NAV consistently, charge calendar-day short borrow and liquidate at phase boundaries. Hand calculations and future-observation perturbations check the resulting behaviour.

**Evidence:** `market_neutral/backtest.py`, `tests/test_research.py`; the historical phase isolation in `market_neutral/historical.py` carries these decisions forward.

**Status:** resolved for the declared notional ledger; raw fills, market impact and a full corporate-action cash ledger remain outside scope. **Lesson:** execution chronology and cost units need to be explicit before interpreting a strategy return.

### M1.4 — The environment could not open a Jupyter kernel socket

**Type:** observed execution-environment failure. Kernel socket creation was unavailable in the build environment.

**Decision and mitigation:** execute trusted notebook cells sequentially in one IPython process and capture text, tables and rich outputs. Preserve execution records and provide normal local Jupyter/VS Code instructions.

**Evidence:** `scripts/execute_notebook.py` and the notebook execution records in `validation/`.

**Status:** notebook cell logic and outputs executed; local VS Code kernel connectivity remains a local environment check. **Lesson:** distinguish inability to start one execution mechanism from failure of the research calculation itself.

## Milestone 2 — Historical baseline

### M2.1 — Accessible historical prices did not provide a point-in-time investable universe

**Type:** data fork and unresolved limitation. The selected 24-stock basket contains surviving companies and does not include historical constituents, all delistings or security-level borrow availability. As Shumway (1997) discusses in *The Delisting Bias in CRSP Data*, omissions around delisting outcomes matter for historical inference; complete histories for survivors cannot repair that omission.

**Decision and mitigation:** explicitly call the study exploratory and conditional on the fixed survivor basket. Preserve adjustments and event records, reject missing/misaligned prices, and avoid a market-wide alpha claim. Stronger data are a separate requirement, not something that can be inferred from a clean CSV.

**Evidence:** `protocol/historical-v1.json`, `data/download-manifest.json`, `outputs/historical/data-audit.csv` and `paper/manuscript.md`, Section 2.

**Status:** mitigated through scope and audit; survivorship, historical adjustment provenance and borrow realism remain unresolved. **Lesson:** data cleanliness and sample validity are separate questions.

### M2.2 — A fresh download may not reproduce the same historical vintage

**Type:** reproducibility fork. The provider can revise adjusted history, and responses also contain current quote metadata unrelated to the requested historical study.

**Decision and mitigation:** retain only requested historical bars and in-range action records; preserve exact request URLs and hashes; keep the original snapshot for offline replay. Restrict acquisition to dates before 2020. Reject hash changes rather than silently replacing the research input.

**Evidence:** `parse_chart`, `fetch_dataset` and `assemble_dataset` in `market_neutral/historical.py`; `tests/test_historical.py`; the download manifest.

**Status:** exact private-snapshot replay supported. Redistribution terms and durable snapshot availability for the future public repository remain to be resolved. **Lesson:** reproducing an observation vintage is stricter than rerunning a query.

### M2.3 — The baseline lost money after costs

**Type:** observed empirical setback. At 5 bps and 2% annual short borrow, CAGR was −3.10% in development and −5.83% in validation. Even zero trading fees left validation negative when borrowing costs remained.

**Decision and mitigation:** retain all four declared fee scenarios and examine the cost/exposure ledger. Do not replace stocks, dates or costs to rescue the finding. Proceed to the already planned graph comparison under the same observations and accounting rules.

**Evidence:** `outputs/historical/baseline-summary.csv`, phase ledgers and `notebooks/02-historical-baseline.ipynb`.

**Status:** profitability was not fixed. The result establishes a limitation of the tested baseline. **Lesson:** passing neutrality and accounting checks does not establish a viable economic signal.

## Milestone 3 — Graph comparison

### M3.1 — The same gross ceiling did not give the two strategies the same actual gross

**Type:** comparison-design fork. Uniform name-cap scaling can reduce baseline and graph exposure by different amounts.

**Decision and mitigation:** include a predeclared matched-gross control that reduces both decision portfolios to their smaller original gross before the execution delay. This preserves linear constraints and never increases leverage. Keep the original comparison alongside it.

**Evidence:** `protocol/graph-comparison-v1.json`, `match_gross_exposure` in `market_neutral/comparison.py`, and matched-gross rows in `outputs/comparison/comparison-summary.csv`.

**Status:** exposure-level confounding reduced, not all risk differences removed. The validation CAGR improvement shrank from about 0.55 to 0.22 percentage points. **Lesson:** identical limits do not imply comparable realised utilisation.

### M3.2 — Ordinary independent-observation uncertainty would ignore serial dependence

**Type:** inference-design fork. Portfolio differences can be serially dependent, and comparing two separate unpaired return summaries would ignore their common dates.

**Decision and mitigation:** form daily graph-minus-baseline differences; use the stationary bootstrap introduced by Politis and Romano (1994) and a Bartlett-weighted HAC cross-check following Newey and West (1987). Verify the bootstrap against the finite-sample variance relationship in Nordman (2009), and independently check the HAC quadratic form. Report all declared block lengths.

**Evidence:** `market_neutral/inference.py`, `tests/test_comparison.py` and `outputs/comparison/paired-uncertainty.csv`.

**Status:** conditional paired uncertainty reported; weak-dependence/stationarity assumptions, sample selection and model-search bias remain. **Lesson:** a statistically careful interval can still have a limited scientific interpretation.

### M3.3 — Graph diffusion did not establish a reliable advantage

**Type:** observed empirical setback. The primary graph candidate lost 4.37% annualised in development and 5.27% in validation. Development worsened relative to the baseline. The annualised arithmetic validation difference was +0.57 percentage points, with the primary bootstrap interval spanning −1.16 to +2.37.

**Decision and mitigation:** retain every one of the 44 declared cases, keep diffusion time one as the primary candidate, and state that no reliable advantage was demonstrated. Continue to topology as a separate descriptor study, not as a retrospectively tuned profitability fix.

**Evidence:** `outputs/comparison/experiment-register.json`, `comparison-summary.csv`, `paired-uncertainty.csv` and `notebooks/03-graph-comparison.ipynb`.

**Status:** economic performance remains unresolved. **Lesson:** a smaller validation loss and an appealing network visual are insufficient grounds for a positive trading claim.

## Milestone 4 — Persistent-homology features

### M4.1 — A sparse trading graph is not the required correlation metric space

**Type:** mathematical design fork. Reusing the positive-threshold adjacency matrix would change the geometry and discard negative relationships. Counting graph cycles without triangle fillings would also confuse graph topology with Rips H1.

**Decision and mitigation:** calculate complete correlation distances from common trailing observations. Declare the edge-threshold convention and use the full Vietoris–Rips filtration over F₂. Check a square, a triangle and a line with analytically known outcomes. Mantegna (1999) supplies the financial distance context, while Bauer (2021) describes the persistence algorithm.

**Evidence:** `protocol/topology-features-v1.json`, `correlation_distance` and `persistence` in `market_neutral/topology.py`, and `tests/test_topology.py`.

**Status:** resolved for the declared construction; it remains a different point-cloud design from Gidea and Katz (2018). **Lesson:** a familiar graph is not interchangeable with the object assumed by a topological method.

### M4.2 — Infinite and omitted zero-length intervals require explicit conventions

**Type:** boundary-handling fork confirmed by duplicate-point checks. A full finite cloud has one essential H0 bar. Arbitrarily capping its infinite death would contaminate averages. Ripser omits zero-length bars, which can affect an H0 mean if duplicate points are present.

**Decision and mitigation:** exclude exactly one essential H0 interval, reject infinite H1, restore omitted zero H0 mergers, and keep empty-H1 sums/maxima at zero. Do not fit a persistence cut-off. Independently compare H0 mergers with a minimum spanning tree.

**Evidence:** the essential and zero-merge columns in `outputs/topology/features.csv`; duplicate-point and MST checks in `tests/test_topology.py`.

**Status:** resolved and tested; the historical data contain no zero H0 mergers. **Lesson:** implementation defaults must be reconciled with the mathematical definition before aggregation.

### M4.3 — H0 mostly overlaps simpler information, and one fitted relation transfers poorly

**Type:** observed empirical limitation. H0 mean has Spearman correlation −0.935/−0.968 with mean correlation in development/validation. The three-control OLS approximation of H0 maximum has development R² 0.810 but validation R² −0.195.

**Decision and mitigation:** retain simple controls, distinguish a ranking association from a fitted level relationship, and report the negative transferred R². Fit centring/scaling/coefficients on development only; do not refit validation to improve the result. The prescribed linear model is only one redundancy diagnostic, so poor fit does not prove new information.

**Evidence:** `outputs/topology/control-correlations.csv`, `control-model-scores.csv`, `control-models.json` and dated predictions/residuals.

**Status:** descriptor computation verified; incremental usefulness and relation stability remain unresolved. **Lesson:** mathematical sophistication does not establish additional explanatory or economic value.

### M4.4 — H1 is less redundant but sensitive to the estimation horizon

**Type:** observed empirical limitation. Development rank correlation for H1 maximum between 252 and 126 sessions is only 0.082. This remains true even though all 480 declared monthly diagram-bound checks pass.

**Decision and mitigation:** retain every 63/126/252-session comparison and explain the distinction between a diagram perturbation bound and empirical feature invariance. As Chazal et al. (2014) explain in *Persistence stability for geometric complexes*, metric perturbations control diagram changes; that theorem does not guarantee stable financial regimes or stable rankings across windows. Keep 126 sessions primary and introduce no trading overlay at this milestone.

**Evidence:** `outputs/topology/window-sensitivity.csv`, `diagram-stability.csv`, Figure 11 and the frozen protocol.

**Status:** numerical bound verified; a defensible regime rule remains open. **Lesson:** passing a mathematical bound cannot substitute for testing the stability actually required by the proposed use.

### M4.5 — One chart write produced an empty PNG

**Type:** observed artifact failure. Visual inspection failed because the initial control-correlation PNG was zero bytes. No conclusion about the underlying numeric calculation follows from that write failure.

**Decision and mitigation:** render each chart into an in-memory buffer, verify the complete PNG before writing, and atomically replace the visible file. Regenerate the charts and inspect the repaired figures. Retain a final integrity check for every delivered PNG.

**Evidence:** `_save_figure` in `market_neutral/topology_plots.py` and `validation/milestone-4-artifacts.json`.

**Status:** repaired; regenerated figures are valid and inspected. **Lesson:** successful numerical execution is not sufficient evidence that every output artifact was written correctly.

## Milestone 5 — Final evaluation

### M5.1 — The topology diagnostics did not justify a new trading rule

**Type:** pre-test design fork. H0 substantially overlapped ordinary correlation, while H1 was sensitive to the estimation horizon. No completed analysis established a defensible signal direction, threshold or exposure rule.

**Decision and mitigation:** freeze the final comparison as the existing graph candidate against the baseline. Transfer all four topology descriptors and the development-only control models as diagnostics, with no new trading overlay. The protocol records that choice before the reserved observations are acquired.

**Evidence:** `protocol/final-evaluation-v1.json`, its timestamped hash lock, and the unchanged control-model hash in `outputs/final/run-manifest.json`.

**Status:** design fork resolved; topology's trading usefulness remains unestablished. **Lesson:** completing a sophisticated feature calculation does not oblige the researcher to turn it into a trade.

### M5.2 — A new adjusted-price vintage could invalidate the warm-up comparison

**Type:** data-vintage risk with small observed revisions. The maximum overlapping 2019 daily-return change was approximately 1.154×10⁻⁶, below the predeclared 10⁻⁵ tolerance. Comparing price levels alone could misinterpret a constant adjustment factor.

**Decision and mitigation:** acquire a separate coherent 2018–2025 price vintage, compare the 252 overlapping returns, require exact calendars and positive complete observations, and retain the old cache unchanged. Do not splice differently adjusted histories. Preserve both input hashes and a snapshot guard for subsequent replay; that guard is distinct from the pre-acquisition design lock.

**Evidence:** `market_neutral/final_data.py`, `outputs/final/data-audit.csv`, `data/final-download-manifest.json`, `data/final-snapshot.lock.json` and the scale-invariance/revision-rejection tests.

**Status:** the acquired vintage passed the declared audit. Point-in-time adjustments, survivor selection and future provider revisions remain limitations. **Lesson:** consistent return history and reproducible input identity need separate checks.

### M5.3 — Relative improvement could be confused with profitability or several independent claims

**Type:** inference-design fork. A strategy can lose less than its comparator while remaining unprofitable. Inspecting several confidence intervals without defining their family can also overstate the evidence.

**Decision and mitigation:** specify baseline mean, graph mean and their paired difference as the fixed three-mean family. Use the same stationary-bootstrap draws for all three, report pointwise and Bonferroni-adjusted intervals, and retain all block lengths plus HAC. As Lehmann and Romano (2005) explain in *Testing Statistical Hypotheses*, family-wise inference distinguishes a joint error probability from individual error probabilities. The allocation is conditional on approximate marginal interval coverage; it does not correct the whole research history.

**Evidence:** `market_neutral/final_inference.py`, `outputs/final/mean-inference.csv`, the paired-resampling and error-budget tests, and manuscript Equations 29–30.

**Status:** comparisons and error allocation are explicit. Dependence assumptions, changing regimes and retrospective sample selection remain. **Lesson:** identify both the estimand and the claim family before interpreting an interval.

### M5.4 — The reserved test did not support the proposed trading advantage

**Type:** observed empirical setback. Default-cost CAGR was −5.57% for the baseline and −4.80% for the primary graph. The arithmetic paired improvement was +0.73 percentage points, with an adjusted interval spanning −2.14 to +3.85. Both primary strategies lost money in every test calendar year; none of the four necessary evidence conditions was met.

**Decision and mitigation:** retain all 22 cases, every year, the matched-gross comparison and the gross/cost decomposition. Do not promote diffusion time 0.5, drop difficult years or replace the default fee with zero because those alternatives look better. Describe the economic hypothesis as unsupported under the frozen design.

**Evidence:** `outputs/final/final-summary.csv`, `mean-inference.csv`, `calendar-year-results.csv`, `evidence-gate.json` and `notebooks/05-final-evaluation.ipynb`.

**Status:** profitability was not fixed; the negative result is the research finding. The 2020–2025 period is now permanently observed. **Lesson:** an unsuccessful economic hypothesis can still produce a rigorous, reproducible research project, but it cannot support a profitable-alpha claim.

### M5.5 — Frozen topology relationships again failed to transfer uniformly

**Type:** observed empirical limitation. The primary-window H1-total and H1-maximum control models produced final-test R² of −0.217 and −0.088. Their explanatory relationships did not carry over reliably, and H1 rankings remained window-sensitive.

**Decision and mitigation:** retain the original development means, scales and coefficients. Report every window and feature; do not refit on the final observations or interpret unexplained residuals as profitable information. All 288 monthly diagram-bound checks passed, which verifies a different property from fitted-model transfer.

**Evidence:** `outputs/final/topology/control-model-scores.csv`, `window-sensitivity.csv`, `diagram-stability.csv` and the frozen model hash.

**Status:** computation and the bound checks pass; stable interpretation and economic usefulness remain unestablished. **Lesson:** a numerical theorem, a descriptive model and a financial hypothesis have distinct validation requirements.

### M5.6 — A completed scenario had an empty saved ledger

**Type:** observed artifact failure. The first run's primary-graph 10 bps sensitivity ledger was zero bytes even though its in-memory calculation and summary completed. The original manifest also recorded the empty-file hash. The exact write failure was not established.

**Decision and mitigation:** preserve that initial manifest and a repair record; serialize tables to memory, verify the temporary bytes, replace the file atomically, then verify the saved bytes. Replay the unchanged experiment. Require every unaffected numerical-output hash to match the first run, check the repaired ledger against its original summary, and validate every final ledger rather than accepting a file's existence or hash alone.

**Evidence:** `market_neutral/final_io.py`, `validation/final-initial-run-manifest.json`, `validation/final-artifact-repair.json`, the replay assertion in the fifth notebook and `validation/milestone-5-artifacts.json`.

**Status:** repaired and verified. All 47 unaffected numerical outputs reproduced exactly, the repaired ledger reconciles with its unchanged summary, and all 22 saved ledgers pass the content/accounting checks. **Lesson:** a hash can faithfully identify a broken artifact. Reproducibility needs content and accounting checks too.

### M5.7 — Reusing a visual layout retained stale slider entries

**Type:** observed interactive-configuration failure. The first notebook execution found 72 final-period frames but 120 slider entries. Updating the earlier plot layout merged its old array entries instead of replacing the complete slider.

**Decision and mitigation:** replace the slider array explicitly, then require each slider label and animation target to match exactly one final-period frame. Keep the fixed axes and verify all displayed landscape samples against the interval definition. Repeat the notebook after the repair.

**Evidence:** `market_neutral/final_plots.py`, the fifth notebook's frame/slider assertion and `scripts/verify_milestone_5.py`.

**Status:** the stale-control defect is repaired and configuration checks are retained. Actual browser interaction remains a local environment check. **Lesson:** reusing a layout requires validating its controls as well as replacing the plotted data.

## Milestone 6 — Final paper assembly and public presentation

The paper-assembly part of this milestone is complete; GitHub publication and the CV/LinkedIn release remain separate work.

### M6.1 — The attached examples use several different document formats

**Type:** presentation-design fork. The SPX paper uses A4 portrait pages and an Arial-compatible body, while the cooler report and some other assignments use a different paper size or column structure. The examples establish a preferred visual and explanatory style, not a required sequence for this trading study.

**Decision and mitigation:** adopt one A4 portrait format throughout, an Arial-compatible 12-point body, smaller centred captions below all figures, tables and equations, and numbered headings. Retain the project's own methods/results sequence, add a dedicated discussion and conclusion, and place reproduction details in an appendix. Preserve Harvard author–date prose and an alphabetical reference list containing references only.

**Evidence:** the attached style examples; `paper/assemble_final_paper.py`; `paper/final/Market-Neutral-Trading-Algorithm-Final-Paper.tex` and the final PDF.

**Status:** the layout specification is implemented. **Lesson:** a reference document's style can be retained without copying a structure or page size that does not suit the new research.

### M6.2 — Initial typesetting checks exposed overflow warnings and sparse continuation pages

**Type:** observed document-build and pagination issues. The first layout produced sparse continuation pages in the contents and symbol registers, a split abbreviation table and longtable caption-box warnings. The first font setup also failed to select the bold face. These were presentation defects, not changes in the scientific calculations.

**Decision and mitigation:** flow the front-matter registers without unnecessary page breaks, reduce rule padding in the symbol/abbreviation tables, keep ordinary tables together as floats, split long equations over aligned lines and explicitly select the font faces. Centre caption boxes at full text width. Escape URL characters correctly, preserve balanced DOI parentheses and retain the original code lines while allowing visual wrapping. The register audit also caught a duplicated counter increment after the front-matter tables; removing that increment restored the consecutive numbering. Recompile until the document has no missing-glyph or overfull-box warnings, then inspect rendered pages and check caption positions, reference links and register page references. Truncated intermediate page images were regenerated and their saved bytes verified before visual review.

**Evidence:** `paper/assemble_final_paper.py` and `validation/final-paper-validation.json`.

**Status:** repaired and checked in the delivered PDF. **Lesson:** successful content assembly does not ensure a readable final document; pagination, glyphs and caption placement need separate verification.

### M6.3 — Author review favoured clearer section boundaries

**Type:** author-directed layout revision. The first assembled version allowed chapters and front-matter registers to share pages to reduce unused space. The author subsequently requested a separate page for each main chapter and each “List of…” heading, and placement of the appendix after the references.

**Decision and mitigation:** introduce page breaks at those boundaries, move the appendix after the Harvard reference list in both the editable manuscript and the PDF, and regenerate the contents, caption registers and bookmarks. Change the displayed title-page date to March 2026. The source access dates and experiment timestamps remain their recorded values.

**Layout verification:** the first rebuild exposed three chapter-ending continuations containing only two lines each. Modestly reducing two figure widths and the setback table's cell padding retained those lines on the preceding pages without changing the text, numerical results or body font size. Compact contents spacing also removed a short front-matter continuation. All chapter and list-section page breaks remain explicit.

**Evidence:** `paper/assemble_final_paper.py`, `paper/update_manuscript.py`, `scripts/verify_final_paper.py` and the revised PDF.

**Status:** the requested layout is implemented and its section starts and ordering are checked. **Lesson:** a deliberate topic break can improve navigation even when it increases the page count; the author's revised preference controls that trade-off.

## Subsequent milestone requirement

For each new milestone, record the actual issue or fork, what the evidence showed, the decision taken, the implementation or analysis used to respond, and what remains unresolved. An unsuccessful hypothesis should stay unsuccessful in the record unless a new, separately specified experiment supports a different conclusion.

## References

Bauer, U. (2021) ‘Ripser: efficient computation of Vietoris–Rips persistence barcodes’, *Journal of Applied and Computational Topology*, 5(3), pp. 391–423. doi: [10.1007/s41468-021-00071-5](https://doi.org/10.1007/s41468-021-00071-5).

Chazal, F., de Silva, V. and Oudot, S. (2014) ‘Persistence stability for geometric complexes’, *Geometriae Dedicata*, 173(1), pp. 193–214. doi: [10.1007/s10711-013-9937-z](https://doi.org/10.1007/s10711-013-9937-z).

Edelsbrunner, H., Letscher, D. and Zomorodian, A. (2002) ‘Topological Persistence and Simplification’, *Discrete and Computational Geometry*, 28, pp. 511–533. doi: [10.1007/s00454-002-2885-2](https://doi.org/10.1007/s00454-002-2885-2).

Gidea, M. and Katz, Y. (2018) ‘Topological data analysis of financial time series: Landscapes of crashes’, *Physica A: Statistical Mechanics and its Applications*, 491, pp. 820–834. doi: [10.1016/j.physa.2017.09.028](https://doi.org/10.1016/j.physa.2017.09.028).

Golub, G.H. and Van Loan, C.F. (2013) *Matrix Computations*. 4th edn. Johns Hopkins University Press. doi: [10.56021/9781421407944](https://doi.org/10.56021/9781421407944).

Lehmann, E.L. and Romano, J.P. (2005) *Testing Statistical Hypotheses*. 3rd edn. Springer Texts in Statistics. Springer. doi: [10.1007/0-387-27605-X](https://doi.org/10.1007/0-387-27605-X).

Mantegna, R.N. (1999) ‘Hierarchical structure in financial markets’, *The European Physical Journal B*, 11, pp. 193–197. doi: [10.1007/s100510050929](https://doi.org/10.1007/s100510050929).

Newey, W.K. and West, K.D. (1987) ‘A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix’, *Econometrica*, 55(3), pp. 703–708. doi: [10.2307/1913610](https://doi.org/10.2307/1913610).

Nordman, D.J. (2009) ‘A note on the stationary bootstrap's variance’, *The Annals of Statistics*, 37(1), pp. 359–370. doi: [10.1214/07-AOS567](https://doi.org/10.1214/07-AOS567).

Politis, D.N. and Romano, J.P. (1994) ‘The Stationary Bootstrap’, *Journal of the American Statistical Association*, 89(428), pp. 1303–1313. doi: [10.1080/01621459.1994.10476870](https://doi.org/10.1080/01621459.1994.10476870).

Shumway, T. (1997) ‘The Delisting Bias in CRSP Data’, *The Journal of Finance*, 52(1), pp. 327–340. doi: [10.1111/j.1540-6261.1997.tb03818.x](https://doi.org/10.1111/j.1540-6261.1997.tb03818.x).
