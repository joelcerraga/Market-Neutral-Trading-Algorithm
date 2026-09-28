"""Daily close ledger, delayed execution, drift-aware costs and final liquidation."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from .config import ResearchConfig


@dataclass
class BacktestResult:
    ledger: pd.DataFrame
    execution_weights: pd.DataFrame
    traded_notionals: pd.DataFrame


def execute_targets(returns, execution_weights, config=ResearchConfig(),
                    execution_betas=None, liquidate_at_end=True):
    """Targets dated t trade at close t, AFTER the day's old-position P&L.

    Public research wrapper below shifts decisions by one close first.
    New target weights refer to NAV after all transaction costs.
    """
    if not returns.index.equals(execution_weights.index) or not returns.columns.equals(execution_weights.columns):
        raise ValueError("Returns and target labels must align exactly")
    if not isinstance(returns.index, pd.DatetimeIndex) or returns.index.hasnans or not returns.index.is_unique or not returns.index.is_monotonic_increasing:
        raise ValueError("A strictly increasing, unique DatetimeIndex is required")
    if not len(returns) or not np.isfinite(returns.to_numpy()).all() or (returns.to_numpy() <= -1).any():
        raise ValueError("Invalid returns")
    if not np.isfinite(execution_weights.to_numpy()).all():
        raise ValueError("Invalid target weights")
    if execution_betas is not None:
        if not returns.index.equals(execution_betas.index) or not returns.columns.equals(execution_betas.columns):
            raise ValueError("Execution beta labels must align exactly")
    weights = execution_weights.copy()
    if liquidate_at_end:
        weights.iloc[-1] = 0.0
    if (weights.abs().sum(axis=1) > config.gross_limit + 1e-8).any() or (weights.abs() > config.position_limit + 1e-8).any().any():
        raise ValueError("Targets exceed configured exposure limits")
    cash, nav = config.initial_capital, config.initial_capital
    notionals = np.zeros(returns.shape[1])
    cost_rate = config.trading_cost_bps / 10_000
    rows, trades = [], []
    for t, date in enumerate(returns.index):
        start_nav = nav
        days = (date - returns.index[t - 1]).total_seconds() / 86400 if t else 0.0
        borrow_cost = np.maximum(-notionals, 0).sum() * config.annual_borrow_rate * days / 365
        pnl = float(notionals @ returns.iloc[t].to_numpy())
        marked = notionals * (1 + returns.iloc[t].to_numpy())
        cash -= borrow_cost
        nav_before_trade = cash + marked.sum()
        if nav_before_trade <= 0:
            raise ValueError("Portfolio insolvent before trading")
        w = weights.iloc[t].to_numpy()
        # Solve NAV_after + fee * traded_dollars = NAV_before.
        def balance(after):
            return after + cost_rate * np.abs(w * after - marked).sum() - nav_before_trade
        if balance(0) >= 0:
            raise ValueError("Cannot fund trading costs")
        nav = float(brentq(balance, 0, nav_before_trade, xtol=1e-10)) if cost_rate else nav_before_trade
        new_notionals = w * nav
        traded = new_notionals - marked
        trade_cost = float(cost_rate * np.abs(traded).sum())
        cash = nav - new_notionals.sum()
        notionals = new_notionals
        beta_exposure = np.nan
        if execution_betas is not None:
            beta = execution_betas.iloc[t].to_numpy()
            if np.isfinite(beta).all():
                beta_exposure = float(w @ beta)
            elif np.abs(w).sum() < 1e-12:
                beta_exposure = 0.0
        rows.append({
            "date": date, "nav": nav, "gross_return": pnl / start_nav,
            "net_return": nav / start_nav - 1, "trading_cost": trade_cost,
            "borrow_cost": borrow_cost, "trading_cost_return": trade_cost / start_nav,
            "borrow_cost_return": borrow_cost / start_nav,
            "traded_notional": float(np.abs(traded).sum()),
            "turnover": float(np.abs(traded).sum() / start_nav),
            "long_exposure": float(np.maximum(w, 0).sum()),
            "short_exposure": float(np.maximum(-w, 0).sum()),
            "gross_exposure": float(np.abs(w).sum()), "net_exposure": float(w.sum()),
            "estimated_beta_exposure": beta_exposure,
            "max_position": float(np.abs(w).max()), "cash": cash,
        })
        trades.append(traded)
    return BacktestResult(pd.DataFrame(rows).set_index("date"), weights,
                          pd.DataFrame(trades, index=returns.index, columns=returns.columns))


def run_backtest(returns, decision_weights, decision_betas, config=ResearchConfig()):
    """Observe close t; execute at close t+1; first P&L at close t+2."""
    executed = decision_weights.shift(1, fill_value=0.0)
    delayed_beta = decision_betas.shift(1)
    return execute_targets(returns, executed, config, delayed_beta, liquidate_at_end=True)


def summarise(result, market, config=ResearchConfig()):
    ledger = result.ledger
    # Exclude the common estimation warm-up; retain entry and liquidation fees.
    evaluation = ledger.iloc[config.warmup:]
    if len(evaluation) < 2:
        raise ValueError("Too little post-warm-up history")
    net = evaluation.net_return
    equity = np.r_[1.0, np.cumprod(1 + net.to_numpy())]
    drawdown = equity / np.maximum.accumulate(equity) - 1
    volatility = net.std(ddof=1)
    m = market.reindex(evaluation.index)
    realized_beta = np.cov(net, m, ddof=1)[0, 1] / m.var(ddof=1) if m.var(ddof=1) > 1e-14 else np.nan
    return {
        "evaluation_days": len(evaluation),
        "total_return": float(equity[-1] - 1),
        "annualised_return": float(equity[-1] ** (config.annualisation / len(net)) - 1),
        "annualised_volatility": float(volatility * np.sqrt(config.annualisation)),
        "sharpe_zero_cash_rate": float(net.mean() / volatility * np.sqrt(config.annualisation)) if volatility > 1e-14 else np.nan,
        "maximum_drawdown": float(drawdown.min()),
        "realized_market_beta": float(realized_beta),
        "mean_turnover": float(evaluation.turnover.mean()),
        "total_trading_cost": float(evaluation.trading_cost.sum()),
        "total_borrow_cost": float(evaluation.borrow_cost.sum()),
        "max_abs_net_exposure": float(evaluation.net_exposure.abs().max()),
        "max_abs_estimated_beta": float(evaluation.estimated_beta_exposure.abs().max()),
        "max_gross_exposure": float(evaluation.gross_exposure.max()),
        "max_position": float(evaluation.max_position.max()),
    }
