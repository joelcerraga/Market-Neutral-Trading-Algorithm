"""A fixed three-mean family; pair-preserving resampling and Bonferroni intervals."""
import numpy as np
import pandas as pd
from .inference import stationary_indices, hac_mean_interval, stationary_mean_interval

CONTRASTS = ("baseline_net_mean", "graph_net_mean", "graph_minus_baseline_mean")


def confidence_levels(alpha, family_size):
    if not 0 < alpha < 1 or not isinstance(family_size,int) or family_size < 1:
        raise ValueError("Invalid alpha or fixed family size")
    return {"pointwise":1-alpha,"bonferroni":1-alpha/family_size}


def fixed_family_intervals(paired, settings):
    if (not paired.index.is_unique or not paired.index.is_monotonic_increasing
            or not np.isfinite(paired[["baseline","graph"]].to_numpy()).all()):
        raise ValueError("Need finite, uniquely dated paired returns")
    base, graph = paired.baseline.to_numpy(), paired.graph.to_numpy()
    values = np.column_stack([base,graph,graph-base])
    levels = confidence_levels(settings["family_alpha"],3)
    rows, samples = [], {}
    for length in settings["block_lengths"]:
        indices = stationary_indices(len(paired),settings["stationary_bootstrap_replicates"],length,
                                     settings["seed"]+length)
        # Each column sees the same blocks; the difference is paired path by path.
        means = np.column_stack([values[:,j][indices].mean(axis=1) for j in range(3)])
        np.testing.assert_allclose(means[:,2],means[:,1]-means[:,0],atol=1e-15)
        if length == settings["primary_block_length"]:
            samples = {name:means[:,j] for j,name in enumerate(CONTRASTS)}
        for j, contrast in enumerate(CONTRASTS):
            for interval_type, confidence in levels.items():
                tail = (1-confidence)/2
                lower, upper = np.quantile(means[:,j],[tail,1-tail])
                rows.append({"contrast":contrast,"method":"stationary bootstrap","block_or_lags":length,
                             "interval_type":interval_type,"confidence_level":confidence,
                             "annualised_mean":252*values[:,j].mean(),"annualised_lower":252*lower,
                             "annualised_upper":252*upper,"annualised_standard_error":252*means[:,j].std(ddof=1)})
    for j,contrast in enumerate(CONTRASTS):
        for interval_type,confidence in levels.items():
            interval = hac_mean_interval(values[:,j],settings["hac_lags"],confidence)
            rows.append({"contrast":contrast,"method":"Newey-West HAC","block_or_lags":settings["hac_lags"],
                         "interval_type":interval_type,"confidence_level":confidence,
                         "annualised_mean":252*interval["daily_mean"],"annualised_lower":252*interval["daily_lower"],
                         "annualised_upper":252*interval["daily_upper"],"annualised_standard_error":252*interval["hac_standard_error"]})
    return pd.DataFrame(rows),pd.DataFrame(samples)


def matched_interval(difference,settings):
    rows = []
    boot = stationary_mean_interval(difference,settings["primary_block_length"],
        settings["stationary_bootstrap_replicates"],settings["seed"]+1000,settings["pointwise_confidence"])
    hac = hac_mean_interval(difference,settings["hac_lags"],settings["pointwise_confidence"])
    for name,length,interval in [("stationary bootstrap",settings["primary_block_length"],boot),
                                 ("Newey-West HAC",settings["hac_lags"],hac)]:
        rows.append({"contrast":"matched_graph_minus_baseline","method":name,"block_or_lags":length,
                     "confidence_level":settings["pointwise_confidence"],
                     "annualised_mean":252*interval["daily_mean"],"annualised_lower":252*interval["daily_lower"],
                     "annualised_upper":252*interval["daily_upper"]})
    return pd.DataFrame(rows)


def evidence_gate(graph_cagr,intervals,matched,primary_block_length=10):
    primary = intervals.loc[(intervals.method=="stationary bootstrap") &
                            (intervals.block_or_lags==primary_block_length) &
                            (intervals.interval_type=="bonferroni")].set_index("contrast")
    if set(primary.index) != set(CONTRASTS) or not primary.index.is_unique:
        raise ValueError("Missing or duplicate primary family interval")
    control = matched.loc[(matched.method=="stationary bootstrap") & (matched.block_or_lags==primary_block_length)]
    if len(control) != 1:
        raise ValueError("Missing matched-gross primary interval")
    conditions = {"positive_compound_return":bool(graph_cagr>0),
                  "positive_absolute_mean":bool(primary.loc["graph_net_mean","annualised_lower"]>0),
                  "positive_incremental_mean":bool(primary.loc["graph_minus_baseline_mean","annualised_lower"]>0),
                  "matched_gross_robustness":bool(control.iloc[0].annualised_lower>0)}
    return {"conditions":conditions,"all_conditions_met":all(conditions.values()),
            "meaning":"A predeclared evidence screen within this survivor basket, not a deployment or population-alpha guarantee"}
