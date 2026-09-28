"""Causal daily estimates and two comparable signal definitions."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .config import ResearchConfig
from .graph import correlation_graph, heat_diffusion
from .portfolio import neutral_weights


@dataclass
class Decisions:
    targets: dict
    betas: pd.DataFrame
    diagnostics: pd.DataFrame
    last_graph: dict


def build_decisions(returns, market, config=ResearchConfig()):
    if not returns.index.equals(market.index) or not returns.columns.is_unique:
        raise ValueError("Align returns and benchmark exactly")
    if len(returns) < config.warmup or returns.shape[1] <= config.neighbours:
        raise ValueError("Insufficient history or asset count")
    r, m = returns.to_numpy(dtype=float), market.to_numpy(dtype=float)
    if not np.isfinite(r).all() or not np.isfinite(m).all() or (r <= -1).any() or (m <= -1).any():
        raise ValueError("Returns must be finite and greater than -100%")
    n = returns.shape[1]
    targets = {name: np.zeros_like(r) for name in ("baseline", "graph")}
    betas = np.full_like(r, np.nan)
    diagnostics, last_graph = [], {}
    for t in range(config.warmup - 1, len(r)):
        beta_returns = r[t + 1 - config.beta_window:t + 1]
        market_history = m[t + 1 - config.beta_window:t + 1]
        centered_market = market_history - market_history.mean()
        denominator = centered_market @ centered_market
        if denominator < 1e-14:
            raise ValueError("Benchmark variance is too small to estimate beta")
        beta = (beta_returns - beta_returns.mean(axis=0)).T @ centered_market / denominator
        volatility = r[t + 1 - config.volatility_window:t + 1].std(axis=0, ddof=1)
        if (volatility < 1e-12).any():
            raise ValueError("Constant asset return series: set an explicit universe policy")
        shock = np.log1p(r[t + 1 - config.signal_window:t + 1]).sum(axis=0)
        shock = np.clip(shock / (volatility * np.sqrt(config.signal_window)), -5, 5)
        corr, adjacency, laplacian = correlation_graph(
            r[t + 1 - config.correlation_window:t + 1],
            config.neighbours, config.minimum_correlation)
        smooth = heat_diffusion(shock, laplacian, config.diffusion_time)
        scores = {"baseline": -shock, "graph": -(shock - smooth)}
        betas[t] = beta
        for name, score in scores.items():
            targets[name][t] = neutral_weights(score, beta, config.gross_limit, config.position_limit)
        diagnostics.append({
            "date": returns.index[t],
            "mean_correlation": (corr.sum() - n) / (n * (n - 1)),
            "edges": int((adjacency > 0).sum() // 2),
            "isolated_assets": int((adjacency.sum(axis=1) == 0).sum()),
            "diffusion_residual_norm": float(np.linalg.norm(shock - smooth)),
        })
        last_graph = {"date": str(returns.index[t].date()), "correlation": corr,
                      "adjacency": adjacency, "laplacian": laplacian,
                      "shock": shock, "smooth": smooth}
    frames = {name: pd.DataFrame(value, index=returns.index, columns=returns.columns)
              for name, value in targets.items()}
    return Decisions(frames, pd.DataFrame(betas, index=returns.index, columns=returns.columns),
                     pd.DataFrame(diagnostics).set_index("date"), last_graph)
