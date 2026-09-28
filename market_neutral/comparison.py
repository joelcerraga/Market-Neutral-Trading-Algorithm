"""Frozen historical graph comparison, sensitivities and matched-exposure controls."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .config import ResearchConfig
from .data import simple_returns
from .strategy import build_decisions
from .backtest import execute_targets
from .historical import load_protocol, phase_inputs, phase_metrics, sha256
from .inference import stationary_mean_interval, hac_mean_interval


def load_comparison_protocol(root, dataset=None):
    root = Path(root)
    parent = load_protocol(root)
    path = root / "protocol/graph-comparison-v1.json"
    lock = json.loads(path.with_suffix(".lock.json").read_text())
    if sha256(path) != lock["sha256"]:
        raise ValueError("Graph protocol differs from its frozen hash")
    protocol = json.loads(path.read_text())
    if protocol["parent_sha256"] != sha256(root / "protocol/historical-v1.json"):
        raise ValueError("Parent protocol changed")
    if protocol["final_holdout_release"] or protocol["phases"] != parent["allowed_phases"]:
        raise ValueError("Reserved final test cannot be released by this comparison")
    if dataset is not None and dataset.metadata["input_sha256"] != protocol["input_sha256"]:
        raise ValueError("Comparison requires the frozen Milestone 2 observations")
    return parent, protocol


def match_gross_exposure(baseline, graph):
    """Scale both daily decisions DOWN to their common minimum gross exposure."""
    if not baseline.index.equals(graph.index) or not baseline.columns.equals(graph.columns):
        raise ValueError("Matched controls require identical dates and assets")
    gross_baseline = baseline.abs().sum(axis=1)
    gross_graph = graph.abs().sum(axis=1)
    common = np.minimum(gross_baseline, gross_graph)
    controls = []
    for weights, gross in [(baseline, gross_baseline), (graph, gross_graph)]:
        factor = common.div(gross.where(gross > 1e-14)).fillna(0.)
        controls.append(weights.mul(factor, axis=0))
    return tuple(controls)


def validate_ledger(result, config):
    ledger = result.ledger
    np.testing.assert_allclose(ledger.net_return,
        ledger.gross_return - ledger.trading_cost_return - ledger.borrow_cost_return, atol=1e-12)
    if ledger.net_exposure.abs().max() > 1e-10 or ledger.estimated_beta_exposure.abs().max() > 1e-10:
        raise AssertionError("Neutrality check failed")
    if ledger.gross_exposure.max() > config.gross_limit + 1e-12 or ledger.max_position.max() > config.position_limit + 1e-12:
        raise AssertionError("Exposure ceiling failed")
    if ledger.gross_return.iloc[0] != 0 or ledger.gross_exposure.iloc[-1] != 0:
        raise AssertionError("Phase entry/exit convention failed")


def compare(root, dataset):
    root = Path(root)
    parent, protocol = load_comparison_protocol(root, dataset)
    config = ResearchConfig(**parent["config"])
    returns, market = simple_returns(dataset)
    out = root / "outputs/comparison"
    out.mkdir(parents=True, exist_ok=True)
    primary = build_decisions(returns, market, config)
    targets = {"baseline": primary.targets["baseline"], "graph_tau_1": primary.targets["graph"]}
    for tau in protocol["diffusion_times"]:
        if tau == config.diffusion_time:
            continue
        targets[f"graph_tau_{tau:g}"] = build_decisions(returns, market, replace(config, diffusion_time=tau)).targets["graph"]
    matched_base, matched_graph = match_gross_exposure(targets["baseline"], targets["graph_tau_1"])
    targets.update(baseline_matched=matched_base, graph_matched=matched_graph)
    primary.diagnostics.to_csv(out / "graph-diagnostics.csv", float_format="%.12g")
    rows, experiments, results = [], [], {}

    def evaluate(phase, model, fee, borrow, purpose):
        key = f"{phase}__{model}__fee{fee:g}__borrow{borrow:g}"
        scenario = replace(config, trading_cost_bps=fee, annual_borrow_rate=borrow)
        r, w, beta = phase_inputs(returns, targets[model], primary.betas, parent, phase)
        result = execute_targets(r, w, scenario, beta, liquidate_at_end=True)
        validate_ledger(result, scenario)
        metrics = phase_metrics(result, market, scenario)
        ledger = result.ledger
        metrics.update(annualised_arithmetic_gross=float(252 * ledger.gross_return.mean()),
                       annualised_arithmetic_net=float(252 * ledger.net_return.mean()),
                       annualised_trading_drag=float(252 * ledger.trading_cost_return.mean()),
                       annualised_borrow_drag=float(252 * ledger.borrow_cost_return.mean()))
        entry = {"phase": phase, "model": model, "trading_cost_bps": fee,
                 "annual_borrow_rate": borrow, "purpose": purpose, **metrics}
        rows.append(entry)
        result.ledger.to_csv(out / f"{key}-ledger.csv", float_format="%.12g")
        if fee == 5 and borrow == .02:
            results[(phase, model)] = result
            result.execution_weights.to_csv(out / f"{phase}__{model}-weights.csv", float_format="%.12g")
        experiments.append({"id": key, "status": "completed", "purpose": purpose,
                            "ledger": f"{key}-ledger.csv", "configuration": scenario.__dict__,
                            "model": model, "phase": phase})

    for phase in protocol["phases"]:
        for model in ["baseline"] + [f"graph_tau_{tau:g}" for tau in protocol["diffusion_times"]]:
            for fee in protocol["cost_scenarios_bps"]:
                evaluate(phase, model, fee, .02, "primary" if model in ["baseline", "graph_tau_1"] else "diffusion sensitivity")
        for borrow in protocol["borrow_sensitivity"]:
            if borrow != .02:
                for model in ["baseline", "graph_tau_1"]:
                    evaluate(phase, model, 5, borrow, "borrow sensitivity")
        for model in ["baseline_matched", "graph_matched"]:
            evaluate(phase, model, 5, .02, "matched gross control")
    summary = pd.DataFrame(rows)
    if len(summary) != protocol["expected_backtest_rows"]:
        raise AssertionError("Not every declared scenario was executed")
    # Guard against an accidental change of the already reported baseline.
    previous = pd.read_csv(root / "outputs/historical/baseline-summary.csv")
    actual = summary[(summary.model == "baseline") & (summary.annual_borrow_rate == .02)]
    merged = previous.merge(actual, on=["phase", "trading_cost_bps"], suffixes=("_old", "_new"), validate="one_to_one")
    for column in previous.select_dtypes(include="number").columns:
        if column != "trading_cost_bps":
            np.testing.assert_allclose(merged[column + "_old"], merged[column + "_new"], rtol=1e-9, atol=1e-10)
    summary.to_csv(out / "comparison-summary.csv", index=False, float_format="%.12g")
    (out / "experiment-register.json").write_text(json.dumps(experiments, indent=2))

    uncertainty, annual = [], []
    settings = protocol["uncertainty"]
    for phase_number, phase in enumerate(protocol["phases"]):
        baseline = results[(phase, "baseline")].ledger
        graph = results[(phase, "graph_tau_1")].ledger
        paired = pd.DataFrame({"baseline": baseline.net_return, "graph": graph.net_return})
        paired["difference"] = paired.graph - paired.baseline
        paired.to_csv(out / f"{phase}-paired-returns.csv", float_format="%.12g")
        for length in settings["mean_block_lengths"]:
            interval = stationary_mean_interval(paired.difference, length, settings["stationary_bootstrap_replicates"],
                settings["random_seed"] + phase_number * 100 + length, settings["confidence_level"])
            uncertainty.append({"phase": phase, "method": "stationary bootstrap", "block_or_lags": length,
                "annualised_mean_difference": 252 * interval["daily_mean"],
                "annualised_lower": 252 * interval["daily_lower"], "annualised_upper": 252 * interval["daily_upper"],
                "annualised_standard_error": 252 * interval["bootstrap_standard_error"]})
        interval = hac_mean_interval(paired.difference.to_numpy(), settings["hac_lags"], settings["confidence_level"])
        uncertainty.append({"phase": phase, "method": "Newey-West HAC", "block_or_lags": settings["hac_lags"],
            "annualised_mean_difference": 252 * interval["daily_mean"],
            "annualised_lower": 252 * interval["daily_lower"], "annualised_upper": 252 * interval["daily_upper"],
            "annualised_standard_error": 252 * interval["hac_standard_error"]})
        for year, part in paired.groupby(paired.index.year):
            annual.append({"phase": phase, "year": int(year),
                           "baseline_return": float((1 + part.baseline).prod() - 1),
                           "graph_return": float((1 + part.graph).prod() - 1),
                           "mean_daily_difference": float(part.difference.mean())})
    uncertainty = pd.DataFrame(uncertainty)
    uncertainty.to_csv(out / "paired-uncertainty.csv", index=False, float_format="%.12g")
    pd.DataFrame(annual).to_csv(out / "calendar-year-returns.csv", index=False, float_format="%.12g")
    manifest = {"protocol_sha256": sha256(root / "protocol/graph-comparison-v1.json"),
        "parent_protocol_sha256": protocol["parent_sha256"], "input_sha256": dataset.metadata["input_sha256"],
        "executed_utc": datetime.now(timezone.utc).isoformat(), "completed_scenarios": len(summary),
        "phases": protocol["phases"], "primary_model": "graph_tau_1", "model_selected_after_results": False,
        "baseline_reproduced": True, "final_holdout_acquired": False, "final_holdout_evaluated": False,
        "source_sha256": {f"market_neutral/{name}.py": sha256(root / f"market_neutral/{name}.py")
                          for name in ["comparison", "inference", "strategy", "graph", "backtest", "portfolio"]}}
    (out / "run-manifest.json").write_text(json.dumps(manifest, indent=2))
    return results, summary, uncertainty, primary
