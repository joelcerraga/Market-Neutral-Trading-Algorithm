"""Explicit release, separate cache and vintage audit for the reserved test."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import urllib.parse
import urllib.request
import numpy as np
import pandas as pd
from .final_io import write_csv_verified
from .data import Dataset, validate_prices
from .historical import parse_chart, sha256


def load_final_protocol(root):
    root = Path(root)
    path = root / "protocol/final-evaluation-v1.json"
    lock = json.loads(path.with_suffix(".lock.json").read_text())
    if sha256(path) != lock["sha256"]:
        raise ValueError("Final protocol differs from its pre-acquisition lock")
    p = json.loads(path.read_text())
    if not p["holdout_release"] or p["test_period"] != ["2020-01-01", "2025-12-31"]:
        raise ValueError("Final-test release is absent or its period changed")
    for name, expected in p["previous_protocols"].items():
        if sha256(root / "protocol" / f"{name}.json") != expected:
            raise ValueError(f"Previous protocol changed: {name}")
    for relative, expected in p["frozen_source_sha256"].items():
        if sha256(root / relative) != expected:
            raise ValueError(f"Frozen calculation changed: {relative}")
    if sha256(root / "outputs/topology/control-models.json") != p["topology_control_models_sha256"]:
        raise ValueError("Development-only topology models changed")
    if sha256(root / "data/processed/adjusted-prices.csv") != p["original_input_sha256"]:
        raise ValueError("Original study observations changed")
    return p


def overlap_audit(original, latest, tolerance):
    """Return-space audit permits a constant adjustment factor, never a splice."""
    if not original.index.equals(latest.index):
        raise ValueError("Warm-up overlap calendars differ")
    old = original.pct_change(fill_method=None).iloc[1:]
    new = latest.pct_change(fill_method=None).iloc[1:]
    difference = (new - old).abs()
    maximum = float(difference.max())
    ratios = latest / original
    result = {"overlap_returns": len(difference), "max_abs_overlap_return_change": maximum,
              "median_adjusted_price_ratio": float(ratios.median()),
              "min_adjusted_price_ratio": float(ratios.min()), "max_adjusted_price_ratio": float(ratios.max())}
    if not np.isfinite(difference).all() or maximum > tolerance:
        raise ValueError(f"Warm-up return revision {maximum:.9g} exceeds frozen tolerance {tolerance}")
    return result


def fetch_final_dataset(root):
    root = Path(root)
    p = load_final_protocol(root)
    out = root / "outputs/final"
    cache = root / p["cache"]
    out.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
    release = out / "holdout-release.json"
    if not release.exists():
        release.write_text(json.dumps({"protocol_sha256":sha256(root / "protocol/final-evaluation-v1.json"),
            "release_started_utc":datetime.now(timezone.utc).isoformat(),
            "meaning":"Acquisition starts after the local protocol lock. The test is subsequently observed and cannot be reused as untouched."},indent=2)+"\n")
    tickers = [t for stocks in p["universe"].values() for t in stocks] + [p["benchmark"]]
    start, end = p["download_start"], p["download_end_exclusive"]
    timestamp = lambda date: int(pd.Timestamp(date,tz="UTC").timestamp())
    params = urllib.parse.urlencode({"period1":timestamp(start),"period2":timestamp(end),"interval":"1d","events":"div,splits"})

    def one(ticker):
        file = cache / f"{ticker}.csv"
        info = file.with_suffix(".json")
        if file.exists() or info.exists():
            if not file.exists() or not info.exists():
                raise ValueError(f"Incomplete cache pair: {ticker}; inspect before reacquisition")
            metadata = json.loads(info.read_text())
            if (metadata["csv_sha256"] != sha256(file) or metadata["requested_start"] != start
                    or metadata["requested_end_exclusive"] != end):
                raise ValueError(f"Final cache hash/period mismatch: {ticker}")
            return metadata
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?{params}"
        request = urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(request,timeout=40) as response:
            raw = response.read()
        frame, metadata = parse_chart(json.loads(raw),ticker,start,end)
        write_csv_verified(frame,file,float_format="%.17g")
        metadata.update({"source_url":url,"requested_start":start,"requested_end_exclusive":end,
                         "retrieved_utc":datetime.now(timezone.utc).isoformat(),
                         "raw_response_sha256":hashlib.sha256(raw).hexdigest(),"csv_sha256":sha256(file),
                         "rows":len(frame),"retained_metadata":"Historical bars and in-range events; current quote fields excluded"})
        info.write_text(json.dumps(metadata,indent=2)+"\n")
        return metadata

    with ThreadPoolExecutor(max_workers=4) as pool:
        metadata = list(pool.map(one,tickers))
    manifest = {"protocol_sha256":sha256(root / "protocol/final-evaluation-v1.json"),
                "test_period_released":p["test_period"],"provider":p["provider"],"field":p["field"],
                "files":metadata}
    (root / "data/final-download-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return assemble_final_dataset(root)


def assemble_final_dataset(root):
    """Audit every input before a single final strategy evaluation is allowed."""
    root = Path(root); p = load_final_protocol(root)
    tickers = [t for stocks in p["universe"].values() for t in stocks] + [p["benchmark"]]
    frames, rows = {}, []
    overlap_start, overlap_end = p["data_review"]["overlap_period"]
    for ticker in tickers:
        path = root / p["cache"] / f"{ticker}.csv"
        metadata = json.loads(path.with_suffix(".json").read_text())
        if (sha256(path) != metadata["csv_sha256"] or metadata["requested_start"] != p["download_start"]
                or metadata["requested_end_exclusive"] != p["download_end_exclusive"]):
            raise ValueError(f"Invalid final snapshot: {ticker}")
        frame = pd.read_csv(path,index_col="date",parse_dates=True)
        if (not frame.index.is_unique or not frame.index.is_monotonic_increasing
                or not np.isfinite(frame.to_numpy()).all() or (frame <= 0).any().any()):
            raise ValueError(f"Missing, unordered, duplicate or nonpositive final observations: {ticker}")
        if (frame.index.min() < pd.Timestamp(p["download_start"])
                or frame.index.max() >= pd.Timestamp(p["download_end_exclusive"])):
            raise ValueError(f"Observations outside released range: {ticker}")
        original_path = root / "data/cache" / f"{ticker}.csv"
        old_metadata = json.loads(original_path.with_suffix(".json").read_text())
        if sha256(original_path) != old_metadata["csv_sha256"]:
            raise ValueError(f"Original cached series changed: {ticker}")
        original = pd.read_csv(original_path,index_col="date",parse_dates=True).adjclose.loc[overlap_start:overlap_end]
        overlap = overlap_audit(original,frame.adjclose.loc[overlap_start:overlap_end],
                                p["data_review"]["overlap_max_abs_daily_return_difference"])
        moves = frame.adjclose.pct_change(fill_method=None).abs()
        flags = int((moves > p["data_review"]["absolute_daily_return_flag"]).sum())
        if flags:
            raise ValueError(f"Large adjusted return flagged for review before evaluation: {ticker}")
        frames[ticker] = frame
        rows.append({"ticker":ticker,"rows":len(frame),"first_date":str(frame.index[0].date()),
                     "last_date":str(frame.index[-1].date()),"missing":int(frame.isna().sum().sum()),
                     "nonpositive_volume":int((frame.volume<=0).sum()),"moves_above_40pct":flags,
                     "largest_abs_adjusted_return":float(moves.max()),
                     "dividend_events":sum(e["kind"]=="dividends" for e in metadata["events"]),
                     "split_events":sum(e["kind"]=="splits" for e in metadata["events"]),**overlap})
    sessions = frames[p["benchmark"]].index
    for ticker, frame in frames.items():
        if not frame.index.equals(sessions):
            raise ValueError(f"Final calendar mismatch: {ticker}; no automatic deletion or filling")
    if sessions[0] != pd.Timestamp("2018-12-31") or sessions[-1] != pd.Timestamp("2025-12-31"):
        raise ValueError("Incomplete declared history endpoints")
    prices = pd.DataFrame({t:frames[t].adjclose for t in tickers[:-1]})
    market = frames[p["benchmark"]].adjclose.rename(p["benchmark"])
    validate_prices(prices,market)
    out = root / "outputs/final"; out.mkdir(parents=True,exist_ok=True)
    audit = pd.DataFrame(rows).set_index("ticker")
    write_csv_verified(audit,out / "data-audit.csv",float_format="%.12g")
    processed = root / "data/final-processed"; processed.mkdir(parents=True,exist_ok=True)
    path = processed / "adjusted-prices.csv"
    write_csv_verified(prices.join(market),path,float_format="%.17g")
    snapshot_lock = root / "data/final-snapshot.lock.json"
    digest = sha256(path)
    if snapshot_lock.exists():
        locked = json.loads(snapshot_lock.read_text())
        if locked["input_sha256"] != digest:
            raise ValueError("Final data vintage differs from its retained snapshot; document a new experiment")
    else:
        earlier_run = out / "run-manifest.json"
        if earlier_run.exists() and json.loads(earlier_run.read_text())["input_sha256"] != digest:
            raise ValueError("Final data differ from the first recorded evaluation")
        snapshot_lock.write_text(json.dumps({"input_sha256":digest,
            "recorded_utc":datetime.now(timezone.utc).isoformat(),
            "protocol_sha256":sha256(root / "protocol/final-evaluation-v1.json"),
            "scope":"Exact audited price vintage for subsequent replay; separate from the pre-acquisition protocol lock"},indent=2)+"\n")
    return Dataset(prices,market,{"data_kind":"RESERVED HISTORICAL TEST / FIXED SURVIVOR BASKET",
        "provider":p["provider"],"input_sha256":digest,
        "protocol_sha256":sha256(root / "protocol/final-evaluation-v1.json")}), audit
