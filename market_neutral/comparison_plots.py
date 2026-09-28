"""Historical comparison figures and an interactive view of graph trading scores."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .data import simple_returns
from .graph import correlation_graph, heat_diffusion
from .historical import load_protocol

COLORS = {"baseline": "#667F91", "graph_tau_1": "#137C70"}


def figures(root, results, summary, uncertainty):
    out = Path(root) / "outputs/comparison"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False, "text.color": "#203D4A"})
    fig, axes = plt.subplots(2, 2, figsize=(11.7, 7.2))
    fig.subplots_adjust(top=.84, bottom=.12, left=.08, right=.97, hspace=.43, wspace=.24)
    fig.suptitle("Graph diffusion against the historical baseline", x=.055, y=.975, ha="left", fontsize=17)
    fig.text(.055, .91, "5 bps per dollar traded | 2% annual short borrow | separate capital at each phase boundary", fontsize=10)
    for col, phase in enumerate(["development", "validation"]):
        for model, color in COLORS.items():
            ledger = results[(phase, model)].ledger
            capital = ledger.nav / 100000
            peak = np.maximum.accumulate(np.r_[1., capital])[1:]
            axes[0, col].plot(capital.index, capital, color=color, label="Baseline" if model == "baseline" else "Graph (tau = 1)")
            axes[1, col].plot(capital.index, (capital / peak - 1) * 100, color=color)
        axes[0, col].set(title=phase.title(), ylabel="Capital / initial capital")
        axes[1, col].set(title="Drawdown", ylabel="% from running peak")
        axes[0, col].legend(frameon=False, fontsize=9)
        for row in range(2):
            axes[row, col].grid(alpha=.17)
            axes[row, col].tick_params(axis="x", labelrotation=20)
    fig.text(.055, .025, "Observed development and validation only. Fixed survivor basket; no final-holdout observations or model selection.", fontsize=9)
    fig.savefig(out / "06-graph-comparison.png", dpi=180); plt.close(fig)

    selected = summary[(summary.annual_borrow_rate == .02) & (summary.purpose != "matched gross control")]
    fig, axes = plt.subplots(1, 2, figsize=(11.7, 5.2))
    fig.subplots_adjust(top=.75, bottom=.2, left=.09, right=.87, wspace=.27)
    fig.suptitle("Every declared diffusion-time and fee combination", x=.055, y=.97, ha="left", fontsize=17)
    fig.text(.055, .89, "Cells show graph CAGR minus baseline CAGR in percentage points; 2% annual borrow throughout.", fontsize=10)
    grids = []
    for phase in ["development", "validation"]:
        part = selected[selected.phase == phase]
        base = part[part.model == "baseline"].set_index("trading_cost_bps")
        grids.append(np.array([[100 * (part[(part.model == f"graph_tau_{tau:g}") & (part.trading_cost_bps == fee)].annualised_return.iloc[0] - base.loc[fee, "annualised_return"])
                              for fee in [0, 5, 10, 20]] for tau in [.5, 1, 2]]))
    bound = max(np.abs(z).max() for z in grids)
    for ax, phase, z in zip(axes, ["Development", "Validation"], grids):
        im = ax.imshow(z, cmap="BrBG", vmin=-bound, vmax=bound, aspect="auto")
        ax.set(title=phase, xlabel="Trading fee (bps)", ylabel="Diffusion time (tau)")
        ax.set_xticks(range(4), [0, 5, 10, 20]); ax.set_yticks(range(3), [.5, 1, 2])
        for i in range(3):
            for j in range(4):ax.text(j, i, f"{z[i,j]:+.2f}", ha="center", va="center", color="white" if abs(z[i,j]) > .65 * bound else "#203D4A")
    cax = fig.add_axes([.9, .23, .018, .49]); fig.colorbar(im, cax=cax, label="Graph minus baseline (pp)")
    fig.text(.055, .04, "Tau = 1 remains the primary model. These are descriptive sensitivity results, not a parameter-selection exercise.", fontsize=9)
    fig.savefig(out / "07-diffusion-and-costs.png", dpi=180); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.7, 5.8))
    fig.subplots_adjust(top=.78, bottom=.2, left=.14, right=.97, wspace=.5)
    fig.suptitle("How certain is the graph-minus-baseline difference?", x=.045, y=.97, ha="left", fontsize=17)
    fig.text(.045, .89, "Point estimates and 95% pointwise intervals for 252 times the mean daily net-return difference (percentage points).", fontsize=10)
    for ax, phase, color in zip(axes, ["development", "validation"], ["#667F91", "#137C70"]):
        part = uncertainty[uncertainty.phase == phase]
        for j, row in enumerate(part.itertuples()):
            ax.plot([100 * row.annualised_lower, 100 * row.annualised_upper], [j, j], color=color, lw=2)
            ax.plot(100 * row.annualised_mean_difference, j, "o", color=color)
        ax.set_yticks(range(4), ["Bootstrap L=5", "Bootstrap L=10", "Bootstrap L=20", "HAC lags=10"])
        ax.invert_yaxis(); ax.axvline(0, color="#A35345", ls="--", lw=1)
        ax.set(title=phase.title(), xlabel="Annualised mean difference (pp)", xlim=(-2.7, 2.8))
        ax.grid(axis="x", alpha=.2)
    fig.text(.045, .04, "Conditional on the observed policies and basket. These intervals are not CAGR intervals or corrections for strategy selection.", fontsize=9)
    fig.savefig(out / "08-paired-uncertainty.png", dpi=180); plt.close(fig)

    primary = summary[summary.model.isin(COLORS) & (summary.trading_cost_bps == 5) & (summary.annual_borrow_rate == .02)]
    fig, ax = plt.subplots(figsize=(11.7, 5.5));fig.subplots_adjust(top=.76, bottom=.24, left=.09, right=.97)
    fig.suptitle("Separate the signal contribution from recurring costs", x=.055, y=.965, ha="left", fontsize=17)
    fig.text(.055, .88, "Annualised arithmetic contributions at 5 bps and 2% borrow. Gross minus trading and borrow charges equals net.", fontsize=10)
    x = np.arange(4)
    for shift, field, label, color in [(-.23, "annualised_arithmetic_gross", "Gross contribution", "#137C70"), (0, "annualised_trading_drag", "Trading drag", "#A95A4B"), (.23, "annualised_borrow_drag", "Borrow drag", "#C2A15D")]:
        values = primary[field].to_numpy() * 100
        if "drag" in field:values = -values
        ax.bar(x + shift, values, .22, label=label, color=color)
    ax.plot(x, primary.annualised_arithmetic_net * 100, "D", color="#203D4A", label="Net arithmetic mean", ms=6)
    ax.set_xticks(x, ["Development\nBaseline", "Development\nGraph", "Validation\nBaseline", "Validation\nGraph"])
    ax.set_ylabel("Percentage points per year");ax.axhline(0, color="#9EAAB0", lw=.8)
    ax.grid(axis="y", alpha=.15);ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(.5, -.17), frameon=False, fontsize=9)
    fig.savefig(out / "09-return-and-cost-components.png", dpi=180);plt.close(fig)


def graph_snapshots(dataset, protocol):
    returns, _ = simple_returns(dataset)
    dates = pd.Series(returns.index, index=returns.index).loc["2010-01-01":].groupby(lambda d: d.to_period("M")).last()
    snapshots = []
    cfg = protocol["config"]
    for date in dates:
        history = returns.loc[:date]
        _, adjacency, laplacian = correlation_graph(history.iloc[-cfg["correlation_window"]:], cfg["neighbours"], cfg["minimum_correlation"])
        vol = history.iloc[-cfg["volatility_window"]:].std(ddof=1).to_numpy()
        shock = np.log1p(history.iloc[-cfg["signal_window"]:].to_numpy()).sum(axis=0)
        shock = np.clip(shock / (vol * np.sqrt(cfg["signal_window"])), -5, 5)
        smooth = heat_diffusion(shock, laplacian, cfg["diffusion_time"])
        snapshots.append({"date": str(date.date()), "adjacency": adjacency.tolist(), "shock": shock.tolist(),
                          "smooth": smooth.tolist(), "graph_score": (smooth - shock).tolist()})
    return snapshots


def explorer(root, dataset):
    root = Path(root);out = root / "outputs/comparison"
    protocol = load_protocol(root)
    snapshots = graph_snapshots(dataset, protocol)
    tickers = list(dataset.prices.columns)
    groups = [next(group for group, stocks in protocol["groups"].items() if t in stocks) for t in tickers]
    group_names = list(protocol["groups"])
    xy = []
    for ticker, group in zip(tickers, groups):
        theta = group_names.index(group) * 2 * np.pi / len(group_names)
        angle = protocol["groups"][group].index(ticker) * np.pi / 2
        xy.append([3 * np.cos(theta) + .65 * np.cos(angle), 3 * np.sin(theta) + .65 * np.sin(angle)])
    xy = np.asarray(xy)
    bound = max(1., float(np.ceil(np.max(np.abs([[s["shock"], s["graph_score"]] for s in snapshots])))))

    def traces(s):
        w = np.asarray(s["adjacency"]);edge_x=[];edge_y=[]
        for i, j in zip(*np.where(np.triu(w > 0, 1))):
            edge_x.extend([xy[i,0], xy[j,0], None]);edge_y.extend([xy[i,1], xy[j,1], None])
        custom = [[ticker, group, s["shock"][i], s["smooth"][i]] for i, (ticker, group) in enumerate(zip(tickers, groups))]
        return [
            go.Scatter3d(x=edge_x, y=edge_y, z=[0 if a is not None else None for a in edge_x], mode="lines", line={"color":"#ADBFC6","width":2}, hoverinfo="skip", showlegend=False),
            go.Scatter3d(x=xy[:,0].tolist(), y=xy[:,1].tolist(), z=s["graph_score"], mode="markers+text", text=tickers, textposition="top center", textfont={"size":10},
                marker={"size":6,"color":s["graph_score"],"colorscale":"RdBu_r","cmin":-bound,"cmax":bound}, customdata=custom,
                hovertemplate="%{customdata[0]} | %{customdata[1]}<br>Shock: %{customdata[2]:.3f}<br>Smoothed: %{customdata[3]:.3f}<br>Graph score: %{z:.3f}<extra></extra>", name="Graph score"),
            go.Bar(x=tickers,y=(-np.array(s["shock"])).tolist(),name="Baseline score",marker_color=COLORS["baseline"]),
            go.Bar(x=tickers,y=s["graph_score"],name="Graph score",marker_color=COLORS["graph_tau_1"])]
    fig = make_subplots(rows=1, cols=2, specs=[[{"type":"scene"},{"type":"xy"}]], column_widths=[.56,.44], horizontal_spacing=.055,
                        subplot_titles=["Network and graph score", "Unconstrained scores before portfolio projection"])
    first = traces(snapshots[0])
    for trace in first[:2]:fig.add_trace(trace,row=1,col=1)
    for trace in first[2:]:fig.add_trace(trace,row=1,col=2)
    fig.frames = [go.Frame(data=traces(s),name=s["date"],traces=[0,1,2,3]) for s in snapshots]
    fig.update_layout(height=750, paper_bgcolor="white", font={"family":"Arial","color":"#203D4A"},
        margin={"t":65,"l":20,"r":25,"b":155}, barmode="group", legend={"orientation":"h","y":1.08,"x":.58},
        scene={"xaxis":{"title":"Fixed display layout","showticklabels":False},"yaxis":{"title":"Fixed display layout","showticklabels":False},
               "zaxis":{"title":"Graph score","range":[-bound,bound]},"uirevision":"fixed-camera","camera":{"eye":{"x":1.35,"y":1.45,"z":1.1}}},
        sliders=[{"active":0,"currentvalue":{"prefix":"Decision close: "},"pad":{"t":65},"x":.06,"len":.88,
                  "steps":[{"label":s["date"],"method":"animate","args":[[s["date"]],{"mode":"immediate","frame":{"duration":0,"redraw":True},"transition":{"duration":0}}]} for s in snapshots]}],
        updatemenus=[{"type":"buttons","direction":"left","x":.06,"y":-.18,"buttons":[
            {"label":"Play","method":"animate","args":[None,{"frame":{"duration":450,"redraw":True},"transition":{"duration":0},"fromcurrent":True}]},
            {"label":"Pause","method":"animate","args":[[None],{"mode":"immediate","frame":{"duration":0,"redraw":False}}]}]}])
    fig.update_yaxes(title_text="Score, not portfolio weight",range=[-bound,bound],row=1,col=2)
    fig.update_xaxes(tickangle=-65,row=1,col=2)
    html = fig.to_html(full_html=True, include_plotlyjs=True, auto_play=False, config={"displaylogo":False,"responsive":True})
    intro='''<header style="max-width:1180px;margin:32px auto 0;padding:0 25px;font:16px/1.5 Arial;color:#203D4A">
<p style="color:#137C70;letter-spacing:2px;font-size:12px">JOEL CERRAGA / MARKET-NEUTRAL RESEARCH / MILESTONE 3</p>
<h1>From connected stocks to a trading score</h1><p>Rotate the network, hover over a stock and move through 120 monthly snapshots. A positive graph score proposes a long direction before dollar/beta projection and position limits. The final portfolio can differ in both sign and scale.</p>
<p><strong>Read the geometry carefully:</strong> horizontal positions are fixed by the six research groups for display. They are not estimated market distances. Lines on the zero-score plane show retained graph connections; height and colour show the graph score. Scores use information through the displayed close and trade only after the specified execution delay.</p></header>'''
    footer='''<footer style="max-width:1180px;margin:0 auto 35px;padding:0 25px;font:15px/1.6 Arial;color:#425563"><h2>Research interpretation</h2>
<p>Kondor and Lafferty (2002), in <em>Diffusion Kernels on Graphs and Other Discrete Input Spaces</em>, supply the matrix-exponential smoothing relationship. Reversing the residual is this project's trading hypothesis, not a result established in that paper.</p>
<p>The graph uses 126-session correlations, five directed neighbours above 0.20 and a symmetric union. Baseline score = minus the scaled shock. Graph score = smoothed shock minus the shock, with diffusion time one. Every node uses the same fixed survivor basket. These development/validation snapshots end in 2019; the final holdout is excluded.</p>
<p><strong>Observed performance:</strong> at 5 bps and 2% borrow, the graph strategy loses money in both phases. Its small validation improvement over the baseline has a confidence interval that includes zero. The visual is an explanation of the signal, not evidence of an established trading edge.</p><h2>References</h2><p>Kondor, R.I. and Lafferty, J.D. (2002) ‘Diffusion Kernels on Graphs and Other Discrete Input Spaces’, in <em>Proceedings of the 19th International Conference on Machine Learning</em>, pp. 315–322. doi: <a href="https://doi.org/10.5555/645531.655996">10.5555/645531.655996</a>.</p></footer>'''
    html=html.replace('<body>','<body style="margin:0;background:white">'+intro).replace('</body>',footer+'</body>')
    target=out/'Graph-Diffusion-Explorer.html';target.write_text(html,encoding='utf-8')
    (out/'graph-snapshots.json').write_text(json.dumps({"tickers":tickers,"groups":groups,"layout_xy":xy.tolist(),"layout":"Fixed research-group display coordinates, not data-fitted distances","snapshots":snapshots}))
    last=snapshots[-1];w=np.asarray(last['adjacency']);z=np.asarray(last['graph_score'])
    fig=plt.figure(figsize=(11.7,5.7));ax=fig.add_subplot(121,projection='3d');bar=fig.add_subplot(122)
    for i,j in zip(*np.where(np.triu(w>0,1))):ax.plot(xy[[i,j],0],xy[[i,j],1],[0,0],color='#AABDC5',alpha=.6,lw=.7)
    ax.scatter(xy[:,0],xy[:,1],z,c=z,cmap='RdBu_r',vmin=-bound,vmax=bound,s=34)
    for i,ticker in enumerate(tickers):ax.text(xy[i,0],xy[i,1],z[i]+.07,ticker,fontsize=6)
    ax.set(zlabel='Graph score',title='Fixed display coordinates; edges on zero plane');ax.set_xticks([]);ax.set_yticks([])
    x=np.arange(len(tickers));bar.bar(x-.2,-np.asarray(last['shock']),.4,label='Baseline score',color=COLORS['baseline']);bar.bar(x+.2,z,.4,label='Graph score',color=COLORS['graph_tau_1'])
    bar.set_xticks(x,tickers,rotation=70,fontsize=7);bar.set_ylabel('Unconstrained score');bar.legend(frameon=False,fontsize=9);bar.grid(axis='y',alpha=.15)
    fig.suptitle(f"How diffusion changes the score: {last['date']}",x=.055,y=.98,ha='left',fontsize=17)
    fig.subplots_adjust(top=.83,bottom=.2,left=.03,right=.98,wspace=.18)
    fig.text(.055,.035,'Display geometry does not enter the strategy. Scores are subsequently projected and scaled; the plotted scores are not trades.',fontsize=9)
    fig.savefig(out/'10-graph-signal-snapshot.png',dpi=180);plt.close(fig)
    return target
