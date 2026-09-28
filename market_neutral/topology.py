"""Causal correlation geometry, persistence and descriptive control comparisons.

The asset cloud differs from the time-delay/market-index construction in
Gidea and Katz (2018). No portfolio return enters this module.
"""
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
import json
import numpy as np
import pandas as pd
from persim import bottleneck
from ripser import ripser
from .historical import load_protocol, sha256

FEATURES = ("h0_mean", "h0_max", "h1_total", "h1_max")
CONTROLS = ("mean_correlation", "mean_stock_volatility", "spy_volatility")


def load_topology_protocol(root):
    root = Path(root)
    path = root / "protocol/topology-features-v1.json"
    lock = json.loads(path.with_name("topology-features-v1.lock.json").read_text())
    if sha256(path) != lock["sha256"]:
        raise ValueError("Topology protocol differs from its frozen hash")
    p = json.loads(path.read_text())
    if sha256(root / "protocol/historical-v1.json") != p["historical_protocol_sha256"]:
        raise ValueError("Historical protocol mismatch")
    return p


def correlation_distance(history):
    """Asset distances: Euclidean chords between centred unit return vectors."""
    r = np.asarray(history, dtype=float)
    if r.ndim != 2 or min(r.shape) < 2 or not np.isfinite(r).all():
        raise ValueError("Need finite time-by-asset observations")
    centered = r - r.mean(axis=0)
    norms = np.linalg.norm(centered, axis=0)
    if (norms <= 1e-12).any():
        raise ValueError("Constant asset: correlation geometry is undefined")
    unit = centered / norms
    corr = np.clip(unit.T @ unit, -1., 1.)
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1.)
    distance = np.sqrt(2 * (1 - corr))
    np.fill_diagonal(distance, 0.)
    return corr, distance


def persistence(distance):
    """Full edge-threshold Rips filtration over F2, including triangle fillings."""
    d = np.asarray(distance, dtype=float)
    if (d.ndim != 2 or d.shape[0] != d.shape[1] or len(d) < 2
            or not np.isfinite(d).all() or (d < 0).any()
            or not np.allclose(d, d.T, atol=1e-12, rtol=0)
            or not np.allclose(np.diag(d), 0, atol=1e-12, rtol=0)):
        raise ValueError("Need a finite symmetric nonnegative distance matrix with zero diagonal")
    diagrams = ripser(d, distance_matrix=True, maxdim=1, coeff=2, thresh=np.inf)["dgms"]
    h0, h1 = diagrams
    essential = np.isinf(h0[:, 1])
    if essential.sum() != 1 or not np.isfinite(h1).all():
        raise ValueError("Full finite Rips filtration must have one essential H0 and no essential H1")
    h0 = h0[~essential].astype(float)
    # Ripser omits zero-length intervals. Keep all n-1 H0 merges in summaries.
    omitted = len(d) - 1 - len(h0)
    if omitted < 0:
        raise ValueError("Unexpected H0 merge count")
    if omitted:
        h0 = np.vstack([h0, np.zeros((omitted, 2))])
    h1 = h1.astype(float)
    if (h0[:, 1] < h0[:, 0]).any() or (h1[:, 1] < h1[:, 0]).any():
        raise ValueError("Invalid persistence interval")
    return {"h0": h0, "h1": h1, "essential_h0": 1, "zero_h0_merges": omitted}


def summarise(diagrams):
    l0 = np.diff(diagrams["h0"], axis=1).ravel()
    l1 = np.diff(diagrams["h1"], axis=1).ravel()
    return {"h0_mean": float(l0.mean()), "h0_max": float(l0.max(initial=0)),
            "h1_total": float(l1.sum()), "h1_max": float(l1.max(initial=0))}


def landscape(diagram, grid, layers=5):
    """Bubenik (2015): kth largest interval tent; ranks are discrete."""
    bars = np.asarray(diagram, dtype=float).reshape(-1, 2)
    if not np.isfinite(bars).all() or (bars[:, 1] < bars[:, 0]).any():
        raise ValueError("Landscapes here require finite valid bars")
    x = np.asarray(grid, dtype=float)
    tents = np.maximum(0, np.minimum(x[None, :] - bars[:, :1], bars[:, 1:] - x[None, :]))
    ordered = np.sort(tents, axis=0)[::-1]
    out = np.zeros((layers, len(x)))
    out[:min(layers, len(bars))] = ordered[:layers]
    return out


def rolling_features(returns, market, windows, dates, snapshot_dates=()):
    """At t, every estimator uses only its last W returns, ending at t."""
    if (not returns.index.equals(market.index) or not returns.index.is_unique
            or not returns.index.is_monotonic_increasing
            or not np.isfinite(returns.to_numpy()).all() or not np.isfinite(market).all()):
        raise ValueError("Need aligned finite observations on unique ordered dates")
    positions = returns.index.get_indexer(dates)
    if (positions < max(windows) - 1).any():
        raise ValueError("Every date must have all declared windows; no silent date dropping")
    rows, snapshots, distances = [], {}, {}
    r, m = returns.to_numpy(), market.to_numpy()
    snap_set = set(pd.DatetimeIndex(snapshot_dates))
    triangle = np.triu_indices(returns.shape[1], 1)
    for window in windows:
        for t in positions:
            date = returns.index[t]
            history = r[t + 1 - window:t + 1]
            corr, d = correlation_distance(history)
            dgms = persistence(d)
            row = {"date": date, "window": window, **summarise(dgms),
                   "mean_correlation": float(corr[triangle].mean()),
                   "mean_stock_volatility": float(history.std(axis=0, ddof=1).mean() * np.sqrt(252)),
                   "spy_volatility": float(m[t + 1 - window:t + 1].std(ddof=1) * np.sqrt(252)),
                   "finite_h0": len(dgms["h0"]), "essential_h0": dgms["essential_h0"],
                   "zero_h0_merges": dgms["zero_h0_merges"], "h1_intervals": len(dgms["h1"])}
            rows.append(row)
            if date in snap_set:
                key = f"{date.date()}|{window}"
                snapshots[key] = {"date": str(date.date()), "window": window,
                                  "h0": dgms["h0"].tolist(), "h1": dgms["h1"].tolist(),
                                  "essential_h0": 1, **summarise(dgms)}
                distances[key] = d
    return pd.DataFrame(rows).set_index("date"), snapshots, distances


def fit_control_model(train, feature):
    """Descriptive feature approximation; development is the only fitting data."""
    x = train[list(CONTROLS)].to_numpy()
    center, scale = x.mean(axis=0), x.std(axis=0, ddof=1)
    if (scale <= 1e-12).any():
        raise ValueError("Constant development control")
    design = np.column_stack([np.ones(len(x)), (x - center) / scale])
    coefficients, _, rank, _ = np.linalg.lstsq(design, train[feature].to_numpy(), rcond=None)
    if rank != design.shape[1]:
        raise ValueError("Rank-deficient control model")
    return {"center": center.tolist(), "scale": scale.tolist(), "coefficients": coefficients.tolist(),
            "condition_number": float(np.linalg.cond(design)), "fitted_rows": len(train),
            "fitted_first_date": str(train.index.min().date()), "fitted_last_date": str(train.index.max().date())}


def predict_control_model(frame, model):
    x = (frame[list(CONTROLS)].to_numpy() - model["center"]) / model["scale"]
    return np.column_stack([np.ones(len(x)), x]) @ np.asarray(model["coefficients"])


def evaluate_features(frame, phases, primary_window):
    corr_rows, fit_rows, stability_rows, models, predictions = [], [], [], {}, []
    windows = sorted(frame.window.unique())
    phase_data = {}
    for window in windows:
        whole = frame.loc[frame.window == window]
        phase_data[window] = {name: whole.loc[start:end] for name, (start, end) in phases.items()}
        for feature in FEATURES:
            model = fit_control_model(phase_data[window]["development"], feature)
            models[f"{window}|{feature}"] = model
            for phase, data in phase_data[window].items():
                actual = data[feature].to_numpy()
                fitted = predict_control_model(data, model)
                sst = np.sum((actual - actual.mean()) ** 2)
                if sst <= 1e-20:
                    raise ValueError("Constant feature: R2 undefined")
                fit_rows.append({"window": window, "phase": phase, "feature": feature, "n": len(data),
                                 "r2": float(1 - np.sum((actual - fitted) ** 2) / sst),
                                 "rmse": float(np.sqrt(np.mean((actual - fitted) ** 2)))})
                predictions.append(pd.DataFrame({"date": data.index, "window": window, "phase": phase,
                                                "feature": feature, "actual": actual, "fitted": fitted,
                                                "residual": actual - fitted}))
                for control in CONTROLS:
                    corr_rows.append({"window": window, "phase": phase, "feature": feature, "control": control,
                                      "spearman": float(data[feature].corr(data[control], method="spearman")), "n": len(data)})
    for window in windows:
        if window == primary_window:
            continue
        for phase in phases:
            alt, primary = phase_data[window][phase], phase_data[primary_window][phase]
            if not alt.index.equals(primary.index):
                raise ValueError("Unequal feature calendars")
            for feature in FEATURES:
                stability_rows.append({"window": window, "primary_window": primary_window, "phase": phase,
                                       "feature": feature, "n": len(alt),
                                       "spearman": float(alt[feature].corr(primary[feature], method="spearman"))})
    return (pd.DataFrame(corr_rows), pd.DataFrame(fit_rows), pd.DataFrame(stability_rows),
            models, pd.concat(predictions, ignore_index=True))


def diagram_stability(snapshots, distances, primary_window):
    rows = []
    for key, snapshot in snapshots.items():
        if snapshot["window"] == primary_window:
            continue
        primary_key = f"{snapshot['date']}|{primary_window}"
        bound = float(np.max(np.abs(distances[key] - distances[primary_key])))
        for dimension in ("h0", "h1"):
            a = np.asarray(snapshot[dimension]).reshape(-1, 2)
            b = np.asarray(snapshots[primary_key][dimension]).reshape(-1, 2)
            observed = float(bottleneck(a, b))
            if observed > bound + 2e-6:
                raise ValueError("Persistence stability bound failed beyond float tolerance")
            rows.append({"date": snapshot["date"], "window": snapshot["window"],
                         "primary_window": primary_window, "dimension": dimension,
                         "bottleneck_distance": observed, "max_distance_change": bound})
    return pd.DataFrame(rows)


def run_topology(root, dataset):
    from .data import simple_returns
    root = Path(root)
    p, h = load_topology_protocol(root), load_protocol(root)
    if dataset.metadata["input_sha256"] != p["input_sha256"]:
        raise ValueError("Input vintage differs from the frozen topology protocol")
    if version("ripser") != "0.6.14":
        raise ValueError("Install the pinned ripser version before reproducing this milestone")
    returns, market = simple_returns(dataset)
    if returns.index.max() >= pd.Timestamp(h["phases"]["final_holdout"][0]):
        raise ValueError("Reserved holdout observations are forbidden")
    phases = {name: h["phases"][name] for name in p["allowed_phases"]}
    mask = np.zeros(len(returns), dtype=bool)
    for start, end in phases.values():
        mask |= (returns.index >= pd.Timestamp(start)) & (returns.index <= pd.Timestamp(end))
    dates = returns.index[mask]
    monthly = pd.Series(dates, index=dates).resample("ME").last().dropna()
    started = perf_counter()
    frame, snapshots, distances = rolling_features(returns, market, p["windows"], dates, monthly)
    computation_seconds = perf_counter() - started
    correlations, fits, windows, models, predictions = evaluate_features(frame, phases, p["primary_window"])
    checks = diagram_stability(snapshots, distances, p["primary_window"])
    out = root / "outputs/topology"
    out.mkdir(parents=True, exist_ok=True)
    tables = {"features.csv": frame, "control-correlations.csv": correlations, "control-model-scores.csv": fits,
              "window-sensitivity.csv": windows, "control-model-predictions.csv": predictions,
              "diagram-stability.csv": checks}
    for filename, table in tables.items():
        table.to_csv(out / filename, index=filename == "features.csv", float_format="%.12g")
    (out / "control-models.json").write_text(json.dumps(models, indent=2) + "\n")
    (out / "monthly-diagrams.json").write_text(json.dumps(snapshots, indent=2) + "\n")
    manifest = {"protocol_sha256": sha256(root / "protocol/topology-features-v1.json"),
                "input_sha256": p["input_sha256"], "generated_utc": datetime.now(timezone.utc).isoformat(),
                "feature_rows": len(frame), "dates_per_window": len(dates), "windows": p["windows"],
                "first_date": str(dates[0].date()), "last_date": str(dates[-1].date()),
                "monthly_snapshots_per_window": len(monthly), "diagram_bound_checks": len(checks),
                "feature_computation_seconds": computation_seconds,
                "phases": list(phases), "final_holdout_acquired_or_evaluated": False,
                "control_model_fitting": "Development only; validation is a descriptive transfer check; no return target",
                "versions": {name: version(name) for name in ("numpy", "pandas", "scipy", "ripser", "persim", "scikit-learn", "plotly")},
                "files": {name: sha256(out / name) for name in [*tables, "control-models.json", "monthly-diagrams.json"]}}
    (out / "run-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return frame, manifest
