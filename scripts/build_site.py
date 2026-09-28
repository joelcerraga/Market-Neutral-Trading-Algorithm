"""Build the static research site and previews from saved artifacts; no backtests."""
from pathlib import Path
from html import escape
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
URL = "https://joelcerraga.github.io/Market-Neutral-Trading-Algorithm/"
REPO = "https://github.com/joelcerraga/Market-Neutral-Trading-Algorithm"
PAPER = "paper/final/Market-Neutral-Trading-Algorithm-Final-Paper.pdf"
EXPLORERS = [
    {"slug": "correlations", "title": "Historical correlations", "number": "01",
     "subtitle": "How relationships between stocks change through time.", "period": "2010–2019", "frames": 120,
     "tag": "Correlation surface", "preview_date": "29 January 2010",
     "artifact": "outputs/historical/Historical-Correlation-Explorer.html",
     "notebook": "02-historical-baseline.ipynb", "data": "outputs/historical/correlation-snapshots.json",
     "summary": "Rotate the full correlation matrix and follow 120 monthly snapshots of the same 24-stock basket.",
     "intro": "Explore the changing relationships among 24 stocks using a rolling 126-session return window. The surface keeps the stock order fixed while the date slider moves through development and validation.",
     "read": "Height and colour show pairwise return correlation. The diagonal equals one because each stock is perfectly correlated with itself. The connecting surface is a visual interpolation between discrete stock pairs.",
     "points": ["Drag the surface to rotate it; hover to read a stock pair and its correlation.", "Use the date slider or Play to compare monthly snapshots from 2010–2019.", "The z-axis measures correlation, not expected return. Each frame uses information through the labelled close."],
     "meaning": "As Mantegna (1999) explains in <em>Hierarchical structure in financial markets</em>, return correlations support a distance representation of market relationships. This explorer displays the complete correlation matrix; the strategy constructs a separate sparse neighbour graph from it.",
     "limit": "The 24 companies were selected from survivors. Shared movement in this basket does not establish diversification under every future condition or a profitable signal.", "references": ["mantegna"]},
    {"slug": "graph-diffusion", "title": "Graph diffusion", "number": "02",
     "subtitle": "From connected stocks to a relative trading score.", "period": "2010–2019", "frames": 120,
     "tag": "Network & signal", "preview_date": "29 January 2010",
     "artifact": "outputs/comparison/Graph-Diffusion-Explorer.html",
     "notebook": "03-graph-comparison.ipynb", "data": "outputs/comparison/graph-snapshots.json",
     "summary": "Inspect the stock network, observed shocks and graph-smoothed scores before portfolio constraints are applied.",
     "intro": "Follow 120 monthly snapshots of the graph signal. The network links stocks with sufficiently strong positive correlations; diffusion then smooths the observed shock across those relationships.",
     "read": "Height and colour show the graph score before portfolio projection. The lines on the zero plane show retained connections. Horizontal node locations are fixed research-group positions for display, not estimated market distances.",
     "points": ["Rotate the network and hover over a stock to inspect its score.", "Compare the observed and smoothed shock in the paired score bars.", "A positive score proposes a long direction; the final weight can differ after dollar/beta projection and position limits."],
     "meaning": "Kondor and Lafferty (2002), in <em>Diffusion Kernels on Graphs and Other Discrete Input Spaces</em>, provide the matrix-exponential smoothing relationship. This project uses diffusion time τ = 1 for the primary case. Reversing the difference between a shock and its smoothed counterpart is the project's trading hypothesis.",
     "limit": "The primary graph strategy loses money after costs in both displayed research phases. Its small validation improvement is uncertain. The visual explains signal construction; it does not establish an investment edge.", "references": ["kondor"]},
    {"slug": "persistence-landscapes", "title": "Persistence landscapes", "number": "03",
     "subtitle": "The shape of stock relationships across scales.", "period": "2010–2019", "frames": 120,
     "tag": "Topology / development", "preview_date": "29 January 2010",
     "artifact": "outputs/topology/Persistence-Landscape-Explorer.html",
     "notebook": "04-topology-features.ipynb", "data": "outputs/topology/monthly-diagrams.json",
     "summary": "Explore ranked persistence layers alongside the birth–death diagram for each monthly asset cloud.",
     "intro": "View 120 monthly persistence landscapes from development and validation. The full correlation-distance geometry of the same 24 stocks supplies the filtration, using the primary 126-session return window.",
     "read": "Threshold is a distance scale; rank orders the landscape layers; height is a persistence-landscape value in distance units. The companion diagram shows where H1 intervals are born and die. Rank is discrete and the surface joining ranks is interpolation.",
     "points": ["Rotate the landscape, hover over a layer and compare the paired birth–death diagram.", "Move through the date slider; axes remain fixed during playback.", "H1 tracks loops that persist before triangles fill them. A triangle in a network is not automatically a persistent H1 feature."],
     "meaning": "As Bubenik (2015) explains in <em>Statistical topological data analysis using persistence landscapes</em>, birth–death intervals can be represented by ordered tent functions. These landscapes visualise that representation, with the full set of finite intervals retained in the numerical descriptors.",
     "limit": "These are descriptive summaries. The study has not established that topology forecasts returns or improves the trading rule. Earlier explorer text describes the holdout status at that milestone; the final stage has now been completed.", "references": ["bubenik"]},
    {"slug": "final-test-landscapes", "title": "Final-test landscapes", "number": "04",
     "subtitle": "The topology study carried into the final evaluation.", "period": "2020–2025", "frames": 72,
     "tag": "Topology / final test", "preview_date": "31 January 2020",
     "artifact": "outputs/final/topology/Final-Test-Landscape-Explorer.html",
     "notebook": "05-final-evaluation.ipynb", "data": "outputs/final/topology/monthly-diagrams.json",
     "summary": "Explore 72 final-period landscapes using the frozen construction and the original stock basket.",
     "intro": "Inspect the 72 monthly observations in the final 2020–2025 evaluation. The asset basket, primary 126-session window and feature construction remain fixed, and the twelve development-fitted control models transfer without refitting.",
     "read": "Each peak represents a persistence interval. Only five ranked layers are drawn, while every finite interval enters the numerical features. Height is neither a return forecast nor a probability of a market crash.",
     "points": ["Use the date slider or playback controls to move through all six calendar years.", "Rotate and hover to compare threshold, rank and landscape height with the birth–death diagram.", "Every frame uses returns available through its displayed close; the complete correlation distance supplies its geometry."],
     "meaning": "Bubenik (2015), in <em>Statistical topological data analysis using persistence landscapes</em>, supplies the landscape representation. The transfer study then asks whether the previously fitted descriptor relationships persist in later observations. The resulting geometry remains a diagnostic; no topology trading overlay was added.",
     "limit": "The primary graph strategy's final CAGR is −4.80% after the declared costs, versus −5.57% for the baseline. The paired improvement remains uncertain and none of the four necessary evidence conditions was met. The final period is now observed.", "references": ["bubenik"]},
]
REFERENCES = {
 "mantegna": 'Mantegna, R.N. (1999) ‘Hierarchical structure in financial markets’, <em>The European Physical Journal B</em>, 11, pp. 193–197. doi: <a href="https://doi.org/10.1007/s100510050929">10.1007/s100510050929</a>.',
 "kondor": 'Kondor, R.I. and Lafferty, J.D. (2002) ‘Diffusion Kernels on Graphs and Other Discrete Input Spaces’, in <em>Proceedings of the 19th International Conference on Machine Learning</em>, pp. 315–322. doi: <a href="https://doi.org/10.5555/645531.655996">10.5555/645531.655996</a>.',
 "bubenik": 'Bubenik, P. (2015) ‘Statistical topological data analysis using persistence landscapes’, <em>Journal of Machine Learning Research</em>, 16(3), pp. 77–102. Available at: <a href="https://jmlr.org/papers/v16/bubenik15a.html">https://jmlr.org/papers/v16/bubenik15a.html</a> (Accessed: 28 September 2026).',
 "politis": 'Politis, D.N. and Romano, J.P. (1994) ‘The Stationary Bootstrap’, <em>Journal of the American Statistical Association</em>, 89(428), pp. 1303–1313. doi: <a href="https://doi.org/10.1080/01621459.1994.10476870">10.1080/01621459.1994.10476870</a>.',
}


def write(path, content):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def shell(title, description, body, path="", depth=0, graph=False):
    p = "../" * depth
    thumbnail = "interactive-graphs.png" if graph else "market-neutral-research.png"
    nav = [(p + "index.html", "Overview", not graph), (p + "explorers/", "Interactive graphs", graph),
           (p + PAPER, "Paper ↗", False), (REPO, "GitHub ↗", False)]
    links = "".join(f'<a href="{href}"' + (' aria-current="page"' if active else '') + f'>{label}</a>' for href, label, active in nav)
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Joel Cerraga</title><meta name="description" content="{escape(description, quote=True)}">
<meta name="author" content="Joel Cerraga"><meta name="theme-color" content="#102b3e">
<link rel="canonical" href="{URL}{path}"><meta property="og:type" content="website"><meta property="og:site_name" content="Market-Neutral Research">
<meta property="og:title" content="{escape(title, quote=True)}"><meta property="og:description" content="{escape(description, quote=True)}"><meta property="og:url" content="{URL}{path}">
<meta property="og:image" content="{URL}assets/thumbnails/{thumbnail}"><meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1774"><meta property="og:image:height" content="887"><meta property="og:image:alt" content="{escape(title, quote=True)} by Joel Cerraga, with conceptual teal research geometry on white">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title, quote=True)}"><meta name="twitter:description" content="{escape(description, quote=True)}"><meta name="twitter:image" content="{URL}assets/thumbnails/{thumbnail}">
<link rel="icon" type="image/svg+xml" href="{p}assets/favicon.svg"><link rel="stylesheet" href="{p}assets/site.css"><script src="{p}assets/site.js" defer></script></head>
<body><a class="skip-link" href="#main">Skip to content</a><header class="site-header"><div class="wrap nav-inner">
<a class="brand" href="{p}index.html"><img class="brand-mark" src="{p}assets/favicon.svg" width="34" height="34" alt=""><span>Market-Neutral Research<small>Joel Cerraga</small></span></a>
<button class="nav-toggle" type="button" aria-controls="site-nav" aria-expanded="false">Menu</button><nav class="nav-links" id="site-nav" aria-label="Main navigation">{links}</nav></div></header>
<main id="main">{body}</main><footer class="site-footer"><div class="wrap footer-inner"><p>Joel Cerraga · Quantitative research · 2026</p><div class="footer-links"><a href="{p}explorers/">Interactive graphs</a><a href="{p}{PAPER}">Final paper</a><a href="{REPO}">Source &amp; reproduction</a></div></div></footer></body></html>\n'''


def cards(prefix="", selected=None):
    html = []
    for item in selected or EXPLORERS:
        html.append(f'''<a class="graph-card" href="{prefix}explorers/{item['slug']}/"><div class="card-image"><img src="{prefix}assets/previews/{item['slug']}.svg" width="900" height="520" alt="Static preview of {item['title'].lower()}, {item['preview_date']}" loading="lazy"><span class="card-tag">{item['tag']}</span></div><div class="card-body"><p class="card-meta">{item['number']} / {item['period']} · {item['frames']} monthly frames</p><h3>{item['title']}</h3><p>{item['summary']}</p><div class="card-bottom"><span>Open explorer</span><span aria-hidden="true">↗</span></div></div></a>''')
    return '<div class="card-grid">' + "".join(html) + '</div>'


def references(keys):
    return '<section class="references" aria-label="References"><h2>References</h2>' + ''.join('<p>' + REFERENCES[k] + '</p>' for k in keys) + '</section>'


def landing():
    body = f'''<section class="hero"><div class="wrap hero-grid"><div class="hero-copy"><p class="eyebrow">Equity signals · Graph diffusion · Topology</p><h1>Market-Neutral<br><span>Trading Algorithm</span></h1><p class="lede">A study of equity reversal and the changing structure of stock relationships, from constrained portfolios to interactive 3D diagnostics.</p><div class="button-row"><a class="button" href="explorers/">Explore the graphs <span aria-hidden="true">↗</span></a><a class="button secondary" href="{PAPER}">Read the paper</a></div><p class="hero-note">Research by Joel Cerraga · Five completed research milestones</p></div><figure class="hero-visual" style="margin:0"><img src="assets/previews/graph-diffusion.svg" width="900" height="520" alt="Actual graph-score snapshot for the 24-stock basket on 29 January 2010"><figcaption class="visual-label"><span>GRAPH DIFFUSION / SAVED SNAPSHOT</span><span>29 JAN 2010</span></figcaption></figure></div></section>
<div class="wrap"><div class="stat-strip"><div class="stat"><strong>24</strong><span>stocks, with SPY as benchmark</span></div><div class="stat"><strong>4</strong><span>interactive research explorers</span></div><div class="stat"><strong>22</strong><span>declared final evaluation cases</span></div><div class="stat"><strong>54</strong><span>pages in the final paper</span></div></div></div>
<section class="section"><div class="wrap question-grid"><div><p class="eyebrow">The research question</p><h2>Can market structure improve a reversal signal?</h2><p>A recent stock move can be compared with the moves of connected stocks. The study asks whether a graph-based version of reversal improves on a simpler baseline once both share the same constraints, execution timing and costs.</p><p>As Mantegna (1999) explains in <em>Hierarchical structure in financial markets</em>, correlations can describe relationships between assets. That representation motivates the analysis; it does not establish a trading advantage.</p></div><div class="method-list"><div class="method-item"><span class="method-num">01</span><div><h3>Construct a constrained portfolio</h3><p>Target dollar and estimated SPY-beta neutrality, with gross exposure and individual position limits. Realised beta can still drift.</p></div></div><div class="method-item"><span class="method-num">02</span><div><h3>Test the network hypothesis</h3><p>Compare baseline reversal with graph diffusion under the same delayed execution, trading fees and short-borrow assumptions.</p></div></div><div class="method-item"><span class="method-num">03</span><div><h3>Inspect the geometry</h3><p>Use correlation surfaces and persistent homology to describe changing stock relationships, then compare descriptors with simpler controls.</p></div></div></div></div></section>
<section class="section tinted" id="findings"><div class="wrap"><div class="question-grid"><div><p class="eyebrow">Final evaluation / 2020–2025</p><h2>The proposed trading advantage was not demonstrated.</h2><p class="muted">Both primary strategies lost money after costs. The graph strategy's smaller observed loss does not establish a reliable improvement, and none of the four predeclared necessary evidence conditions was met.</p><p class="muted">As Politis and Romano (1994) describe in <em>The Stationary Bootstrap</em>, random blocks support resampling dependent observations. Here the paired, family-adjusted interval for the annualised arithmetic improvement spans <strong>−2.14 to +3.85 percentage points</strong>.</p></div><div class="result-box"><h3>Annualised compound return</h3><p class="muted small">Primary cases · after declared costs</p><div class="result-numbers"><div class="result-number"><strong>−5.57%</strong><span>Baseline reversal</span></div><div class="result-number"><strong>−4.80%</strong><span>Graph diffusion, τ = 1</span></div></div><p class="result-note">5 bps per dollar traded · 2% annual short borrow. The confidence interval describes an arithmetic-mean difference, not a difference in compound returns.</p><a class="text-link" href="{REPO}/blob/main/outputs/final/milestone-5-results.md">Read the complete findings <span aria-hidden="true">↗</span></a></div></div></div></section>
<section class="section"><div class="wrap"><div class="section-heading"><div><p class="eyebrow">Interactive research</p><h2>Four views of market structure.</h2></div><p>Rotate, hover and move through time. Each explorer has its own context and interpretation.</p></div>{cards()}<p class="graph-hint">All four explorers use the saved research artifacts. Their axes describe correlation, signal scores or persistence geometry.</p></div></section>
<section class="section tinted"><div class="wrap"><div class="section-heading"><div><p class="eyebrow">Read. Inspect. Reproduce.</p><h2>The complete research record.</h2></div></div><div class="resource-grid"><article class="resource"><h3>The final paper</h3><p>Methodology, numbered equations, results, setbacks, discussion and conclusion, with Harvard references.</p><a href="{PAPER}">Open the PDF ↗</a></article><article class="resource"><h3>Code and notebooks</h3><p>Five executed notebooks, frozen protocols, focused tests and every retained research output.</p><a href="{REPO}">Browse the repository ↗</a></article><article class="resource"><h3>Decisions and limitations</h3><p>The design forks, failures and mitigations that shaped each milestone of the study.</p><a href="{REPO}/blob/main/docs/milestone-decisions.md">Read the decision log ↗</a></article></div><div class="callout" style="margin-top:35px"><p><strong>Scope of the evidence.</strong> This is a retrospective study of a fixed survivor basket using adjusted prices. It lacks a point-in-time universe, comprehensive delisting outcomes and historical stock-level borrow availability. All evaluation periods are now observed. The public repository includes saved results and synthetic tests; exact historical replay requires the separately retained input snapshots.</p></div></div></section>
<div class="wrap section">{references(['mantegna','politis'])}</div>'''
    write("index.html", shell("Market-Neutral Trading Algorithm", "Joel Cerraga's research into constrained equity reversal, graph diffusion and persistent homology. Explore the results, final paper and four interactive 3D graphs.", body))


def gallery():
    body = f'''<section class="hero"><div class="wrap catalog-intro"><div><p class="eyebrow">The interactive companion</p><h1>Explore the structure<br><span style="color:var(--teal)">of markets.</span></h1><p class="lede">Four dedicated explorers connect the research method to its visual evidence. Choose a view, rotate it and follow the monthly sequence.</p><div class="tag-row"><span class="tag">24-stock basket</span><span class="tag">126-session primary window</span><span class="tag">Saved research outputs</span></div></div><img src="../assets/thumbnails/interactive-graphs.png" width="1774" height="887" alt="Interactive Graphs by Joel Cerraga: conceptual teal cover illustration on white"></div></section><section class="section" style="padding-top:10px"><div class="wrap">{cards('../')}<div class="callout" style="margin-top:32px"><p><strong>How to read these views.</strong> A correlation surface shows co-movement; a graph score explains a proposed signal; a persistence landscape describes geometry. None of these heights is a forecast probability. The final trading results remain negative after the declared costs.</p></div><div class="button-row"><a class="button secondary" href="../{PAPER}">Read the interpretation in the paper</a><a class="button secondary" href="../index.html#findings">See the final results</a></div></div></section>'''
    write("explorers/index.html", shell("Interactive Graphs — Market-Neutral Research", "Explore four interactive 3D views: historical correlations, graph diffusion, persistence landscapes and the final 2020–2025 test.", body, "explorers/", 1, True))


def detail(item, index):
    p = "../../"
    next_item = EXPLORERS[(index + 1) % len(EXPLORERS)]
    points = ''.join('<li>' + x + '</li>' for x in item['points'])
    body = f'''<section class="page-intro"><div class="wrap"><p class="breadcrumb"><a href="../../index.html">Overview</a><span>/</span><a href="../">Interactive graphs</a><span>/</span>{item['number']}</p><p class="eyebrow">{item['tag']} / {item['period']}</p><h1>{item['title']}</h1><p class="lede">{item['intro']}</p><div class="tag-row"><span class="tag">{item['frames']} monthly frames</span><span class="tag">24 stocks</span><span class="tag">126-session primary window</span></div></div></section>
<section class="section" style="padding-top:0"><div class="wrap"><div class="viewer"><div class="viewer-toolbar"><strong>{item['subtitle']}</strong><a href="{p}{item['artifact']}" target="_blank" rel="noopener">Open standalone ↗</a></div><div class="preview-stage"><img src="{p}assets/previews/{item['slug']}.svg" width="900" height="520" alt="Static preview of {item['title'].lower()} on {item['preview_date']}"><button type="button" class="button" data-launch>Load interactive graph <span aria-hidden="true">↗</span></button><p>Static preview: {item['preview_date']}. Load the explorer to rotate, zoom and move through dates.</p></div><p class="loading-status" role="status" aria-live="polite"></p><div class="viewer-scroll"><iframe class="viewer-frame" title="{item['title']} interactive research graph" data-src="{p}{item['artifact']}" hidden></iframe></div><noscript><p style="padding:20px">JavaScript is required for the controls. <a href="{p}{item['artifact']}">Open the standalone graph</a>, or view the static preview and paper.</p></noscript></div><p class="graph-hint">On a smaller screen, scroll horizontally inside the graph or open the standalone view for more space.</p><div class="read-grid"><div><h2>How to read the graph</h2><p>{item['read']}</p><ul>{points}</ul></div><div><h2>What the relationship means</h2><p>{item['meaning']}</p></div></div><div class="callout"><p>{item['limit']}</p></div><div class="detail-links"><a href="{REPO}/blob/main/notebooks/{item['notebook']}">Open the notebook ↗</a><a href="{p}{item['data']}" download>Download the saved graph data</a><a href="{p}{PAPER}">Read the final paper ↗</a></div><div class="section" style="padding-bottom:0">{references(item['references'])}</div><div class="next-explorer"><a href="../">← All explorers</a><a href="../{next_item['slug']}/">Next: {next_item['title']} →</a></div></div></section>'''
    write(f"explorers/{item['slug']}/index.html", shell(item['title'] + " — Market-Neutral Research", item['summary'], body, f"explorers/{item['slug']}/", 2, True))


def previews():
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": "#102b3e", "axes.labelcolor": "#526775", "xtick.color": "#526775", "ytick.color": "#526775", "svg.fonttype": "none", "svg.hashsalt": "market-neutral-site-v1"})
    cmap = LinearSegmentedColormap.from_list("market", ["#cce9e4", "#58a59c", "#174f66"])
    def setup():
        fig = plt.figure(figsize=(9, 5.2), facecolor="white")
        ax = fig.add_subplot(111, projection="3d")
        ax.view_init(elev=25, azim=-54)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.fill = False
            axis.pane.set_edgecolor("#e6eeef")
            axis._axinfo["grid"].update(color="#e0e9eb", linewidth=.5)
        ax.tick_params(labelsize=8, pad=1)
        fig.subplots_adjust(left=.02, right=.96, top=.98, bottom=.04)
        return fig, ax
    def save(fig, slug):
        target = ROOT / f"assets/previews/{slug}.svg"
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, format="svg", metadata={"Date": None, "Creator": "Market-Neutral research site; saved data preview"})
        plt.close(fig)
    d = json.loads((ROOT / "outputs/historical/correlation-snapshots.json").read_text())
    fig, ax = setup()
    x, y = np.meshgrid(np.arange(24), np.arange(24))
    ax.plot_surface(x, y, np.asarray(d['correlations'][0]), cmap=cmap, linewidth=.25, edgecolor="#ffffff66", vmin=-1, vmax=1)
    ax.set(xlabel="Stock index", ylabel="Stock index", zlabel="Correlation", zlim=(-1, 1), xticks=[0, 8, 16, 23], yticks=[0, 8, 16, 23], zticks=[-1, 0, 1])
    save(fig, "correlations")
    d = json.loads((ROOT / "outputs/comparison/graph-snapshots.json").read_text())
    s = d['snapshots'][0]; xy = np.asarray(d['layout_xy']); scores = np.asarray(s['graph_score']); adjacency = np.asarray(s['adjacency'])
    fig, ax = setup()
    for i in range(24):
        for j in range(i + 1, 24):
            if adjacency[i, j] > 0:
                ax.plot(xy[[i, j], 0], xy[[i, j], 1], [0, 0], color="#bfd5d3", alpha=.7, linewidth=.6)
    for i in range(24):
        ax.plot([xy[i, 0]]*2, [xy[i, 1]]*2, [0, scores[i]], color="#83b8b0", linewidth=.8)
    ax.scatter(xy[:, 0], xy[:, 1], scores, c=scores, cmap=cmap, s=42, edgecolors="white", linewidths=.7, depthshade=False)
    ax.set(xlabel="Fixed display x", ylabel="Fixed display y", zlabel="Graph score")
    ax.set_box_aspect((1.25, 1, .7))
    save(fig, "graph-diffusion")
    for slug, source in [("persistence-landscapes", "outputs/topology/explorer-figure.json"), ("final-test-landscapes", "outputs/final/topology/explorer-figure.json")]:
        data = json.loads((ROOT / source).read_text())['data'][0]
        x = np.asarray(data['x']); z = np.asarray(data['z']); ranks = np.arange(1, len(z)+1)
        fig, ax = setup()
        for i, rank in enumerate(ranks):
            points = [(x[0], rank, 0)] + list(zip(x, np.full(len(x), rank), z[i])) + [(x[-1], rank, 0)]
            poly = Poly3DCollection([points], facecolors=cmap(.25 + .14*i), edgecolors="#327a76", linewidth=.55, alpha=.8)
            ax.add_collection3d(poly)
        ax.set(xlim=(0, 2), ylim=(1, 5), zlim=(0, data['cmax']), xlabel="Distance threshold", ylabel="Layer rank", zlabel="Landscape height", xticks=[0, 1, 2], yticks=[1, 3, 5])
        ax.set_box_aspect((1.4, 1, .65))
        save(fig, slug)


def build(with_previews=True):
    if with_previews:
        previews()
    landing()
    gallery()
    for i, item in enumerate(EXPLORERS):
        detail(item, i)
    locations = [URL, URL + 'explorers/'] + [URL + 'explorers/' + item['slug'] + '/' for item in EXPLORERS]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + location + '</loc></url>' for location in locations) + '</urlset>\n')
    print("Built six static pages and " + ("four data-derived previews." if with_previews else "reused existing previews."))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-previews', action='store_true')
    args = parser.parse_args()
    build(not args.skip_previews)
