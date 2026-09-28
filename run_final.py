"""Replay the frozen final experiment offline after explicit data acquisition."""
from pathlib import Path
import json
from market_neutral.final_data import assemble_final_dataset
from market_neutral.final_evaluation import evaluate_final

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    dataset,audit = assemble_final_dataset(ROOT)
    results,summary,intervals,manifest = evaluate_final(ROOT,dataset)
    from market_neutral.final_plots import create_final_figures
    create_final_figures(ROOT)
    print(summary.loc[summary.purpose=="primary",["model","annualised_return","maximum_drawdown","mean_turnover"]].to_string(index=False))
    print(json.dumps(manifest["evidence_gate"],indent=2))
