"""Synthetic fixtures and strict price-data ingestion; never forward-fill."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from .config import ResearchConfig


@dataclass
class Dataset:
    prices: pd.DataFrame
    market: pd.Series
    metadata: dict


def validate_prices(prices, market):
    if not isinstance(prices, pd.DataFrame) or prices.shape[1] < 4:
        raise ValueError("At least four assets are required")
    if not isinstance(prices.index, pd.DatetimeIndex) or prices.index.hasnans:
        raise ValueError("Use a valid DatetimeIndex")
    if not prices.index.is_unique or not prices.index.is_monotonic_increasing:
        raise ValueError("Dates must be unique and strictly increasing")
    if not prices.columns.is_unique or not prices.index.equals(market.index):
        raise ValueError("Unique assets and exactly aligned benchmark dates required")
    values = np.column_stack([prices.to_numpy(dtype=float), market.to_numpy(dtype=float)])
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Prices must be finite and positive; missing prices need an explicit policy")
    if len(prices) < 4:
        raise ValueError("Too few price rows")


def generate_synthetic(config=ResearchConfig()):
    """Artificial factors and mean-reverting mispricing; not historical equities."""
    rng = np.random.default_rng(config.seed)
    t, n = config.observations, config.assets
    sector_id = np.arange(n) % config.sectors
    true_beta = np.linspace(0.65, 1.45, n)
    stress = np.zeros(t, dtype=bool)
    stress[int(0.55 * t):int(0.70 * t)] = True
    market_log = rng.normal(size=t) * np.where(stress, 0.018, 0.008) + 0.0001
    sector_log = rng.normal(size=(t, config.sectors)) * 0.007
    state = np.zeros((t + 1, n))
    innovations = rng.normal(size=(t, n)) * 0.007
    for day in range(t):
        state[day + 1] = 0.92 * state[day] + innovations[day]
    stock_log = (market_log[:, None] * true_beta
                 + 0.55 * sector_log[:, sector_id]
                 + np.diff(state, axis=0)
                 + rng.normal(size=(t, n)) * 0.004)
    dates = pd.bdate_range("2020-01-02", periods=t + 1, name="date")
    names = [f"SYN{i + 1:02d}" for i in range(n)]
    prices = pd.DataFrame(100 * np.exp(np.vstack([np.zeros(n), np.cumsum(stock_log, axis=0)])),
                          index=dates, columns=names)
    market = pd.Series(100 * np.exp(np.r_[0, np.cumsum(market_log)]),
                       index=dates, name="SYN_MARKET")
    metadata = {
        "data_kind": "SYNTHETIC — NOT HISTORICAL MARKET DATA",
        "seed": config.seed,
        "calendar": "Synthetic weekdays; no exchange-holiday calendar",
        "construction": "Market and sector factors plus deliberately mean-reverting latent mispricing",
        "stress_start": str(dates[int(0.55 * t) + 1].date()),
        "stress_end": str(dates[int(0.70 * t)].date()),
        "sectors": {name: f"Sector {sector_id[i] + 1}" for i, name in enumerate(names)},
        "warning": "Fixture design favours reversal hypotheses. Performance is not evidence of tradable alpha.",
    }
    validate_prices(prices, market)
    return Dataset(prices, market, metadata)


def load_prices_csv(path, benchmark):
    """Read date, benchmark and asset columns. Provider adjustment policy is external."""
    frame = pd.read_csv(Path(path))
    if "date" not in frame or benchmark not in frame:
        raise ValueError("CSV needs date, the named benchmark, and asset columns")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame = frame.set_index("date")
    market = frame.pop(benchmark)
    validate_prices(frame, market)
    return Dataset(frame, market, {
        "data_kind": "USER-SUPPLIED DATA — PROVENANCE NOT VERIFIED",
        "input_file": Path(path).name,
        "benchmark": benchmark,
        "warning": "Verify total-return adjustments, point-in-time universe, missingness and execution prices before interpreting results.",
    })


def simple_returns(dataset):
    validate_prices(dataset.prices, dataset.market)
    return (dataset.prices.pct_change(fill_method=None).iloc[1:],
            dataset.market.pct_change(fill_method=None).iloc[1:])
