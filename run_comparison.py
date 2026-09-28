"""Reproduce Milestone 3 from the frozen historical cache; no new acquisition."""
from pathlib import Path
from market_neutral.historical import assemble_dataset
from market_neutral.comparison import compare
from market_neutral.comparison_plots import figures, explorer


def run(root=None):
    root = Path(root) if root else Path(__file__).resolve().parent
    dataset, _ = assemble_dataset(root)
    results, summary, uncertainty, decisions = compare(root, dataset)
    figures(root, results, summary, uncertainty)
    explorer(root, dataset)
    return dataset, results, summary, uncertainty, decisions


if __name__ == "__main__":
    _, _, summary, uncertainty, _ = run()
    mask = summary.model.isin(["baseline", "graph_tau_1"]) & (summary.trading_cost_bps == 5) & (summary.annual_borrow_rate == .02)
    print(summary.loc[mask, ["phase", "model", "annualised_return", "maximum_drawdown", "mean_turnover", "mean_gross_exposure"]].to_string(index=False))
    print(uncertainty.to_string(index=False))
    print("All declared scenarios retained. Final holdout is unavailable in this milestone.")
