"""Generate final-study manuscript tables directly from the retained outputs."""
import pandas as pd


def final_tables(root):
    out=root/"outputs/final"
    summary=pd.read_csv(out/"final-summary.csv")
    primary=summary.loc[summary.purpose=="primary"].set_index("model")
    tables={}
    lines=["Table 19. Reserved-test primary outcomes at 5 bps and 2% annual short borrow", "",
           "| Measure | Baseline | Graph, τ = 1 |", "| --- | ---: | ---: |"]
    for key,label in [("annualised_return","CAGR"),("total_return","Total return"),("maximum_drawdown","Maximum drawdown"),
                      ("annualised_volatility","Annualised volatility"),("mean_gross_exposure","Mean gross exposure"),("mean_turnover","Mean daily turnover")]:
        lines.append(f"| {label} | {100*primary.loc['baseline',key]:.2f}% | {100*primary.loc['graph_tau_1',key]:.2f}% |")
    lines.append(f"| Realised full-period SPY beta | {primary.loc['baseline','realized_market_beta']:.4f} | {primary.loc['graph_tau_1','realized_market_beta']:.4f} |")
    tables['primary']='\n'.join(lines)
    inference=pd.read_csv(out/"mean-inference.csv")
    selected=inference.loc[(inference.method=="stationary bootstrap") & (inference.block_or_lags==10)]
    lines=["Table 20. Annualised arithmetic means and stationary-bootstrap intervals; percentage points", "",
           "| Comparison | Estimate | Pointwise 95% interval | Bonferroni 98.33% interval |", "| --- | ---: | --- | --- |"]
    for key,label in [("baseline_net_mean","Baseline versus zero cash rate"),("graph_net_mean","Graph versus zero cash rate"),
                      ("graph_minus_baseline_mean","Graph minus baseline")]:
        row=selected.loc[selected.contrast==key].set_index("interval_type")
        interval=lambda kind:f"[{100*row.loc[kind,'annualised_lower']:+.2f}, {100*row.loc[kind,'annualised_upper']:+.2f}]"
        lines.append(f"| {label} | {100*row.iloc[0].annualised_mean:+.2f} | {interval('pointwise')} | {interval('bonferroni')} |")
    tables['inference']='\n'.join(lines)
    lines=["Table 21. Matched-gross control at the default costs", "", "| Measure | Baseline matched | Graph matched |", "| --- | ---: | ---: |"]
    matched=summary.loc[summary.purpose=="matched gross control"].set_index("model")
    for key,label in [("annualised_return","CAGR"),("mean_gross_exposure","Mean gross exposure"),("mean_turnover","Mean daily turnover")]:
        lines.append(f"| {label} | {100*matched.loc['baseline_matched',key]:.2f}% | {100*matched.loc['graph_matched',key]:.2f}% |")
    tables['matched']='\n'.join(lines)
    lines=["Table 22. Every declared fee/diffusion case: final-test CAGR; borrow fixed at 2%", "",
           "| Model | 0 bps | 5 bps | 10 bps | 20 bps |", "| --- | ---: | ---: | ---: | ---: |"]
    for model in ['baseline','graph_tau_0.5','graph_tau_1','graph_tau_2']:
        rows=summary.loc[(summary.model==model)&(summary.annual_borrow_rate==.02)].set_index('trading_cost_bps')
        lines.append('| '+model.replace('graph_tau_','Graph τ = ').capitalize()+' | '+' | '.join(f"{100*rows.loc[fee,'annualised_return']:.2f}%" for fee in [0,5,10,20])+' |')
    tables['fees']='\n'.join(lines)
    lines=["Table 23. Every declared borrow case: final-test CAGR; trading cost fixed at 5 bps", "",
           "| Annual short borrow | Baseline | Graph, τ = 1 |", "| --- | ---: | ---: |"]
    selected=summary.loc[(summary.trading_cost_bps==5)&summary.model.isin(['baseline','graph_tau_1'])].set_index(['model','annual_borrow_rate'])
    for rate in [0,.02,.05]:
        lines.append(f"| {rate:.0%} | {100*selected.loc[('baseline',rate),'annualised_return']:.2f}% | {100*selected.loc[('graph_tau_1',rate),'annualised_return']:.2f}% |")
    tables['borrow']='\n'.join(lines)
    yearly=pd.read_csv(out/'calendar-year-results.csv').pivot(index='year',columns='model',values='net_return')
    lines=["Table 24. Calendar-year net returns within one continuous final-test ledger", "",
           "| Year | Baseline | Graph, τ = 1 |", "| --- | ---: | ---: |"]
    for year,row in yearly.iterrows():lines.append(f"| {year} | {100*row.baseline:.2f}% | {100*row.graph_tau_1:.2f}% |")
    tables['annual']='\n'.join(lines)
    fits=pd.read_csv(out/'topology/control-model-scores.csv');fits=fits.loc[fits.window==126].set_index('feature')
    corr=pd.read_csv(out/'topology/control-correlations.csv');corr=corr.loc[(corr.window==126)&(corr.control=='mean_correlation')].set_index('feature')
    window=pd.read_csv(out/'topology/window-sensitivity.csv').set_index(['feature','window'])
    lines=["Table 25. Primary-window topology transfer and declared window checks on the final period", "",
           "| Feature | Development-fitted model: test R² | Spearman with mean correlation | 63 vs 126 rank correlation | 252 vs 126 rank correlation |", "| --- | ---: | ---: | ---: | ---: |"]
    for feature in ['h0_mean','h0_max','h1_total','h1_max']:
        lines.append(f"| {feature.replace('_',' ').upper()} | {fits.loc[feature,'r2']:.3f} | {corr.loc[feature,'spearman']:.3f} | {window.loc[(feature,63),'spearman']:.3f} | {window.loc[(feature,252),'spearman']:.3f} |")
    tables['topology']='\n'.join(lines)
    return tables
