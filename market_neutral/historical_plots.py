"""Static research figures and a standalone interactive correlation explorer."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from .data import simple_returns


def figures(root, dataset, results, summary):
    root = Path(root)
    out = root / "outputs/historical"
    colors = {"development": "#557787", "validation": "#176960"}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "text.color": "#203440"})
    fig, ax = plt.subplots(2, 2, figsize=(11.7, 7.4))
    fig.subplots_adjust(left=.08, right=.97, bottom=.13, top=.82, hspace=.5, wspace=.28)
    fig.suptitle("Historical baseline: development and validation", x=.055, y=.98, ha="left", fontsize=17)
    fig.text(.055, .90, "Fixed survivor basket · 24 US stocks · 5 bps per dollar traded · 2% annual short borrow", fontsize=10, color="#557787")
    for col, (phase, result) in enumerate(results.items()):
        ledger = result.ledger
        nav = ledger.nav / 100000
        peak = np.maximum.accumulate(np.r_[1, nav.to_numpy()])[1:]
        ax[0, col].plot(nav.index, nav, color=colors[phase], lw=1.6)
        ax[0, col].axhline(1, color="#A5AFB4", lw=.8)
        ax[0, col].set(title=phase.title(), ylabel="Net capital / initial capital")
        ax[1, col].fill_between(nav.index, 100 * (nav / peak - 1), 0, color=colors[phase], alpha=.28)
        ax[1, col].set(title="Drawdown", ylabel="% from running peak")
        for row in range(2):
            ax[row, col].grid(alpha=.18)
            ax[row, col].tick_params(axis="x", labelrotation=20)
    fig.text(.055,.025,"Each phase starts flat and includes entry and final liquidation. Final holdout (2020-2025) remains unacquired and unevaluated.",fontsize=9)
    fig.savefig(out / "03-historical-baseline.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.7, 4.8))
    fig.subplots_adjust(left=.08, right=.97, bottom=.2, top=.78, wspace=.27)
    fig.suptitle("Trading costs and residual market exposure",x=.055,y=.97,ha="left",fontsize=17)
    for phase, color in colors.items():
        part = summary[summary.phase == phase]
        axes[0].plot(part.trading_cost_bps, part.annualised_return * 100, marker="o",color=color,label=phase.title())
        ledger=results[phase].ledger
        market=dataset.market.pct_change(fill_method=None).reindex(ledger.index)
        rb=ledger.net_return.rolling(63).cov(market)/market.rolling(63).var()
        axes[1].plot(rb.index, rb, color=color, lw=1.1)
    axes[0].set(xlabel="Trading cost per dollar traded (bps)",ylabel="Annualised net return (%)",title="All predeclared fee scenarios")
    axes[0].set_xticks([0,5,10,20]);axes[0].legend(frameon=False)
    axes[1].set(ylabel="63-session realised beta to SPY",title="Realised beta can differ from the constraint")
    axes[1].tick_params(axis="x",labelrotation=20)
    for a in axes:a.axhline(0,color="#9DAAB1",lw=.8);a.grid(alpha=.15)
    fig.text(.055,.035,"0 bps still includes short-borrow charges. Scenarios were fixed in the protocol; the best scenario is not selected after the run.",fontsize=9)
    fig.savefig(out/"04-costs-and-beta.png",dpi=180);plt.close(fig)


def correlation_snapshots(dataset, window=126):
    returns, _ = simple_returns(dataset)
    eligible = returns.index[window-1:]
    eligible = eligible[eligible >= pd.Timestamp("2010-01-01")]
    # Each month-end is an actually observed session; no calendar filling.
    endpoints = pd.Series(eligible,index=eligible).groupby(eligible.to_period("M")).last()
    dates, matrices = [], []
    for date in endpoints:
        history = returns.loc[:date].iloc[-window:]
        corr = history.corr().to_numpy()
        if not np.isfinite(corr).all():raise ValueError("Invalid correlation snapshot")
        dates.append(str(date.date()));matrices.append(corr)
    return dates, matrices


def explorer(root, dataset):
    root=Path(root);out=root/"outputs/historical"
    dates,matrices=correlation_snapshots(dataset)
    tickers=list(dataset.prices.columns);n=len(tickers)
    hover=np.array([[f"{a} / {b}" for a in tickers] for b in tickers])
    def surface(z):
        return go.Surface(x=list(range(n)),y=list(range(n)),z=z.tolist(),surfacecolor=z.tolist(),
                          customdata=hover.tolist(),colorscale="RdBu_r",cmin=-1,cmax=1,
                          colorbar={"title":"Correlation"},
                          hovertemplate="%{customdata}<br>Correlation: %{z:.3f}<extra></extra>")
    fig=go.Figure(data=[surface(matrices[0])],frames=[go.Frame(data=[surface(z)],name=date) for date,z in zip(dates,matrices)])
    axis={"tickmode":"array","tickvals":list(range(n)),"ticktext":tickers,"tickfont":{"size":9}}
    steps=[{"label":d,"method":"animate","args":[[d],{"mode":"immediate","frame":{"duration":0,"redraw":True},"transition":{"duration":0}}]} for d in dates]
    fig.update_layout(title={"text":"126-session stock correlation surface","font":{"size":22}},height=700,
        font={"family":"Arial","color":"#203440"},paper_bgcolor="#FFFFFF",margin={"l":10,"r":30,"t":70,"b":110},
        scene={"xaxis":dict(axis,title="Stock"),"yaxis":dict(axis,title="Stock"),"zaxis":{"title":"Correlation","range":[-1,1]},
               "camera":{"eye":{"x":1.5,"y":1.5,"z":1.0}},"aspectratio":{"x":1,"y":1,"z":.7},"uirevision":"keep-camera"},
        sliders=[{"steps":steps,"currentvalue":{"prefix":"Window ending: "},"pad":{"t":35},"x":.05,"len":.90}],
        updatemenus=[{"type":"buttons","direction":"left","x":.05,"y":-.12,"buttons":[
            {"label":"Play","method":"animate","args":[None,{"frame":{"duration":250,"redraw":True},"transition":{"duration":0},"fromcurrent":True}]},
            {"label":"Pause","method":"animate","args":[[None],{"mode":"immediate","frame":{"duration":0,"redraw":False}}]}]}])
    header='''<main style="max-width:1200px;margin:32px auto;padding:0 24px;font-family:Arial,sans-serif;color:#203440">
<p style="letter-spacing:2px;color:#176960;font-size:12px">JOEL CERRAGA / MARKET-NEUTRAL RESEARCH / MILESTONE 2</p>
<h1 style="font-size:34px;margin-bottom:8px">How stock relationships change through time</h1>
<p>Drag to rotate, scroll to zoom and use the date slider or Play control. Each frame uses only the preceding 126 observed daily returns, including the labelled date.</p>
<p><strong>Historical development and validation data, 2010-2019.</strong> The final test period is excluded. Stock order is fixed across frames. Surface interpolation is visual only: stocks are discrete categories, and the grid values are the measured correlations.</p>
</main>'''
    footer='''<section style="max-width:1150px;margin:20px auto 40px;padding:0 24px;font:15px/1.6 Arial;color:#425563">
<h2>Research interpretation</h2><p>As Mantegna (1999) explains in <em>Hierarchical structure in financial markets</em>, correlations between stock returns can support a graph representation of their relationships. This explorer shows the full correlation matrix; it is not Mantegna's minimum spanning tree or evidence of profitable trading.</p>
<p>The strategy's positive-correlation neighbour graph is a separate transformation of these matrices. The 24-stock basket was chosen from surviving companies, so this is an exploratory sample. Historical prices use Yahoo Finance's supplied adjusted-close field. Rotate and compare frames without treating the z-axis as expected return.</p></section>'''
    html=fig.to_html(full_html=True,include_plotlyjs=True,config={"displaylogo":False,"responsive":True},auto_play=False)
    html=html.replace('<body>','<body style="margin:0;background:#fff">'+header).replace('</body>',footer+'</body>')
    target=out/"Historical-Correlation-Explorer.html";target.write_text(html,encoding="utf-8")
    (out/"correlation-snapshots.json").write_text(json.dumps({"tickers":tickers,"window":126,"dates":dates,"correlations":[m.tolist() for m in matrices]}))
    fig,ax=plt.subplots(figsize=(8.5,7.0))
    image=ax.imshow(matrices[-1],vmin=-1,vmax=1,cmap="RdBu_r")
    ax.set_xticks(range(n),tickers,rotation=65,ha="right",fontsize=8)
    ax.set_yticks(range(n),tickers,fontsize=8)
    ax.set_title(f"Historical correlation snapshot: {dates[-1]}\n126 observed sessions",pad=16)
    fig.colorbar(image,ax=ax,shrink=.8,label="Return correlation")
    fig.tight_layout();fig.savefig(out/"05-correlation-snapshot.png",dpi=180);plt.close(fig)
    return target
