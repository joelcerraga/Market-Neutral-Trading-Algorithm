"""The locked final experiment; retains all cases and never promotes a winner."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from importlib.metadata import version
import json
import numpy as np
import pandas as pd
from .final_io import write_csv_verified, write_text_verified
from .config import ResearchConfig
from .data import simple_returns
from .strategy import build_decisions
from .backtest import execute_targets
from .comparison import match_gross_exposure, validate_ledger
from .historical import phase_inputs, phase_metrics, sha256
from .final_data import load_final_protocol
from .final_inference import fixed_family_intervals, matched_interval, evidence_gate
from .topology import FEATURES, CONTROLS, rolling_features, predict_control_model, diagram_stability


def final_topology(root, dataset, protocol):
    """Transfer frozen descriptor/control relationships; no final-period fitting."""
    root = Path(root)
    if version("ripser") != "0.6.14":
        raise ValueError("Install the pinned Ripser version")
    returns, market = simple_returns(dataset)
    start, end = protocol["test_period"]
    dates = returns.loc[start:end].index
    monthly = pd.Series(dates,index=dates).resample("ME").last().dropna()
    settings = protocol["topology_transfer"]
    frame,snapshots,distances = rolling_features(returns,market,settings["windows"],dates,monthly)
    models = json.loads((root / "outputs/topology/control-models.json").read_text())
    scores, correlations, predictions, stability = [], [], [], []
    for window in settings["windows"]:
        data = frame.loc[frame.window == window]
        for feature in FEATURES:
            model = models[f"{window}|{feature}"]
            if model["fitted_last_date"] >= "2017-01-01":
                raise ValueError("Control model was not development-only")
            fitted = predict_control_model(data,model)
            actual = data[feature].to_numpy()
            sst = np.sum((actual-actual.mean())**2)
            if sst <= 1e-20:
                raise ValueError("Constant descriptor: R2 undefined")
            scores.append({"phase":"final_test","window":window,"feature":feature,"n":len(data),
                           "r2":float(1-np.sum((actual-fitted)**2)/sst),
                           "rmse":float(np.sqrt(np.mean((actual-fitted)**2)))})
            predictions.append(pd.DataFrame({"date":data.index,"window":window,"feature":feature,
                                             "actual":actual,"fitted":fitted,"residual":actual-fitted}))
            for control in CONTROLS:
                correlations.append({"phase":"final_test","window":window,"feature":feature,"control":control,
                                     "n":len(data),"spearman":float(data[feature].corr(data[control],method="spearman"))})
            if window != settings["primary_window"]:
                primary = frame.loc[frame.window == settings["primary_window"],feature]
                if not data.index.equals(primary.index):
                    raise ValueError("Mismatched topology calendars")
                stability.append({"phase":"final_test","window":window,"primary_window":settings["primary_window"],
                                  "feature":feature,"n":len(data),
                                  "spearman":float(data[feature].corr(primary,method="spearman"))})
    checks = diagram_stability(snapshots,distances,settings["primary_window"])
    out = root / "outputs/final/topology";out.mkdir(parents=True,exist_ok=True)
    tables = {"features.csv":frame,"control-model-scores.csv":pd.DataFrame(scores),
              "control-correlations.csv":pd.DataFrame(correlations),
              "control-model-predictions.csv":pd.concat(predictions,ignore_index=True),
              "window-sensitivity.csv":pd.DataFrame(stability),"diagram-stability.csv":checks}
    for name,table in tables.items():
        write_csv_verified(table,out / name,index=name == "features.csv",float_format="%.12g")
    write_text_verified(out / "monthly-diagrams.json",json.dumps(snapshots,indent=2)+"\n")
    return {"feature_rows":len(frame),"dates_per_window":len(dates),"monthly_frames":len(monthly),
            "diagram_bound_checks":len(checks),"control_models_refitted":False,
            "frozen_control_models_sha256":sha256(root / "outputs/topology/control-models.json")}


def evaluate_final(root,dataset):
    root = Path(root);p = load_final_protocol(root)
    if dataset.metadata["protocol_sha256"] != sha256(root / "protocol/final-evaluation-v1.json"):
        raise ValueError("Final dataset/protocol mismatch")
    config = ResearchConfig(**p["config"])
    returns,market = simple_returns(dataset)
    primary = build_decisions(returns,market,config)
    targets = {"baseline":primary.targets["baseline"],"graph_tau_1":primary.targets["graph"]}
    for tau in p["diffusion_times"]:
        if tau != config.diffusion_time:
            targets[f"graph_tau_{tau:g}"] = build_decisions(returns,market,replace(config,diffusion_time=tau)).targets["graph"]
    matched = match_gross_exposure(targets["baseline"],targets["graph_tau_1"])
    targets.update(baseline_matched=matched[0],graph_matched=matched[1])
    phase_protocol = {"allowed_phases":["final_test"],"phases":{"final_test":p["test_period"]}}
    out = root / "outputs/final";out.mkdir(parents=True,exist_ok=True)
    rows,experiments,results = [], [], {}

    def evaluate(model,fee,borrow,purpose):
        scenario = replace(config,trading_cost_bps=fee,annual_borrow_rate=borrow)
        r,w,beta = phase_inputs(returns,targets[model],primary.betas,phase_protocol,"final_test")
        result = execute_targets(r,w,scenario,beta,liquidate_at_end=True)
        validate_ledger(result,scenario)
        metrics = phase_metrics(result,market,scenario)
        ledger = result.ledger
        metrics.update(annualised_arithmetic_gross=float(252*ledger.gross_return.mean()),
                       annualised_arithmetic_net=float(252*ledger.net_return.mean()),
                       annualised_trading_drag=float(252*ledger.trading_cost_return.mean()),
                       annualised_borrow_drag=float(252*ledger.borrow_cost_return.mean()))
        rows.append({"phase":"final_test","model":model,"trading_cost_bps":fee,
                     "annual_borrow_rate":borrow,"purpose":purpose,**metrics})
        key = f"final_test__{model}__fee{fee:g}__borrow{borrow:g}"
        write_csv_verified(ledger,out / f"{key}-ledger.csv",float_format="%.12g")
        if fee == 5 and borrow == .02:
            results[model] = result
            write_csv_verified(result.execution_weights,out / f"{model}-weights.csv",float_format="%.12g")
        experiments.append({"id":key,"status":"completed","model":model,"purpose":purpose,
                            "configuration":scenario.__dict__,"ledger":f"{key}-ledger.csv"})

    for model in ["baseline"]+[f"graph_tau_{tau:g}" for tau in p["diffusion_times"]]:
        for fee in p["cost_scenarios_bps"]:
            purpose = "primary" if model in ["baseline","graph_tau_1"] and fee == 5 else "declared sensitivity"
            evaluate(model,fee,.02,purpose)
    for borrow in p["borrow_sensitivity"]:
        if borrow != .02:
            for model in ["baseline","graph_tau_1"]:
                evaluate(model,5,borrow,"borrow sensitivity")
    for model in ["baseline_matched","graph_matched"]:
        evaluate(model,5,.02,"matched gross control")
    summary = pd.DataFrame(rows)
    if len(summary) != p["expected_scenarios"] or len({e["id"] for e in experiments}) != len(experiments):
        raise ValueError("Incomplete or duplicated final scenario set")
    write_csv_verified(summary,out / "final-summary.csv",index=False,float_format="%.12g")
    write_text_verified(out / "experiment-register.json",json.dumps(experiments,indent=2)+"\n")
    paired = pd.DataFrame({"baseline":results["baseline"].ledger.net_return,
                           "graph":results["graph_tau_1"].ledger.net_return})
    paired["difference"] = paired.graph-paired.baseline
    write_csv_verified(paired,out / "paired-returns.csv",float_format="%.12g")
    intervals,samples = fixed_family_intervals(paired,p["inference"])
    write_csv_verified(intervals,out / "mean-inference.csv",index=False,float_format="%.12g")
    write_csv_verified(samples,out / "primary-bootstrap-means.csv",index=False,float_format="%.12g")
    matched_difference = results["graph_matched"].ledger.net_return-results["baseline_matched"].ledger.net_return
    write_csv_verified(matched_difference.rename("difference"),out / "matched-paired-returns.csv",float_format="%.12g")
    control = matched_interval(matched_difference,p["inference"])
    write_csv_verified(control,out / "matched-uncertainty.csv",index=False,float_format="%.12g")
    graph_cagr = summary.loc[(summary.model=="graph_tau_1") & (summary.trading_cost_bps==5) &
                             (summary.annual_borrow_rate==.02),"annualised_return"].iloc[0]
    gate = evidence_gate(graph_cagr,intervals,control,p["inference"]["primary_block_length"])
    write_text_verified(out / "evidence-gate.json",json.dumps(gate,indent=2)+"\n")
    annual,exposures = [], []
    for model in ["baseline","graph_tau_1"]:
        ledger = results[model].ledger
        for year,part in ledger.groupby(ledger.index.year):
            annual.append({"year":int(year),"model":model,"days":len(part),
                           "net_return":float((1+part.net_return).prod()-1),
                           "annualised_arithmetic_gross":float(252*part.gross_return.mean()),
                           "annualised_trading_drag":float(252*part.trading_cost_return.mean()),
                           "annualised_borrow_drag":float(252*part.borrow_cost_return.mean()),
                           "mean_gross_exposure":float(part.gross_exposure.mean()),
                           "mean_turnover":float(part.turnover.mean())})
        benchmark = market.loc[ledger.index]
        beta = ledger.net_return.rolling(63).cov(benchmark)/benchmark.rolling(63).var()
        exposures.append(pd.DataFrame({"date":ledger.index,"model":model,"rolling63_realised_beta":beta.to_numpy(),
                                       "gross_exposure":ledger.gross_exposure.to_numpy(),"turnover":ledger.turnover.to_numpy()}))
    write_csv_verified(pd.DataFrame(annual),out / "calendar-year-results.csv",index=False,float_format="%.12g")
    write_csv_verified(pd.concat(exposures,ignore_index=True),out / "exposure-diagnostics.csv",index=False,float_format="%.12g")
    write_csv_verified(primary.diagnostics.loc[p["test_period"][0]:p["test_period"][1]],out / "graph-diagnostics.csv",float_format="%.12g")
    topology = final_topology(root,dataset,p)
    files = sorted(path for path in out.rglob("*") if path.is_file() and path.suffix in {".csv",".json"}
                   and path.name not in {"run-manifest.json","explorer-figure.json"})
    manifest = {"executed_utc":datetime.now(timezone.utc).isoformat(),"protocol_sha256":dataset.metadata["protocol_sha256"],
                "input_sha256":dataset.metadata["input_sha256"],"test_first_date":str(paired.index[0].date()),
                "test_last_date":str(paired.index[-1].date()),"test_sessions":len(paired),"completed_scenarios":len(summary),
                "primary_model":"graph_tau_1","topology_overlay":False,"test_is_now_observed":True,
                "post_test_model_selection":False,"evidence_gate":gate, "topology":topology,
                "versions":{name:version(name) for name in ["numpy","pandas","scipy","ripser","persim","plotly"]},
                "files":{str(path.relative_to(out)):sha256(path) for path in files},
                "source_sha256":{name:sha256(root / name) for name in ["market_neutral/final_data.py",
                    "market_neutral/final_evaluation.py","market_neutral/final_inference.py","market_neutral/final_io.py"]}}
    write_text_verified(out / "run-manifest.json",json.dumps(manifest,indent=2)+"\n")
    return results,summary,intervals,manifest
