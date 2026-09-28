"""Frozen historical protocol, auditable data acquisition and phase isolation."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from .config import ResearchConfig
from .data import Dataset, validate_prices, simple_returns
from .portfolio import neutral_weights
from .backtest import execute_targets


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_protocol(root):
    path = Path(root) / "protocol/historical-v1.json"
    lock = json.loads((path.parent / "historical-v1.lock.json").read_text())
    if sha256(path) != lock["sha256"]:
        raise ValueError("Protocol differs from its frozen hash; create a documented revision")
    p = json.loads(path.read_text())
    tickers = [ticker for group in p["groups"].values() for ticker in group]
    if len(tickers) != len(set(tickers)) or p["benchmark"] in tickers:
        raise ValueError("Duplicate asset or benchmark in trading universe")
    if pd.Timestamp(p["download_end_exclusive"]) > pd.Timestamp(p["phases"]["final_holdout"][0]):
        raise ValueError("Acquisition would enter the reserved final holdout")
    return p


def parse_chart(payload, ticker, start, end):
    """Strip current quote metadata; retain only requested historical observations."""
    chart = payload.get("chart", {})
    if chart.get("error") or not chart.get("result"):
        raise ValueError(f"Provider returned no usable chart for {ticker}")
    item = chart["result"][0]
    meta = item["meta"]
    if meta.get("symbol") != ticker or meta.get("currency") != "USD":
        raise ValueError(f"Unexpected identity or currency for {ticker}")
    dates = pd.to_datetime(item["timestamp"], unit="s", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
    quote = item["indicators"]["quote"][0]
    adjusted = item["indicators"].get("adjclose", [])
    if not adjusted:
        raise ValueError(f"No adjusted close supplied for {ticker}")
    frame = pd.DataFrame({"adjclose": adjusted[0]["adjclose"], "close": quote["close"],
                          "volume": quote["volume"]}, index=dates)
    frame.index.name = "date"
    if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError(f"Duplicate or unordered dates for {ticker}")
    if not len(frame) or frame.index.min() < pd.Timestamp(start) or frame.index.max() >= pd.Timestamp(end):
        raise ValueError(f"Provider bars outside permitted acquisition window for {ticker}")
    if not np.isfinite(frame.to_numpy(dtype=float)).all() or (frame <= 0).any().any():
        raise ValueError(f"Missing, nonpositive price or volume for {ticker}")
    events = []
    for kind, values in item.get("events", {}).items():
        for event in values.values():
            date = pd.Timestamp(event["date"], unit="s", tz="UTC").tz_convert("America/New_York").date().isoformat()
            if start <= date < end:
                events.append({"kind": kind, "date": date,
                               **{k: v for k, v in event.items() if k != "date"}})
    return frame, {"symbol": ticker, "currency": meta["currency"],
                   "exchange": meta.get("exchangeName"), "events": events}


def fetch_dataset(root):
    """Acquire only development/validation bars. Cache permits offline replay."""
    root = Path(root)
    p = load_protocol(root)
    cache = root / "data/cache"
    cache.mkdir(parents=True, exist_ok=True)
    tickers = [t for group in p["groups"].values() for t in group] + [p["benchmark"]]
    start, end = p["download_start"], p["download_end_exclusive"]
    period = lambda d: int(pd.Timestamp(d, tz="UTC").timestamp())
    params = urllib.parse.urlencode({"period1": period(start), "period2": period(end),
                                    "interval": "1d", "events": "div,splits"})

    def one(ticker):
        file = cache / f"{ticker}.csv"
        info = cache / f"{ticker}.json"
        if file.exists() and info.exists():
            metadata = json.loads(info.read_text())
            if metadata["csv_sha256"] != sha256(file) or metadata["requested_start"] != start or metadata["requested_end_exclusive"] != end:
                raise ValueError(f"Cached data hash or period mismatch: {ticker}")
            return metadata
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?{params}"
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=40) as response:
            raw = response.read()
        frame, metadata = parse_chart(json.loads(raw), ticker, start, end)
        frame.to_csv(file, float_format="%.17g")
        metadata.update({"source_url": url, "requested_start": start, "requested_end_exclusive": end,
                         "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                         "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
                         "csv_sha256": sha256(file), "rows": len(frame),
                         "retained_metadata": "Current quote fields excluded; historical bars and in-range events only"})
        info.write_text(json.dumps(metadata, indent=2))
        return metadata

    with ThreadPoolExecutor(max_workers=4) as pool:
        metadata = list(pool.map(one, tickers))
    manifest = {"protocol_sha256": sha256(root / "protocol/historical-v1.json"),
                "provider": p["provider"], "field": p["field"],
                "final_holdout_bars_acquired": False, "files": metadata}
    (root / "data/download-manifest.json").write_text(json.dumps(manifest, indent=2))
    return assemble_dataset(root)


def assemble_dataset(root):
    root = Path(root)
    p = load_protocol(root)
    tickers = [t for group in p["groups"].values() for t in group] + [p["benchmark"]]
    frames, metadata = {}, {}
    for ticker in tickers:
        path = root / "data/cache" / f"{ticker}.csv"
        info = json.loads(path.with_suffix(".json").read_text())
        if sha256(path) != info["csv_sha256"]:
            raise ValueError(f"Frozen input changed: {ticker}")
        frame = pd.read_csv(path, index_col="date", parse_dates=True)
        if frame.index.max() >= pd.Timestamp(p["phases"]["final_holdout"][0]):
            raise ValueError("Final-holdout bars are not permitted in this milestone")
        if not frame.index.is_unique or not frame.index.is_monotonic_increasing or not np.isfinite(frame.to_numpy()).all() or (frame <= 0).any().any():
            raise ValueError(f"Invalid cached observations: {ticker}")
        frames[ticker], metadata[ticker] = frame, info
    sessions = frames[p["benchmark"]].index
    for ticker, frame in frames.items():
        if not frame.index.equals(sessions):
            raise ValueError(f"{ticker} dates do not exactly match benchmark sessions; no automatic deletion or filling")
    prices = pd.DataFrame({t: frames[t].adjclose for t in tickers[:-1]})
    market = frames[p["benchmark"]].adjclose.rename(p["benchmark"])
    validate_prices(prices, market)
    rows = []
    for ticker, frame in frames.items():
        unchanged = frame.adjclose.eq(frame.adjclose.shift())
        runs = unchanged.groupby((~unchanged).cumsum()).sum()
        adjusted_returns = frame.adjclose.pct_change(fill_method=None)
        rows.append({"ticker": ticker, "rows": len(frame), "first_date": str(frame.index[0].date()),
                     "last_date": str(frame.index[-1].date()), "missing": int(frame.isna().sum().sum()),
                     "nonpositive_volume": int((frame.volume <= 0).sum()),
                     "max_unchanged_run": int(runs.max()),
                     "moves_above_40pct": int((adjusted_returns.abs() > .4).sum()),
                     "min_20d_dollar_volume_proxy": float((frame.close * frame.volume).rolling(20).mean().min()),
                     "dividend_events": sum(e["kind"] == "dividends" for e in metadata[ticker]["events"]),
                     "split_events": sum(e["kind"] == "splits" for e in metadata[ticker]["events"])})
    audit = pd.DataFrame(rows).set_index("ticker")
    output = root / "outputs/historical"
    output.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output / "data-audit.csv")
    processed = root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    prices.join(market).to_csv(processed / "adjusted-prices.csv", float_format="%.17g")
    return Dataset(prices, market, {"data_kind": "HISTORICAL / FIXED SURVIVOR BASKET",
                                    "provider": p["provider"], "input_sha256": sha256(processed / "adjusted-prices.csv"),
                                    "protocol_sha256": sha256(root / "protocol/historical-v1.json")}), audit


def baseline_decisions(returns, market, config):
    """Baseline only: do not select a model using graph-strategy results."""
    weights = pd.DataFrame(0., index=returns.index, columns=returns.columns)
    betas = pd.DataFrame(np.nan, index=returns.index, columns=returns.columns)
    r, m = returns.to_numpy(), market.to_numpy()
    for t in range(config.warmup - 1, len(r)):
        history = r[t + 1 - config.beta_window:t + 1]
        benchmark = m[t + 1 - config.beta_window:t + 1]
        centered = benchmark - benchmark.mean()
        variance_sum = centered @ centered
        if variance_sum <= 1e-14:
            raise ValueError("Benchmark variance too small")
        beta = (history - history.mean(axis=0)).T @ centered / variance_sum
        volatility = r[t + 1 - config.volatility_window:t + 1].std(axis=0, ddof=1)
        if (volatility <= 1e-12).any():
            raise ValueError("A constant stock return series needs an explicit eligibility rule")
        shock = np.log1p(r[t + 1 - config.signal_window:t + 1]).sum(axis=0)
        shock = np.clip(shock / (volatility * np.sqrt(config.signal_window)), -5, 5)
        weights.iloc[t] = neutral_weights(-shock, beta, config.gross_limit, config.position_limit)
        betas.iloc[t] = beta
    return weights, betas


def phase_inputs(returns, weights, betas, protocol, phase):
    """Shift before slicing: first execution can use the prior session's decision."""
    if phase not in protocol["allowed_phases"]:
        raise ValueError("Phase is reserved and unavailable in this milestone")
    start, end = protocol["phases"][phase]
    execution = weights.shift(1, fill_value=0.)
    exposure = betas.shift(1)
    mask = (returns.index >= pd.Timestamp(start)) & (returns.index <= pd.Timestamp(end))
    if mask.sum() < 2 or exposure.loc[mask].isna().any().any():
        raise ValueError("Insufficient warm-up for phase start")
    return returns.loc[mask], execution.loc[mask], exposure.loc[mask]


def phase_metrics(result, market, config):
    ledger = result.ledger
    net = ledger.net_return
    growth = np.r_[1., np.cumprod(1 + net.to_numpy())]
    peak = np.maximum.accumulate(growth)
    m = market.loc[net.index]
    return {"days": len(net), "total_return": float(growth[-1] - 1),
            "annualised_return": float(growth[-1] ** (252 / len(net)) - 1),
            "annualised_volatility": float(net.std(ddof=1) * np.sqrt(252)),
            "sharpe_zero_cash_rate": float(net.mean() / net.std(ddof=1) * np.sqrt(252)),
            "maximum_drawdown": float((growth / peak - 1).min()),
            "realized_market_beta": float(np.cov(net, m, ddof=1)[0, 1] / m.var(ddof=1)),
            "mean_turnover": float(ledger.turnover.mean()),
            "mean_gross_exposure": float(ledger.gross_exposure.mean()),
            "trading_cost": float(ledger.trading_cost.sum()), "borrow_cost": float(ledger.borrow_cost.sum()),
            "max_abs_net_exposure": float(ledger.net_exposure.abs().max()),
            "max_abs_estimated_beta": float(ledger.estimated_beta_exposure.abs().max()),
            "max_position": float(ledger.max_position.max())}


def evaluate_baseline(root, dataset):
    root = Path(root)
    p = load_protocol(root)
    config = ResearchConfig(**p["config"])
    returns, market = simple_returns(dataset)
    weights, betas = baseline_decisions(returns, market, config)
    out = root / "outputs/historical"
    out.mkdir(parents=True, exist_ok=True)
    rows, results = [], {}
    for phase in p["allowed_phases"]:
        r, w, beta = phase_inputs(returns, weights, betas, p, phase)
        for fee in p["cost_scenarios_bps"]:
            scenario = replace(config, trading_cost_bps=fee)
            result = execute_targets(r, w, scenario, beta, liquidate_at_end=True)
            metrics = phase_metrics(result, market, scenario)
            rows.append({"phase": phase, "trading_cost_bps": fee, **metrics})
            result.ledger.to_csv(out / f"{phase}-{fee:g}bps-ledger.csv", float_format="%.12g")
            if fee == config.trading_cost_bps:
                results[phase] = result
                result.execution_weights.to_csv(out / f"{phase}-weights.csv", float_format="%.12g")
    summary = pd.DataFrame(rows)
    summary.to_csv(out / "baseline-summary.csv", index=False, float_format="%.12g")
    manifest = {"protocol": p["protocol_id"], "protocol_sha256": dataset.metadata["protocol_sha256"],
                "input_sha256": dataset.metadata["input_sha256"], "phases_evaluated": p["allowed_phases"],
                "final_holdout_evaluated": False, "graph_performance_evaluated": False,
                "parameter_searches": 0, "cost_scenarios": p["cost_scenarios_bps"],
                "baseline": "Identical score and portfolio rule to Milestone 1; historical input substituted",
                "phase_boundary": "Each phase starts flat with fresh capital; last close liquidates"}
    (out / "run-manifest.json").write_text(json.dumps(manifest, indent=2))
    return results, summary
