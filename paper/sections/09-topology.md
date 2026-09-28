## 9. Persistent homology and simpler controls

As Edelsbrunner et al. (2002) explain in *Topological Persistence and Simplification*, a filtration records structure across scales through the birth and death of homological features. Here H0 describes component mergers and H1 describes cycles before they become boundaries of filled triangles. A triangle in the correlation network does not, by itself, constitute a persistent H1 feature. These objects describe the geometry of the observations; a financial interpretation requires a separate empirical argument.

Gidea and Katz (2018), in *Topological data analysis of financial time series: Landscapes of crashes*, examine sliding-window point clouds of market-index returns. Their construction motivates asking whether topological summaries can describe financial structure. The present project instead treats the 24 assets as the points and constructs their distances from trailing return correlations. Consequently, this is not a replication of their experiment, and their findings cannot be transferred as evidence that this strategy forecasts crashes or earns positive returns.

### 9.1. Frozen feature design and causal geometry

Table 14. Topology protocol recorded before the first historical feature extraction

| Design choice | Declared implementation |
| --- | --- |
| Points | The same 24 assets; SPY is a volatility control, not a point |
| Observations | Trailing daily simple adjusted-price returns through close t |
| Windows | 126 sessions primary; 63 and 252 sessions retained as sensitivities |
| Geometry | Complete correlation distances, including negatively correlated pairs |
| Filtration | Vietoris–Rips; edge threshold ε; coefficients in F₂; H0 and H1 |
| Features | Mean and maximum finite H0 persistence; total and maximum finite H1 persistence |
| Controls | Same-window mean correlation, mean annualised stock volatility and annualised SPY volatility |
| Fitting | Descriptive OLS coefficients and control standardisation fitted on development only |
| Comparison dates | 2,516 common dates: 1,762 development and 754 validation |
| Trading interpretation | No return target, threshold fitting, strategy overlay or new backtest |
| Holdout at Milestone 4 | 2020–2025 was unavailable; release and final evaluation appear in Section 10 |

The local record is `protocol/topology-features-v1.json`, with SHA-256 `2b2d975392129a88ea10b5955dd9405be46d49ba2860f7d0e9872b0e76c926d1`. It was locked before topology extraction, after the baseline and graph outcomes were already known. It is not external preregistration. No primary feature or window is selected after comparing the results.

As Mantegna (1999) explains in *Hierarchical structure in financial markets*, return correlations can be transformed into distances for studying relationships between assets. Equation 21 uses that transformation. For the complete common observation window, it also follows directly from the Euclidean distance between centred, unit-length return vectors.

Equation 21. Correlation distance as a Euclidean chord

$$u_{i,t}=\frac{r_{i,t-W_{\mathrm{len}}+1:t}-\bar r_{i,t}\mathbf{1}}{\left\|r_{i,t-W_{\mathrm{len}}+1:t}-\bar r_{i,t}\mathbf{1}\right\|_2},\qquad d_{ij,t}=\sqrt{2(1-\rho_{ij,t})}=\|u_{i,t}-u_{j,t}\|_2 \qquad (21)$$

Where: W_len is the number of return observations and the mean is taken over that window. Constant series are rejected because the normalisation is undefined. Missing-data handling remains the exact-calendar rejection rule. The distance lies between zero and two; identical standardised histories can give zero distance between labelled assets. Neither thresholding the positive trading graph nor discarding negative correlations is part of this geometry.

Listing 9. Constructing the complete causal correlation geometry

Source: `market_neutral/topology.py`, `correlation_distance`; selected executable lines.

<!-- CODE:correlation_distance:    centered =:    return corr, distance -->

Features dated t include the return ending at t. They are available at that close and cannot earn an earlier return. Any future trading overlay would have to preserve the existing t+1 execution and t+2 first new-position return. A future-perturbation check replaces all later observations and confirms that earlier features are unchanged.

### 9.2. Filtration, intervals and explicit boundary handling

As Bauer (2021) describes in *Ripser: efficient computation of Vietoris–Rips persistence barcodes*, efficient persistence calculations can operate on Rips filtrations. Tralie et al. (2018), in *Ripser.py: A lean persistent homology library for Python*, provide the Python interface used here. The implementation fixes Ripser.py 0.6.14, homology coefficients modulo two and the full filtration through dimension one.

Equation 22. Edge-threshold Vietoris–Rips complex

$$\mathrm{VR}_{\varepsilon}(D_t)=\{\sigma\subseteq\{1,\ldots,n\}:\max_{i,j\in\sigma}d_{ij,t}\leq\varepsilon\} \qquad (22)$$

Equation 22 includes a simplex whenever all its pairwise distances are at most ε. In particular, a three-vertex clique includes its filled triangle. The scale is an edge distance; replacing it with a ball-radius convention would change the numerical scale and is not done here.

In a full filtration on this finite cloud, one H0 interval persists indefinitely and all H1 intervals eventually die. The implementation excludes that one essential H0 interval from finite summaries and verifies that no essential H1 interval remains. It does not substitute an arbitrary finite value for infinity. Ripser omits zero-length intervals, so omitted zero-distance H0 mergers are restored as zero intervals when needed to retain the n−1 finite merger convention. This duplicate-point case is covered by a separate check; it does not occur in the historical extraction.

Equation 23. Four predeclared persistence summaries

$$\ell_a=d_a-b_a,\qquad f_{0,\mathrm{mean}}=\frac{1}{n-1}\sum_{a\in\mathcal D_0^{\mathrm{fin}}}\ell_a,\quad f_{0,\max}=\max_{a\in\mathcal D_0^{\mathrm{fin}}}\ell_a,\quad f_{1,\mathrm{total}}=\sum_{a\in\mathcal D_1}\ell_a,\quad f_{1,\max}=\max_{a\in\mathcal D_1}\ell_a \qquad (23)$$

Where: b_a and d_a are birth and death thresholds, and ℓ_a is their difference. Empty H1 diagrams have total and maximum equal to zero. Every positive lifetime emitted by the engine is retained; there is no fitted significance or persistence cut-off. The features have distance units. The H0 merger distances agree with minimum spanning tree edge weights: both connect previously separate components in increasing distance order. The implementation is independently checked against SciPy's spanning-tree calculation on a known finite cloud.

Listing 10. Full persistence calculation and essential-interval checks

Source: `market_neutral/topology.py`, `persistence`; selected executable lines. The complete function also validates the input and restores zero-distance H0 mergers.

<!-- CODE:persistence:    diagrams =:    h0 = h0[~essential].astype(float) -->

### 9.3. Simpler controls and an honest redundancy check

The controls are the mean of the off-diagonal correlations, the mean sample standard deviation of stock returns multiplied by √252, and the sample standard deviation of SPY returns multiplied by √252. Each uses the same window as the corresponding topological feature. Their purpose is to test whether an elaborate descriptor mostly reproduces a simpler observable.

Within-phase Spearman correlations compare rankings. The separate OLS calculation approximates each feature with the three controls. As Golub and Van Loan (2013) explain in *Matrix Computations*, least-squares problems can be solved without explicitly inverting the normal-equations matrix; the implementation uses a least-squares solver and rejects a deficient design rank. The choice of these three controls is a project diagnostic, not a specification derived from that book.

Equation 24. Development-only standardisation and control approximation

$$z_{j,t}=\frac{c_{j,t}-\bar c_{j,\mathrm{dev}}}{s_{j,\mathrm{dev}}},\qquad \widehat\theta=\arg\min_{\theta}\sum_{t\in\mathrm{dev}}\big(f_t-[1,z_t^\top]\theta\big)^2,\qquad \widehat f_t=[1,z_t^\top]\widehat\theta \qquad (24)$$

Where: c_j is a control, s_j is its sample standard deviation and f is one of the four descriptors. Validation never enters centring, scaling or coefficient fitting. The outputs include coefficients and dated predictions/residuals for every window and feature. There are twelve fitted descriptive models, not twelve trading strategies.

Listing 11. Fitting controls only on the development segment

Source: `market_neutral/topology.py`, `fit_control_model`; selected executable lines. The caller passes development observations only.

<!-- CODE:fit_control_model:    x =:    coefficients, _, rank, _ = -->

Equation 25. Phase-specific descriptive approximation score

$$R^2_{\mathcal P}=1-\frac{\sum_{t\in\mathcal P}(f_t-\widehat f_t)^2}{\sum_{t\in\mathcal P}(f_t-\bar f_{\mathcal P})^2} \qquad (25)$$

The phase mean in Equation 25 is used only to score the approximation, not to fit it. Negative validation R² is retained: it means that the transferred model has larger squared error than the constant validation-mean benchmark. A low R² does not establish novelty, predictability or a trading benefit; it can also reflect a limited functional form, estimation noise or distribution change. Overlapping windows induce dependence, so no independent-observation p-values are attached to these diagnostics.

<!-- GENERATED_RESULTS -->

![Figure 9. Primary-window topology descriptors and simpler market measures](../outputs/topology/09-topology-features.png)

![Figure 10. Spearman dependence between topology features and simple controls](../outputs/topology/10-control-redundancy.png)

H0 mean persistence largely follows the ordinary correlation level. The OLS approximation for H0 maximum fits development reasonably well but transfers poorly, with validation R² below zero. This is a concrete setback for treating the same fitted relation as stable across phases. It is preserved in the record; the validation segment is not used to re-estimate the model and produce a more attractive score.

H1 retains variation not captured by the declared linear control model. That observation is insufficient to promote it into a trading signal. In particular, the window comparison below shows that the identity and duration of cycles change considerably with the estimation horizon. None of the three windows is selected as a winner after this analysis.

### 9.4. Window sensitivity and diagram stability

As Chazal et al. (2014) explain in *Persistence stability for geometric complexes*, Rips persistence diagrams can be controlled by changes in the underlying metric geometry. For the same labelled assets, matching each asset to itself gives the specialisation in Equation 26. This is a bound on diagram changes, not a statement that every summary or financial relationship stays constant when the return window changes.

Equation 26. Same-label perturbation bound for Rips diagrams

$$d_B\big(\mathcal D_q(D),\mathcal D_q(D')\big)\leq\eta,\qquad\eta=\max_{i,j}|D_{ij}-D'_{ij}|,\quad q\in\{0,1\} \qquad (26)$$

Where: d_B is bottleneck distance, allowing intervals to match to the diagonal. The matching essential H0 intervals are omitted on both sides of the finite computation. The full finite complexes use the same edge-threshold convention. The numerical comparison permits 2×10⁻⁶ for the engine's finite precision; it does not relax the theoretical bound for a statistical reason.

All 480 declared checks satisfy the bound: 120 month-end dates, two alternative windows and two homology dimensions. The checks use real distances for each window and compare them with the primary 126-session matrix. They validate numerical consistency with the bound. Empirical feature stability is assessed separately by paired-date rank correlations.

![Figure 11. Feature sensitivity to the declared estimation windows](../outputs/topology/11-window-sensitivity.png)

H1 maximum persistence is particularly sensitive: its development rank correlation between 252 and 126 sessions is approximately 0.082. Passing the diagram bound therefore cannot be advertised as robust regime classification. Before a future overlay could be considered, a new protocol would need to state which feature and horizon it intends to use, why the decision is justified, and how dependence and model selection will be handled.

### 9.5. Dynamic three-dimensional explanation

As Bubenik (2015) explains in *Statistical topological data analysis using persistence landscapes*, intervals can be mapped to ordered tent functions. Equation 27 defines the landscape used in the interactive companion. The complete interval set supplies the numerical descriptors; the display shows only its first five ranks on a fixed grid from zero to two.

Equation 27. Persistence landscape from ordered interval tents

$$g_a(\varepsilon)=\max\{0,\min(\varepsilon-b_a,d_a-\varepsilon)\},\qquad\lambda_k(\varepsilon)=\operatorname{kth\ largest}_{a}\,g_a(\varepsilon) \qquad (27)$$

Where: k is a positive integer and unavailable ranks have value zero. Each height has distance units. The interpolation joining integer ranks in the 3D surface is a display choice; it does not define additional topological observations and is not a fitted financial surface.

Listing 12. Computing ordered landscape layers from the actual intervals

Source: `market_neutral/topology.py`, `landscape`; selected executable lines.

<!-- CODE:landscape:    x =:    return out -->

![Figure 12. H1 landscape and birth–death diagram at the last validation month-end](../outputs/topology/12-persistence-landscape.png)

`outputs/topology/Persistence-Landscape-Explorer.html` contains 120 primary-window monthly frames, rotatable 3D layers, a paired birth–death diagram, date selection and playback. Axes remain fixed through playback and JavaScript is embedded for offline use. Structural checks verify frame counts, matching dates, layer values and control configuration. Live browser interaction is not claimed as tested in the build environment.

Ten new focused automated checks cover the square, triangle and line examples; an independent spanning-tree comparison; duplicate points; correlation-distance invariance; future-data isolation; analytic landscape tents; a perturbed-metric bound; control fitting; and invalid geometry. At the completion of this stage, 35 tests passed; the final evaluation expands the suite to 41. The extraction produces 7,548 dated window rows in approximately three seconds in the recorded environment; this timing excludes plots and diagram-distance checks and is not a hardware-independent performance claim.
