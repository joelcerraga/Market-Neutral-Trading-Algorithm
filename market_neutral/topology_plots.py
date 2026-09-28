"""Scientific figures and an offline, animated persistence-landscape companion."""
from pathlib import Path
import json
from io import BytesIO
from PIL import Image
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .topology import FEATURES, CONTROLS, landscape

LABELS = {"h0_mean": "H0 mean merger distance", "h0_max": "H0 final merger distance",
          "h1_total": "H1 total persistence", "h1_max": "H1 maximum persistence",
          "mean_correlation": "Mean correlation", "mean_stock_volatility": "Mean stock volatility",
          "spy_volatility": "SPY volatility"}


def _save_figure(fig, path):
    """Validate the complete in-memory PNG before replacing the visible file."""
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=170)
    payload = buffer.getvalue()
    with Image.open(BytesIO(payload)) as image:
        image.verify()
    temporary = path.with_suffix(".png.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    if path.stat().st_size != len(payload):
        raise IOError(f"Incomplete chart write: {path}")


def create_topology_figures(root):
    out = Path(root) / "outputs/topology"
    data = pd.read_csv(out / "features.csv", index_col="date", parse_dates=True)
    primary = data.loc[data.window == 126]
    correlations = pd.read_csv(out / "control-correlations.csv")
    windows = pd.read_csv(out / "window-sensitivity.csv")
    scores = pd.read_csv(out / "control-model-scores.csv")
    all_snapshots = json.loads((out / "monthly-diagrams.json").read_text())
    snapshots = [s for s in all_snapshots.values() if s["window"] == 126]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                        "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(3, 2, figsize=(12, 8.3), sharex=True)
    for ax, feature in zip(axes.flat, [*FEATURES, "mean_correlation", "spy_volatility"]):
        ax.plot(primary.index, primary[feature], color="#137C70", lw=.9)
        ax.axvline(pd.Timestamp("2017-01-01"), color="#A15D35", ls="--", lw=1)
        ax.set_title(LABELS[feature], loc="left", fontsize=10)
        ax.grid(alpha=.15)
    fig.suptitle("126-session descriptors | fixed 24-stock basket", x=.06, ha="left", fontsize=16)
    fig.text(.06, .012, "Dashed line: validation begins. Each observation uses only returns through that date; no return forecast is shown.", fontsize=9)
    fig.tight_layout(rect=[0, .035, 1, .96]); _save_figure(fig, out / "09-topology-features.png"); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, phase in zip(axes, ["development", "validation"]):
        table = correlations.loc[(correlations.window == 126) & (correlations.phase == phase)]
        values = table.pivot(index="feature", columns="control", values="spearman").loc[list(FEATURES), list(CONTROLS)].to_numpy()
        im = ax.imshow(values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(3), ["Mean\ncorrelation", "Stock\nvolatility", "SPY\nvolatility"])
        ax.set_yticks(range(4), ["H0 mean", "H0 maximum", "H1 total", "H1 maximum"])
        ax.set_title(phase.capitalize(), loc="left")
        for i in range(4):
            for j in range(3):
                ax.text(j, i, f"{values[i,j]:+.3f}", ha="center", va="center", color="white" if abs(values[i,j]) > .55 else "#18303D")
    fig.subplots_adjust(left=.12, right=.88, bottom=.16, top=.82, wspace=.18)
    fig.colorbar(im, cax=fig.add_axes([.91, .19, .018, .58]), label="Spearman correlation")
    fig.suptitle("Topology and simpler controls | 126-session window", x=.06, ha="left", fontsize=16)
    fig.text(.06, .035, "Descriptive dependence on overlapping windows; these correlations have no independence-based p-values.", fontsize=9)
    _save_figure(fig, out / "10-control-redundancy.png"); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    for ax, phase in zip(axes, ["development", "validation"]):
        for shift, window, color in [(-.18, 63, "#137C70"), (.18, 252, "#A15D35")]:
            values = windows.loc[(windows.phase == phase) & (windows.window == window)].set_index("feature").loc[list(FEATURES), "spearman"]
            bars = ax.bar(np.arange(4) + shift, values, width=.34, color=color, label=f"{window} vs 126 sessions")
            ax.bar_label(bars, fmt="%.2f", fontsize=8, padding=2)
        ax.set_xticks(range(4), ["H0 mean", "H0 max", "H1 total", "H1 max"])
        ax.set_ylim(-.05, 1.12); ax.set_title(phase.capitalize(), loc="left"); ax.grid(axis="y", alpha=.15)
    axes[0].set_ylabel("Paired-date Spearman correlation"); axes[1].legend(loc="lower left", fontsize=9)
    fig.suptitle("Changing the estimation window changes the descriptor", x=.06, ha="left", fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, .92]); _save_figure(fig, out / "11-window-sensitivity.png"); plt.close(fig)

    # Fixed scales over all display dates; they affect only the visualisation.
    grid = np.linspace(0, 2, 401)
    layers = np.arange(1, 6)
    landscape_bound = max(float(landscape(s["h1"], grid).max()) for s in snapshots) * 1.05
    def traces(snapshot):
        h1 = np.asarray(snapshot["h1"]).reshape(-1, 2)
        return [go.Surface(x=grid.tolist(), y=layers.tolist(), z=landscape(h1, grid).tolist(),
                           colorscale="Teal", cmin=0, cmax=landscape_bound, showscale=False,
                           hovertemplate="Threshold: %{x:.3f}<br>Layer: %{y}<br>Height: %{z:.4f}<extra></extra>"),
                go.Scatter(x=h1[:, 0].tolist(), y=h1[:, 1].tolist(), mode="markers",
                           marker={"color":"#137C70", "size":9}, name="H1 intervals",
                           hovertemplate="Birth: %{x:.4f}<br>Death: %{y:.4f}<extra></extra>"),
                go.Scatter(x=[0, 2], y=[0, 2], mode="lines", line={"color":"#A4AFB5", "dash":"dash"},
                           hoverinfo="skip", showlegend=False)]
    fig = make_subplots(rows=1, cols=2, specs=[[{"type":"scene"}, {"type":"xy"}]],
                        column_widths=[.62, .38], horizontal_spacing=.07,
                        subplot_titles=["First five H1 landscape layers", "H1 birth and death thresholds"])
    first = traces(snapshots[0])
    fig.add_trace(first[0], row=1, col=1)
    for trace in first[1:]: fig.add_trace(trace, row=1, col=2)
    def title(s):
        return f"{s['date']} | total H1 persistence {s['h1_total']:.3f} | maximum {s['h1_max']:.3f}"
    fig.frames = [go.Frame(data=traces(s), name=s["date"], traces=[0, 1, 2],
                           layout={"title":{"text":title(s)}}) for s in snapshots]
    fig.update_layout(height=720, title={"text":title(snapshots[0]), "font":{"size":15}},
                      font={"family":"Arial", "color":"#203D4A"}, paper_bgcolor="white", showlegend=False,
                      margin={"l":30,"r":35,"b":140,"t":95},
                      scene={"xaxis":{"title":"Filtration threshold ε", "range":[0,2]},
                             "yaxis":{"title":"Landscape rank k", "tickvals":layers.tolist(), "range":[1,5]},
                             "zaxis":{"title":"Landscape height", "range":[0,landscape_bound]},
                             "uirevision":"landscape-camera", "camera":{"eye":{"x":1.55,"y":1.55,"z":1.0}}},
                      sliders=[{"active":0, "currentvalue":{"prefix":"Observed close: "}, "pad":{"t":55},
                                "x":.07, "len":.85, "steps":[{"label":s["date"],"method":"animate",
                                "args":[[s["date"]], {"mode":"immediate", "frame":{"duration":0,"redraw":True},
                                "transition":{"duration":0}}]} for s in snapshots]}],
                      updatemenus=[{"type":"buttons","direction":"left","x":.07,"y":-.17,"buttons":[
                          {"label":"Play","method":"animate","args":[None,{"frame":{"duration":450,"redraw":True},"transition":{"duration":0},"fromcurrent":True}]},
                          {"label":"Pause","method":"animate","args":[[None],{"mode":"immediate","frame":{"duration":0,"redraw":False}}]}]}])
    fig.update_xaxes(title_text="Birth threshold", range=[0,2], row=1, col=2)
    fig.update_yaxes(title_text="Death threshold", range=[0,2], scaleanchor="x", scaleratio=1, row=1, col=2)
    html = fig.to_html(full_html=True, include_plotlyjs=True, auto_play=False, config={"responsive":True,"displaylogo":False})
    intro = '''<header style="max-width:1200px;margin:30px auto 0;padding:0 25px;font:16px/1.55 Arial;color:#203D4A">
<p style="letter-spacing:2px;color:#137C70;font-size:12px">JOEL CERRAGA / MARKET-NEUTRAL RESEARCH / MILESTONE 4</p>
<h1>The shape of relationships between stocks</h1>
<p>Rotate the landscape, hover over a layer and use the slider or playback to inspect 120 monthly observations from 2010–2019. Each cloud contains the same 24 stocks, represented by 126 trailing daily returns. The complete correlation distance supplies the geometry.</p>
<p>As Bubenik (2015) explains in <em>Statistical Topological Data Analysis using Persistence Landscapes</em>, birth–death intervals can be represented by ordered tent functions. Each peak belongs to a persistence interval; height is measured in distance units. It is not a return, probability or estimate of crash risk.</p>
<p>Rank is discrete. The surface joins layers for display; only the integer ranks have a mathematical definition here. Only five layers are displayed; all finite intervals enter the numeric feature summaries. Threshold ε is an edge distance, not a ball radius.</p></header>'''
    footer = '''<footer style="max-width:1200px;margin:0 auto 35px;padding:0 25px;font:15px/1.6 Arial;color:#425563">
<h2>Interpretation</h2><p>H1 records cycles that persist before triangles fill them. A triangle in a stock network is therefore not automatically a persistent H1 feature. All scales are held fixed during playback. Every frame ends at the displayed close; the reserved 2020–2025 observations are absent.</p>
<p>These are descriptive summaries. The study has not shown that topology forecasts returns or improves the trading strategy. Window sensitivity and simpler-control comparisons are reported in the notebook and working manuscript.</p>
<h2>References</h2><p>Bubenik, P. (2015) ‘Statistical topological data analysis using persistence landscapes’, <em>Journal of Machine Learning Research</em>, 16(3), pp. 77–102. Available at: <a href="https://jmlr.org/papers/v16/bubenik15a.html">https://jmlr.org/papers/v16/bubenik15a.html</a> (Accessed: 21 September 2026).</p></footer>'''
    html = html.replace("<body>", '<body style="margin:0;background:white">'+intro).replace("</body>", footer+"</body>")
    (out / "Persistence-Landscape-Explorer.html").write_text(html, encoding="utf-8")
    (out / "explorer-figure.json").write_text(fig.to_json(), encoding="utf-8")

    last = snapshots[-1]; h1 = np.asarray(last["h1"]).reshape(-1,2)
    fig = plt.figure(figsize=(12,5.2)); ax = fig.add_subplot(121, projection="3d"); diag = fig.add_subplot(122)
    xx, yy = np.meshgrid(grid, layers)
    ax.plot_surface(xx, yy, landscape(h1, grid), cmap="viridis", linewidth=0, alpha=.95)
    ax.set(xlabel="Threshold ε", ylabel="Rank k", zlabel="Height", title="First five landscape layers")
    ax.set_yticks(layers); ax.view_init(elev=22, azim=-60)
    diag.scatter(h1[:,0], h1[:,1], color="#137C70", s=28); diag.plot([0,2],[0,2],"--",color="#A4AFB5")
    diag.set(xlabel="Birth threshold", ylabel="Death threshold", title="Finite H1 diagram", xlim=(0,2), ylim=(0,2))
    diag.set_aspect("equal")
    fig.suptitle(f"Persistence at {last['date']} | 126-session window", x=.06, ha="left", fontsize=16)
    fig.subplots_adjust(left=.03, right=.95, bottom=.13, top=.85, wspace=.19)
    _save_figure(fig, out / "12-persistence-landscape.png"); plt.close(fig)

    rows = ["# Milestone 4: topology descriptors and simpler controls", "", 
            "The frozen protocol evaluates four features at 63, 126 and 252 sessions on 2,516 identical decision dates. The primary window remains 126 sessions. No trading overlay was introduced.", "",
            "## Primary-window correlations with mean correlation", "",
            "| Feature | Development Spearman | Validation Spearman |", "| --- | ---: | ---: |"]
    selected = correlations.loc[(correlations.window == 126) & (correlations.control == "mean_correlation")].pivot(index="feature",columns="phase",values="spearman")
    for feature in FEATURES:
        rows.append(f"| {LABELS[feature]} | {selected.loc[feature,'development']:.3f} | {selected.loc[feature,'validation']:.3f} |")
    rows += ["", "## Approximation using the three simpler controls", "", 
             "Ordinary least squares uses an intercept, mean correlation, mean stock volatility and SPY volatility. All centring, scaling and coefficients use development only. R² scores the topology feature, not a trading return.", "",
             "| Feature | Development R² | Validation R² |", "| --- | ---: | ---: |"]
    table = scores.loc[scores.window == 126].pivot(index="feature",columns="phase",values="r2")
    for feature in FEATURES:
        rows.append(f"| {LABELS[feature]} | {table.loc[feature,'development']:.3f} | {table.loc[feature,'validation']:.3f} |")
    rows += ["", "A negative validation R² means that the transferred development model has larger squared error than a constant equal to the validation feature mean. That mean is used only as a scoring benchmark. Unexplained variation is not evidence of predictive or economic value.", "", 
             "All window comparisons, fit coefficients, row-level residuals and numerical stability checks are retained in the companion CSV/JSON files. Overlapping windows make these observations dependent; no independent-observation significance claims are made.", ""]
    (out / "milestone-4-results.md").write_text("\n".join(rows), encoding="utf-8")
