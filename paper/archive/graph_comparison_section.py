"""Narrative, equations and source-linked excerpts for Milestone 3."""
import pandas as pd
from market_neutral.comparison import match_gross_exposure
from market_neutral.inference import stationary_indices, hac_mean_interval
from market_neutral.strategy import build_decisions


def add_graph_comparison(root, p, heading, table, equation, figure, listing, counts):
    out = root / 'outputs/comparison'
    all_results = pd.read_csv(out / 'comparison-summary.csv')
    uncertainty = pd.read_csv(out / 'paired-uncertainty.csv')
    primary = all_results[all_results.model.isin(['baseline', 'graph_tau_1']) & (all_results.trading_cost_bps == 5) & (all_results.annual_borrow_rate == .02)].set_index(['phase', 'model'])
    labels = {'baseline': 'Baseline', 'graph_tau_1': 'Graph, tau = 1'}

    heading('8. Historical graph comparison', True)
    p('Milestone 3 evaluates the graph rule in Equation 9 using exactly the acquired observations and accounting conventions from the historical baseline. The baseline outcome was known when this comparison began. The graph settings were inherited from the synthetic prototype, and a separate local protocol was hashed before the first historical graph run. Neither development nor validation is represented as a newly untouched dataset.')
    table('Predeclared comparison and sensitivity design', [
        ['Component', 'Fixed design'],
        ['Primary candidate', '126-session graph; five directed neighbours above 0.20; symmetric union; diffusion time one'],
        ['Trading-fee sensitivity', '0, 5, 10 and 20 bps; 2% annual borrow'],
        ['Diffusion-time sensitivity', '0.5, 1 and 2; every trading-fee combination retained'],
        ['Borrow sensitivity', '0%, 2% and 5%; baseline and primary graph at 5 bps'],
        ['Exposure control', 'Both primary targets scaled down to their common daily gross exposure; 5 bps and 2% borrow'],
        ['Uncertainty', 'Paired stationary bootstrap, 5,000 replicates; mean block lengths 5/10/20; HAC with 10 lags'],
        ['Experiment record', '44 distinct backtests completed; no replacement of the primary candidate'],
        ['Final holdout', '2020-2025 remains unacquired and unavailable']],[.28,.72])
    p('As White argues in <i>A Reality Check for Data Snooping</i> (2000), searching across alternatives can produce misleading apparent success [9]. For this reason, all declared sensitivity results are retained and the primary candidate remains tau = 1. This protocol does not implement White\'s multiple-comparison test or retrospectively remove earlier knowledge of the baseline.')
    listing('Constructing the graph-relative score from the same observed shock', build_decisions, '        corr, adjacency, laplacian =', '        betas[t] = beta')

    heading('8.1. Primary historical outcomes', True)
    rows = [['Phase / model', 'Ann. net return', 'Ann. volatility', 'Max. drawdown', 'Mean gross', 'Mean turnover']]
    for (phase, model), row in primary.iterrows():
        rows.append([phase.title() + ' / ' + labels[model], f'{row.annualised_return:.2%}', f'{row.annualised_volatility:.2%}', f'{row.maximum_drawdown:.2%}', f'{row.mean_gross_exposure:.2%}', f'{row.mean_turnover:.2%}'])
    table('Primary strategies at 5 bps trading fees and 2% borrow', rows, [.27,.15,.14,.16,.14,.14])
    dg = primary.loc[('development', 'graph_tau_1')];db = primary.loc[('development', 'baseline')]
    vg = primary.loc[('validation', 'graph_tau_1')];vb = primary.loc[('validation', 'baseline')]
    p(f'The graph candidate earns {dg.annualised_return:.2%} annualised in development, compared with {db.annualised_return:.2%} for the baseline. In validation, the corresponding values are {vg.annualised_return:.2%} and {vb.annualised_return:.2%}. The graph-minus-baseline CAGR differences are therefore {100*(dg.annualised_return-db.annualised_return):+.2f} and {100*(vg.annualised_return-vb.annualised_return):+.2f} percentage points. Both strategies lose money at the default costs.')
    figure('Baseline and graph capital paths under identical accounting conventions', out/'06-graph-comparison.png')
    p('The graph portfolio has somewhat lower realised volatility and lower mean gross exposure. Equal exposure ceilings do not force equal realised capital utilisation. Therefore, the return comparison alone cannot isolate the effect of the graph signal from the portfolio scaling that follows it.')

    heading('8.2. A causal control for gross exposure', True)
    p('The control below matches the two portfolios at the decision close. It reduces both targets to the smaller of their gross exposures, then applies the original execution delay. It does not scale a portfolio upward, use realised future volatility or relax a name limit. This is a project-specific diagnostic, not a claim that equal gross exposure implies equal risk.')
    equation('Matching the gross exposure of the two decision portfolios',
             r'G_t^*=\min(\|w_t^B\|_1,\|w_t^G\|_1),\qquad w_t^{j,*}=w_t^j\frac{G_t^*}{\|w_t^j\|_1}',
             'Equation 15 defines the control for j equal to baseline B or graph G. A zero denominator gives a flat vector. Uniform shrinking preserves dollar and estimated-beta neutrality and cannot increase any absolute name weight. Risk and sector composition can still differ.')
    listing('Matching exposure without levering either portfolio upward', match_gross_exposure, '    gross_baseline =', '    return tuple(controls)')
    matched = all_results[all_results.purpose == 'matched gross control'].set_index(['phase', 'model'])
    rows = [['Phase', 'Baseline CAGR', 'Graph CAGR', 'Difference (pp)', 'Common mean gross']]
    for phase in ['development', 'validation']:
        b=matched.loc[(phase,'baseline_matched')];g=matched.loc[(phase,'graph_matched')]
        rows.append([phase.title(), f'{b.annualised_return:.2%}', f'{g.annualised_return:.2%}', f'{100*(g.annualised_return-b.annualised_return):+.2f}', f'{b.mean_gross_exposure:.2%}'])
    table('Separate backtests of the matched-gross controls',rows,[.2,.2,.2,.18,.22])
    p('The validation advantage becomes smaller when gross exposure is matched, while the development disadvantage remains. This reinforces the need to discuss exposure and volatility alongside return. The controls are fully rerun portfolios, not an after-the-fact division of the original returns by average exposure.')

    heading('8.3. Paired uncertainty with dependent observations', True)
    p('The uncertainty calculation concerns the paired daily net-return difference at the primary cost settings. Both strategies experience the same dates and market observations. Resampling their paired difference preserves that contemporaneous comparison; resampling the two strategies independently would discard it.')
    equation('Paired daily difference and annualised arithmetic mean',
             r'\delta_t=R_t^{G,\mathrm{net}}-R_t^{B,\mathrm{net}},\qquad \widehat{\mu}_{\mathrm{ann}}=252\,\bar\delta',
             'Equation 16 defines the estimated annualised arithmetic difference. It is not the difference between the two compounded annual growth rates. The uncertainty intervals below refer to this mean, so their estimate should not be substituted for the CAGR difference in the performance table.')
    p('Politis and Romano introduce the stationary bootstrap in <i>The Stationary Bootstrap</i> (1994) [16]. Nordman restates its geometric-block construction in Section 2.1 of <i>A note on the stationary bootstrap\'s variance</i> (2009) [18]. Following that construction, this implementation restarts at a uniformly chosen observed date or continues circularly from the preceding sampled index.')
    equation('Random restarts and circular continuation in the stationary bootstrap',
             r'\Pr(\mathrm{restart})=\ell^{-1},\qquad I_{k+1}^*=1+(I_k^*\ \mathrm{mod}\ T)',
             'Equation 17 gives the restart probability and the continuation rule when no restart occurs. Here ell is the expected block length, T is the phase sample size and the mathematical indices run from 1 to T. On a restart, a new index is uniform on that range. Python uses the equivalent zero-based convention.')
    listing('Preserving blocks through random restarts and circular continuation', stationary_indices, '    indices =', '    return indices')
    p('The primary interval uses 5,000 replicates and expected block length 10; lengths 5 and 20 are retained as sensitivity checks. The reported bounds are the 2.5th and 97.5th percentiles of the bootstrap mean, multiplied by 252. Seeds are specified in the protocol and derive deterministically from phase and block length. No block length is chosen because it yields a preferred conclusion.')

    heading('8.4. HAC cross-check and interpretation', True)
    p('Newey and West, in <i>A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix</i> (1987), develop a covariance estimator using weighted lagged covariances [17]. Their 1986 working-paper version was consulted for the Bartlett weights. Here the intercept-only special case supplies a second estimate of uncertainty for the paired mean.')
    equation('Bartlett-weighted long-run variance of the paired difference',
             r'\widehat{\Omega}=\widehat{\gamma}_0+2\sum_{k=1}^{K}\left(1-\frac{k}{K+1}\right)\widehat{\gamma}_k',
             'Equation 18 uses K = 10 lags. Each gamma-hat is the sum of products of mean-centred paired differences k observations apart, divided by the full phase length T. The same T denominator is used at every lag. This convention is checked against the equivalent Bartlett quadratic form.')
    equation('HAC standard error of the annualised arithmetic difference',
             r'\widehat{\mathrm{SE}}(\widehat{\mu}_{\mathrm{ann}})=252\sqrt{\widehat{\Omega}/T}',
             'Equation 19 scales the standard error of the sample mean by 252. It does not use square-root-of-252 volatility scaling. The approximate 95% HAC interval adds and subtracts the standard-normal critical value times this standard error.')
    listing('Accumulating serial covariance with Bartlett weights', hac_mean_interval, '    centered =', '    if long_run_variance <')
    rows=[['Phase','Mean difference (pp)','95% bootstrap interval (pp)','95% HAC interval (pp)']]
    for phase in ['development','validation']:
        sb=uncertainty[(uncertainty.phase==phase)&(uncertainty.method=='stationary bootstrap')&(uncertainty.block_or_lags==10)].iloc[0]
        hac=uncertainty[(uncertainty.phase==phase)&(uncertainty.method=='Newey-West HAC')].iloc[0]
        rows.append([phase.title(),f'{100*sb.annualised_mean_difference:+.2f}',f'[{100*sb.annualised_lower:+.2f}, {100*sb.annualised_upper:+.2f}]',f'[{100*hac.annualised_lower:+.2f}, {100*hac.annualised_upper:+.2f}]'])
    table('Pointwise uncertainty for the primary paired-return difference',rows,[.2,.24,.3,.26])
    p('The development intervals lie below zero, while every validation interval spans zero. Thus the modest positive validation point estimate does not establish a reliable graph advantage. These are approximate, pointwise intervals conditional on the observed policies and basket. They assume adequate stationarity and weak dependence, do not refit signals on bootstrapped price paths, and cannot correct survivorship bias, historical selection or repeated model searching.')

    heading('8.5. Sensitivity and the economic effect of costs', True)
    figure('Stationary-bootstrap and HAC intervals for the paired mean',out/'08-paired-uncertainty.png')
    figure('Graph-minus-baseline CAGR across every declared fee and diffusion time',out/'07-diffusion-and-costs.png')
    p('Every tested diffusion time underperforms the baseline in development and improves its validation CAGR slightly. None is profitable in validation, even when trading fees are zero and borrow remains 2%. This pattern is retained without promoting a different diffusion time to the primary specification. The complete scenario values and calendar-year returns are supplied as machine-readable outputs.')

    heading('8.6. Gross contribution, borrow and turnover', True)
    figure('Annualised arithmetic return contributions and recurring charges',out/'09-return-and-cost-components.png')
    p('For the primary graph in development, the positive gross arithmetic contribution is insufficient to cover trading and borrowing charges. In validation its gross contribution is smaller still. This diagnosis is more informative than reporting a Sharpe statistic alone: the graph changes the relative allocation, but the observed gross signal does not finance the declared turnover cost.')
    rows=[['Annual borrow','Dev. baseline','Dev. graph','Val. baseline','Val. graph']]
    for borrow in [0,.02,.05]:
        row=[f'{borrow:.0%}']
        for phase,model in [('development','baseline'),('development','graph_tau_1'),('validation','baseline'),('validation','graph_tau_1')]:
            value=all_results[(all_results.phase==phase)&(all_results.model==model)&(all_results.trading_cost_bps==5)&(all_results.annual_borrow_rate==borrow)].annualised_return.iloc[0]
            row.append(f'{value:.2%}')
        rows.append(row)
    table('Borrow sensitivity: CAGR with trading fees fixed at 5 bps',rows,[.2,.2,.2,.2,.2])
    p('The zero-borrow case retains transaction fees. It is a sensitivity scenario, not an assertion that every short can be financed for free. Likewise, a uniform 5% borrow rate does not represent security-specific availability or a stressed lending book. These tests describe the assumed ledger, not executable brokerage terms.')

    heading('8.7. Interpreting diffusion through an interactive graph', True)
    equation('Spectral gain applied to the unsmoothed residual',
             r'g_{\tau}(\lambda)=1-\exp(-\tau\lambda)',
             'Equation 20 follows directly from Equation 8: an eigenvector of L with eigenvalue lambda is multiplied by this factor in x minus its diffused value. The zero-eigenvalue component is removed. Changing tau changes the relative treatment of graph modes; the subsequent exposure projection and scaling remain separate operations.')
    figure('A historical graph and the resulting unconstrained scores',out/'10-graph-signal-snapshot.png')
    p('The companion <b>Graph-Diffusion-Explorer.html</b> shows 120 monthly graph snapshots, with a rotatable 3D network, date slider and paired score bars. Horizontal node coordinates are a fixed arrangement of the six research groups for display. Lines on the zero plane show retained connections; height shows the graph score. Neither drawing coordinates nor rendered interpolation enter the trading algorithm.')
    p('A positive plotted graph score proposes a long direction before the constraints are applied. The final projected weight may have a different sign. This distinction helps connect the mathematical operator to the implementation without presenting raw scores as actual trades or interpreting an attractive network visual as evidence of financial value.')
