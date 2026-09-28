"""Figures for the fixed final evaluation and its descriptive topology transfer."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from .topology import FEATURES, landscape
from .topology_plots import _save_figure

COLORS={"baseline":"#667F91","graph_tau_1":"#137C70"}
LABELS={"baseline":"Baseline","graph_tau_1":"Graph, τ = 1"}


def final_landscape_explorer(root):
    root=Path(root);out=root/"outputs/final/topology"
    all_snapshots=json.loads((out/"monthly-diagrams.json").read_text())
    snapshots=[s for s in all_snapshots.values() if s["window"]==126]
    # Reuse only the earlier visual layout; replace every data trace and frame.
    template=json.loads((root/"outputs/topology/explorer-figure.json").read_text())
    fig=go.Figure(layout=template["layout"])
    grid=np.linspace(0,2,401);ranks=list(range(1,6))
    upper=max(float(landscape(s["h1"],grid).max()) for s in snapshots)*1.05
    def traces(s):
        bars=np.asarray(s["h1"]).reshape(-1,2)
        return [go.Surface(x=grid.tolist(),y=ranks,z=landscape(bars,grid).tolist(),colorscale="Teal",
                    cmin=0,cmax=upper,showscale=False,
                    hovertemplate="Threshold: %{x:.3f}<br>Rank: %{y}<br>Height: %{z:.4f}<extra></extra>"),
                go.Scatter(x=bars[:,0].tolist(),y=bars[:,1].tolist(),mode="markers",marker={"color":"#137C70","size":9},
                    hovertemplate="Birth: %{x:.4f}<br>Death: %{y:.4f}<extra></extra>"),
                go.Scatter(x=[0,2],y=[0,2],mode="lines",line={"color":"#A4AFB5","dash":"dash"},hoverinfo="skip")]
    def title(s):return f"{s['date']} | total H1 persistence {s['h1_total']:.3f} | maximum {s['h1_max']:.3f}"
    fig.add_traces(traces(snapshots[0]))
    fig.frames=[go.Frame(name=s["date"],data=traces(s),traces=[0,1,2],layout={"title":{"text":title(s)}}) for s in snapshots]
    steps=[{"label":s["date"],"method":"animate","args":[[s["date"]],{"mode":"immediate","frame":{"duration":0,"redraw":True},"transition":{"duration":0}}]} for s in snapshots]
    fig.update_layout(title={"text":title(snapshots[0])},scene={"zaxis":{"range":[0,upper]}})
    # Assign the slider outright: update_layout merges arrays with the old 120-step template.
    fig.layout.sliders = [{"active":0,"currentvalue":{"prefix":"Final-test close: "},"pad":{"t":55},"x":.07,"len":.85,"steps":steps}]
    if len(fig.layout.sliders[0].steps) != len(fig.frames):
        raise ValueError("Slider/frame calendar mismatch")
    html=fig.to_html(full_html=True,include_plotlyjs=True,auto_play=False,config={"responsive":True,"displaylogo":False})
    intro='''<header style="max-width:1200px;margin:30px auto 0;padding:0 25px;font:16px/1.55 Arial;color:#203D4A">
<p style="letter-spacing:2px;color:#137C70;font-size:12px">JOEL CERRAGA / MARKET-NEUTRAL RESEARCH / MILESTONE 5</p>
<h1>Persistence in the reserved historical test</h1>
<p>Inspect 72 monthly observations from 2020–2025 using the same 24 stocks and primary 126-session return window. Rotate, hover, use the date slider or play the sequence. Each frame uses only returns available through the displayed close.</p>
<p>As Bubenik (2015) explains in <em>Statistical topological data analysis using persistence landscapes</em>, intervals can be represented by ordered tent functions. Here rank is discrete; the joining surface is visual interpolation. Only five layers are shown, while every finite interval enters the numerical features.</p>
<p><strong>Scientific scope:</strong> topology remains a descriptor. No topology trading overlay was introduced. This is a retrospectively reserved survivor-basket study; the period has now been inspected and cannot be reused as an untouched test.</p></header>'''
    footer='''<footer style="max-width:1200px;margin:0 auto 35px;padding:0 25px;font:15px/1.6 Arial;color:#425563">
<h2>What the final evaluation found</h2><p>At 5 bps per dollar traded and 2% annual short borrow, baseline CAGR was −5.57% and primary graph CAGR was −4.80%. The paired improvement remains uncertain. The predeclared evidence criteria were not met. A landscape peak is neither a return forecast nor a crash probability.</p>
<p>All axes are fixed through playback. The full correlation distance supplies the geometry; a sparse trading adjacency matrix is not substituted. Both infinite-interval handling and numerical landscape values are checked separately from rendering. Browser interaction remains a local environment check.</p>
<h2>References</h2><p>Bubenik, P. (2015) ‘Statistical topological data analysis using persistence landscapes’, <em>Journal of Machine Learning Research</em>, 16(3), pp. 77–102. Available at: <a href="https://jmlr.org/papers/v16/bubenik15a.html">https://jmlr.org/papers/v16/bubenik15a.html</a> (Accessed: 21 September 2026).</p></footer>'''
    html=html.replace("<body>",'<body style="margin:0;background:white">'+intro).replace("</body>",footer+"</body>")
    (out/"Final-Test-Landscape-Explorer.html").write_text(html,encoding="utf-8")
    (out/"explorer-figure.json").write_text(fig.to_json(),encoding="utf-8")


def create_final_figures(root):
    root=Path(root);out=root/"outputs/final"
    summary=pd.read_csv(out/"final-summary.csv")
    intervals=pd.read_csv(out/"mean-inference.csv")
    primary=summary.loc[summary.purpose=="primary"].set_index("model")
    annual=pd.read_csv(out/"calendar-year-results.csv")
    exposures=pd.read_csv(out/"exposure-diagnostics.csv",parse_dates=["date"])
    ledgers={name:pd.read_csv(out/f"final_test__{name}__fee5__borrow0.02-ledger.csv",index_col=0,parse_dates=True)
             for name in COLORS}
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for model,ledger in ledgers.items():
        growth=np.r_[1.,np.cumprod(1+ledger.net_return.to_numpy())]
        dates=pd.DatetimeIndex([pd.Timestamp("2019-12-31"),*ledger.index])
        axes[0,0].plot(dates,growth*100000,label=LABELS[model],color=COLORS[model],lw=1.2)
        axes[0,1].plot(dates,100*(growth/np.maximum.accumulate(growth)-1),color=COLORS[model],lw=1.2)
        yearly=annual.loc[annual.model==model]
        shift=-.18 if model=="baseline" else .18
        axes[1,0].bar(yearly.year+shift,100*yearly.net_return,width=.34,color=COLORS[model],label=LABELS[model])
        data=exposures.loc[exposures.model==model]
        axes[1,1].plot(data.date,data.rolling63_realised_beta,color=COLORS[model],lw=.8)
    axes[0,0].axhline(100000,color="#777777",ls="--",lw=.8,label="No trade, zero cash rate")
    axes[0,0].set_title("Net capital, USD",loc="left");axes[0,0].legend(fontsize=8)
    axes[0,1].set_title("Drawdown from running peak, %",loc="left")
    axes[1,0].set_title("Calendar-year net return, %",loc="left");axes[1,0].axhline(0,color="#777777",lw=.7)
    axes[1,1].set_title("Realised beta, rolling 63 sessions",loc="left");axes[1,1].axhline(0,color="#777777",lw=.7)
    for ax in axes.flat:ax.grid(alpha=.15)
    fig.suptitle("Reserved test: 2020–2025 | default costs",x=.06,ha="left",fontsize=16)
    fig.text(.06,.012,"5 bps per dollar traded; 2% annual short borrow. One continuous ledger, with entry and terminal liquidation costs.",fontsize=9)
    fig.tight_layout(rect=[0,.035,1,.96]);_save_figure(fig,out/"13-final-performance.png");plt.close(fig)

    selected=intervals.loc[(intervals.method=="stationary bootstrap") & (intervals.block_or_lags==10)]
    contrasts=["baseline_net_mean","graph_net_mean","graph_minus_baseline_mean"]
    labels=["Baseline versus zero cash rate","Graph versus zero cash rate","Graph minus baseline"]
    fig,ax=plt.subplots(figsize=(11.6,4.8))
    for y,contrast in enumerate(contrasts):
        rows=selected.loc[selected.contrast==contrast].set_index("interval_type")
        for interval_type,width,color in [("bonferroni",2,"#667F91"),("pointwise",6,"#137C70")]:
            row=rows.loc[interval_type]
            ax.plot([100*row.annualised_lower,100*row.annualised_upper],[y,y],lw=width,color=color,
                    label="98.33% per mean; Bonferroni family of three" if y==0 and interval_type=="bonferroni" else
                          "95% pointwise" if y==0 else None)
        ax.scatter(100*rows.iloc[0].annualised_mean,y,color="#1A333E",s=40,zorder=3)
    ax.axvline(0,color="#9B5631",ls="--",lw=1)
    ax.set_yticks(range(3),labels);ax.invert_yaxis();ax.set_ylim(2.6,-.6)
    ax.set_xlabel("Annualised arithmetic mean relative to the stated comparator (pp)")
    ax.grid(axis="x",alpha=.15);ax.legend(loc="upper center",bbox_to_anchor=(.5,-.21),fontsize=9,ncol=2)
    fig.suptitle("Uncertainty separates a smaller loss from a demonstrated edge",x=.04,ha="left",fontsize=15)
    fig.subplots_adjust(left=.28,right=.97,top=.83,bottom=.26)
    _save_figure(fig,out/"14-final-inference.png");plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(12,5.2))
    for model,color,style in [("baseline",COLORS["baseline"],"-"),("graph_tau_0.5","#B18046","--"),
                              ("graph_tau_1",COLORS["graph_tau_1"],"-"),("graph_tau_2","#9472A1","--")]:
        part=summary.loc[(summary.model==model)&(summary.annual_borrow_rate==.02)].sort_values("trading_cost_bps")
        axes[0].plot(part.trading_cost_bps,100*part.annualised_return,marker="o",color=color,ls=style,label=LABELS.get(model,model.replace("graph_tau_","Graph, τ = ")))
    axes[0].axhline(0,color="#777777",lw=.8);axes[0].set(xlabel="Cost per dollar traded, bps",ylabel="CAGR, %",title="Every declared fee/diffusion case")
    axes[0].set_xticks([0,5,10,20]);axes[0].legend(fontsize=8);axes[0].grid(alpha=.15)
    x=np.arange(2);gross=100*primary.loc[list(COLORS),"annualised_arithmetic_gross"].to_numpy()
    trade=100*primary.loc[list(COLORS),"annualised_trading_drag"].to_numpy()
    borrow=100*primary.loc[list(COLORS),"annualised_borrow_drag"].to_numpy()
    net=100*primary.loc[list(COLORS),"annualised_arithmetic_net"].to_numpy()
    axes[1].bar(x,gross,color="#137C70",label="Gross contribution")
    axes[1].bar(x,-trade,color="#B18046",label="Trading cost")
    axes[1].bar(x,-borrow,bottom=-trade,color="#9472A1",label="Borrow cost")
    axes[1].scatter(x,net,marker="D",color="#1A333E",label="Net arithmetic mean",zorder=3)
    axes[1].axhline(0,color="#777777",lw=.8);axes[1].set_xticks(x,["Baseline","Graph, τ = 1"])
    axes[1].set_ylabel("Annualised arithmetic contribution / drag, pp")
    axes[1].set_title("Default costs exceed gross contribution")
    axes[1].legend(fontsize=8,loc="upper center",bbox_to_anchor=(.5,-.14),ncol=2)
    fig.suptitle("Cost sensitivity and the source of the net losses",x=.06,ha="left",fontsize=16)
    fig.tight_layout(rect=[0,.07,1,.92]);_save_figure(fig,out/"15-final-costs.png");plt.close(fig)

    old=pd.read_csv(root/"outputs/topology/control-model-scores.csv")
    latest=pd.read_csv(out/"topology/control-model-scores.csv")
    scores=pd.concat([old,latest]);scores=scores.loc[scores.window==126]
    sensitivity=pd.read_csv(out/"topology/window-sensitivity.csv")
    fig,axes=plt.subplots(1,2,figsize=(12,5.2))
    for shift,phase,color in [(-.24,"development","#667F91"),(0,"validation","#B18046"),(.24,"final_test","#137C70")]:
        values=scores.loc[scores.phase==phase].set_index("feature").loc[list(FEATURES),"r2"]
        axes[0].bar(np.arange(4)+shift,values,width=.23,color=color,label=phase.replace("_"," ").capitalize())
    axes[0].axhline(0,color="#777777",lw=.8);axes[0].set_ylabel("Descriptor R²; fitted on development only")
    axes[0].set_title("The same control models across all phases");axes[0].legend(fontsize=8)
    for shift,window,color in [(-.18,63,"#137C70"),(.18,252,"#B18046")]:
        values=sensitivity.loc[sensitivity.window==window].set_index("feature").loc[list(FEATURES),"spearman"]
        bars=axes[1].bar(np.arange(4)+shift,values,width=.34,color=color,label=f"{window} vs 126 sessions")
        axes[1].bar_label(bars,fmt="%.2f",fontsize=8,padding=3)
    axes[1].set_ylim(0,1.12);axes[1].set_ylabel("Paired-date Spearman correlation");axes[1].set_title("Final-test window sensitivity")
    axes[1].legend(fontsize=8,loc="upper right")
    for ax in axes:
        ax.set_xticks(range(4),["H0 mean","H0 max","H1 total","H1 max"]);ax.grid(axis="y",alpha=.15)
    fig.suptitle("Topology transfer: descriptive relationships remain conditional",x=.06,ha="left",fontsize=16)
    fig.tight_layout(rect=[0,0,1,.92]);_save_figure(fig,out/"16-final-topology-transfer.png");plt.close(fig)
    final_landscape_explorer(root)
    write_results(root)


def write_results(root):
    out=Path(root)/"outputs/final"
    summary=pd.read_csv(out/"final-summary.csv")
    primary=summary.loc[summary.purpose=="primary"].set_index("model")
    intervals=pd.read_csv(out/"mean-inference.csv")
    delta=intervals.loc[(intervals.contrast=="graph_minus_baseline_mean")&(intervals.method=="stationary bootstrap")&
                        (intervals.block_or_lags==10)].set_index("interval_type")
    rows=["# Milestone 5 — Final evaluation", "",
          "The local protocol was locked before acquisition of the reserved 2020–2025 observations. All 22 declared cases were evaluated; no primary model or parameter was changed after results. The test is now observed.", "",
          "## Primary outcomes", "", "| Measure | Baseline | Graph, τ = 1 |", "| --- | ---: | ---: |"]
    for key,label in [("annualised_return","CAGR"),("total_return","Total net return"),("maximum_drawdown","Maximum drawdown"),
                      ("annualised_volatility","Annualised volatility"),("mean_gross_exposure","Mean gross exposure"),("mean_turnover","Mean daily turnover")]:
        rows.append(f"| {label} | {100*primary.loc['baseline',key]:.2f}% | {100*primary.loc['graph_tau_1',key]:.2f}% |")
    rows += ["", "Defaults: 5 bps per dollar traded, 2% annual short borrow. Both strategies lost money in every calendar year of the test.", "",
             f"The annualised arithmetic graph-minus-baseline mean is **{100*delta.loc['pointwise','annualised_mean']:+.2f} pp**. Its 95% pointwise interval is **{100*delta.loc['pointwise','annualised_lower']:+.2f} to {100*delta.loc['pointwise','annualised_upper']:+.2f} pp**; the Bonferroni-adjusted interval is **{100*delta.loc['bonferroni','annualised_lower']:+.2f} to {100*delta.loc['bonferroni','annualised_upper']:+.2f} pp**. These are arithmetic-mean intervals, not CAGR intervals.", "",
             "None of the four predeclared evidence conditions was met. A smaller observed loss does not establish a positive or reliably superior strategy. Matched-gross controls also leave the paired improvement uncertain.", "",
             "## Why the economic result is negative", ""]
    for model in COLORS:
        row=primary.loc[model]
        rows.append(f"{LABELS[model]}: annualised arithmetic gross contribution {100*row.annualised_arithmetic_gross:+.2f}%, trading drag {100*row.annualised_trading_drag:.2f}%, borrow drag {100*row.annualised_borrow_drag:.2f}%, net {100*row.annualised_arithmetic_net:+.2f}%.")
        rows.append("")
    rows += ["## Topology remains a diagnostic", "",
             "Four features at all three declared windows were extracted on 1,508 final-test dates. Development-fitted control models were transferred without refitting. The transferred primary-window H1-total and H1-maximum approximations gave final-test R² −0.217 and −0.088. H1 rankings remain window-sensitive. No topology overlay was added.", "",
             "## Scope and next step", "",
             "This is a retrospectively reserved survivor-basket study using current-vintage adjusted prices. It is not a prospective blind test or evidence of deployability. The inference is conditional and approximate; it does not cure sample selection or nonstationarity.", "",
             "The research evaluation is complete for the frozen design. Next is the public-repository and presentation milestone, including accurate CV/LinkedIn claims and the author's final document specification. Any future model revision requires new evidence; this test cannot be reused as untouched.", ""]
    (out/"milestone-5-results.md").write_text("\n".join(rows),encoding="utf-8")
