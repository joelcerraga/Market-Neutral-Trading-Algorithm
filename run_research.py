"""Run the deterministic synthetic milestone, or explicitly supplied CSV data."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy as np
import pandas as pd
import scipy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from market_neutral.config import ResearchConfig
from market_neutral.data import generate_synthetic, load_prices_csv, simple_returns
from market_neutral.strategy import build_decisions
from market_neutral.backtest import run_backtest, summarise


ROOT = Path(__file__).resolve().parent
COLORS = {"baseline": "#688797", "graph": "#176960"}


def make_figures(results, decisions, dataset, market, destination, config):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "axes.labelcolor": "#243947",
                         "text.color": "#243947", "axes.edgecolor": "#CAD3D8"})
    label = "SYNTHETIC VALIDATION" if dataset.metadata["data_kind"].startswith("SYNTHETIC") else "USER-SUPPLIED DATA / UNVERIFIED"
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.3))
    fig.subplots_adjust(left=.08, right=.975, bottom=.16, top=.82, wspace=.27, hspace=.52)
    fig.suptitle(f"Market-Neutral Trading Algorithm\n{label} · Milestone 1", fontsize=18, ha="left", x=0.045, y=.98)
    for name, result in results.items():
        ledger = result.ledger.iloc[config.warmup:]
        nav = ledger.nav / config.initial_capital
        peak = np.maximum.accumulate(np.r_[1., nav.to_numpy()])[1:]
        axes[0, 0].plot(nav.index, nav, label=name.title(), color=COLORS[name], lw=1.8)
        axes[0, 1].plot(nav.index, 100 * (nav / peak - 1), color=COLORS[name], lw=1.2)
        axes[1, 0].plot(nav.index, ledger.gross_exposure, color=COLORS[name], alpha=0.9)
        rolling_beta = ledger.net_return.rolling(63).cov(market) / market.rolling(63).var()
        axes[1, 1].plot(nav.index, rolling_beta.reindex(nav.index), color=COLORS[name], lw=1.2)
    axes[0, 0].set(title="Net capital, after costs", ylabel="Initial capital = 1")
    axes[0, 0].legend(frameon=False)
    axes[0, 1].set(title="Drawdown", ylabel="% from running peak")
    axes[1, 0].set(title="Gross exposure at each close", ylabel="Long + short / net asset value", ylim=(-0.02, config.gross_limit * 1.1))
    axes[1, 1].set(title="Realised beta can drift from zero", ylabel="63-day beta to synthetic market" if label.startswith("SYNTHETIC") else "63-day beta to supplied benchmark")
    axes[1, 1].axhline(0, color="#8C9BA3", lw=0.8)
    for ax in axes.flat:
        ax.grid(alpha=0.16)
        ax.tick_params(axis="x", labelrotation=20)
    fig.text(0.045, 0.02, "Synthetic fixture deliberately includes mean reversion. These curves validate mechanics; they do not establish market profitability.\nSame timing and cost assumptions for both signals. Final liquidation included." if label.startswith("SYNTHETIC") else "Data provenance is user supplied. Corporate actions, survivorship, borrow availability and executable prices require separate checks.", fontsize=9, color="#5E707D")
    fig.savefig(destination / "01-performance-and-exposures.png", dpi=160)
    plt.close(fig)

    snap = decisions.last_graph
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.4))
    fig.subplots_adjust(left=.07, right=.975, bottom=.23, top=.77, wspace=.32)
    fig.suptitle(f"Graph diffusion: from connected stocks to a relative signal\n{label} · Snapshot {snap['date']}", fontsize=16, ha="left", x=0.035, y=.98)
    matrix = axes[0].imshow(snap["adjacency"], cmap="YlGnBu", vmin=0, vmax=1)
    axes[0].set(title="Weighted stock graph", xlabel="Asset index", ylabel="Asset index")
    fig.colorbar(matrix, ax=axes[0], shrink=0.75, label="Positive return correlation")
    selection = np.arange(min(12, dataset.prices.shape[1]))
    axes[1].bar(selection - .18, snap["shock"][selection], width=.36, color="#688797", label="Observed shock")
    axes[1].bar(selection + .18, snap["smooth"][selection], width=.36, color="#176960", label="Diffused shock")
    axes[1].set_xticks(selection, dataset.prices.columns[selection], rotation=50, ha="right")
    axes[1].set(title="First 12 stocks: observed versus smoothed", ylabel="Volatility-scaled 5-day log return")
    axes[1].axhline(0, color="#8C9BA3", lw=.8)
    axes[1].legend(frameon=False)
    axes[1].grid(axis="y", alpha=.16)
    fig.text(.035, .025, "Graph score = negative of (observed shock − diffused shock). Portfolio constraints are applied after signal construction.", fontsize=9, color="#5E707D")
    fig.savefig(destination / "02-graph-diffusion.png", dpi=160)
    plt.close(fig)


def write_report(summary, out, config, data_kind):
    context = ("This run checks the research implementation. It is not an out-of-sample market study. "
               "The synthetic generator deliberately includes mean reversion, so favourable results cannot establish an investment edge."
               if data_kind.startswith("SYNTHETIC") else
               "This is an exploratory run on user-supplied prices. Data provenance, universe selection, corporate actions "
               "and executable prices have not been verified by this program. No out-of-sample protocol is imposed by this run.")
    lines = ["# Market-Neutral Trading Algorithm", "", "## Milestone 1: validation results", "",
             f"**Data: {data_kind}.**", "",
             context, "",
             "| Measure | Baseline reversal | Graph diffusion |", "| --- | ---: | ---: |"]
    metrics = [("total_return", "Simulated total return", ".2%"),
               ("sharpe_zero_cash_rate", "Simulated Sharpe (zero cash rate)", ".2f"),
               ("maximum_drawdown", "Simulated maximum drawdown", ".2%"),
               ("realized_market_beta", "Realised market beta", ".4f"),
               ("mean_turnover", "Mean daily traded notional / start NAV", ".2%"),
               ("total_trading_cost", "Trading costs, capital units", ",.2f"),
               ("total_borrow_cost", "Borrow costs, capital units", ",.2f"),
               ("max_abs_net_exposure", "Largest absolute net dollar exposure", ".2e"),
               ("max_abs_estimated_beta", "Largest absolute estimated beta exposure", ".2e"),
               ("max_gross_exposure", "Largest gross exposure", ".2%"),
               ("max_position", "Largest single position", ".2%")]
    for key, label, fmt in metrics:
        lines.append(f"| {label} | {format(summary.loc['baseline', key], fmt)} | {format(summary.loc['graph', key], fmt)} |")
    lines.extend(["", "## Interpretation", "",
                  "Neutrality holds against the lagged beta estimate at each rebalance. "
                  "It does not imply zero future market covariance, sector exposure, intraday exposure or drawdown. "
                  "Performance metrics exclude the common estimation warm-up and include entry and terminal liquidation costs.", "",
                  f"Assumptions: {config.trading_cost_bps:g} bps per dollar bought or sold; "
                  f"{config.annual_borrow_rate:.0%} annual borrow on short notional, ACT/365; "
                  f"{config.gross_limit:.0%} gross limit; {config.position_limit:.0%} name limit. "
                  "Cash interest and financing rebates are zero. Fee settings are examples, not broker quotes.", "",
                  "## Next research gate", "",
                  "Choose and document a historical data source, point-in-time universe, adjustment convention, "
                  "calendar and liquidity rules. Freeze a chronological evaluation plan before inspecting results. "
                  "Only then compare the two signals on market data and add persistent-homology regime features.", ""])
    (out / "milestone-1-results.md").write_text("\n".join(lines), encoding="utf-8")


def run(config=ResearchConfig(), output=None, dataset=None):
    dataset = generate_synthetic(config) if dataset is None else dataset
    out = Path(output) if output is not None else ROOT / "outputs" / "synthetic"
    out.mkdir(parents=True, exist_ok=True)
    returns, market = simple_returns(dataset)
    decisions = build_decisions(returns, market, config)
    results, metrics = {}, {}
    for name, target in decisions.targets.items():
        result = run_backtest(returns, target, decisions.betas, config)
        results[name] = result
        metrics[name] = summarise(result, market, config)
        result.ledger.to_csv(out / f"{name}-ledger.csv", float_format="%.12g")
        result.execution_weights.to_csv(out / f"{name}-weights.csv", float_format="%.12g")
        result.traded_notionals.to_csv(out / f"{name}-trades.csv", float_format="%.12g")
    summary = pd.DataFrame(metrics).T
    summary.index.name = "strategy"
    summary.to_csv(out / "summary.csv", float_format="%.12g")
    decisions.diagnostics.to_csv(out / "graph-diagnostics.csv", float_format="%.12g")
    decisions.betas.to_csv(out / "decision-betas.csv", float_format="%.12g")
    data_csv = dataset.prices.join(dataset.market).to_csv(float_format="%.17g")
    (out / "input-prices.csv").write_text(data_csv, encoding="utf-8")
    metadata = {"config": asdict(config), "dataset": dataset.metadata,
                "input_sha256": hashlib.sha256(data_csv.encode()).hexdigest(),
                "python": platform.python_version(),
                "versions": {"numpy": np.__version__, "pandas": pd.__version__,
                             "scipy": scipy.__version__, "matplotlib": matplotlib.__version__},
                "timing": "Decide close t; execute close t+1; first P&L close t+2",
                "status": "Research milestone; no live execution or empirical alpha claim"}
    (out / "run-manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    make_figures(results, decisions, dataset, market, out, config)
    write_report(summary, out, config, dataset.metadata["data_kind"])
    return dataset, decisions, results, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prices", type=Path, help="Optional date + benchmark + asset price CSV")
    parser.add_argument("--benchmark", help="Required column name when --prices is supplied")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prices and not args.benchmark:
        parser.error("--benchmark is required with --prices")
    if args.benchmark and not args.prices:
        parser.error("--benchmark requires --prices")
    data = load_prices_csv(args.prices, args.benchmark) if args.prices else None
    out = args.output or ROOT / "outputs" / ("supplied-data" if data else "synthetic")
    _, _, _, summary = run(output=out, dataset=data)
    print("SYNTHETIC VALIDATION — not historical performance" if data is None else "USER-SUPPLIED DATA — provenance not verified")
    print(summary[["max_abs_net_exposure", "max_abs_estimated_beta", "max_gross_exposure", "max_position"]].to_string())
    print(f"Research outputs written to {out.resolve()}")


if __name__ == "__main__":
    main()
