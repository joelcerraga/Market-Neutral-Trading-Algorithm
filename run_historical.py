"""Offline historical baseline. Run fetch_historical.py first if cache is absent."""
from pathlib import Path
from market_neutral.historical import assemble_dataset, evaluate_baseline
from market_neutral.historical_plots import figures, explorer


def run(root=None):
    root=Path(root) if root else Path(__file__).resolve().parent
    dataset,audit=assemble_dataset(root)
    results,summary=evaluate_baseline(root,dataset)
    figures(root,dataset,results,summary)
    explorer(root,dataset)
    return dataset,audit,results,summary


if __name__ == "__main__":
    _,_,_,summary=run()
    print(summary[["phase","trading_cost_bps","annualised_return","sharpe_zero_cash_rate","maximum_drawdown"]].to_string(index=False))
    print("Exploratory survivor basket. Final holdout and graph-strategy performance have not been evaluated.")
