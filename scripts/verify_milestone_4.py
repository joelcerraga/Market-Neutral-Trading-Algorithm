"""Verify the delivered research artifacts without rerunning model selection."""
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys
import numpy as np
import pandas as pd
import nbformat
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from market_neutral.historical import sha256, load_protocol
from market_neutral.topology import load_topology_protocol


def verify():
    p = load_topology_protocol(ROOT)
    h = load_protocol(ROOT)
    out = ROOT / "outputs/topology"
    manifest = json.loads((out / "run-manifest.json").read_text())
    assert manifest["input_sha256"] == p["input_sha256"]
    assert sha256(ROOT / "data/processed/adjusted-prices.csv") == p["input_sha256"]
    for name, expected in manifest["files"].items():
        assert sha256(out / name) == expected, name
    features = pd.read_csv(out / "features.csv", index_col="date", parse_dates=True)
    assert len(features) == 7548 and np.isfinite(features.to_numpy()).all()
    calendars = [features.loc[features.window == w].index for w in p["windows"]]
    assert all(calendars[0].equals(c) for c in calendars[1:])
    assert calendars[0].min() == pd.Timestamp("2010-01-04")
    assert calendars[0].max() == pd.Timestamp("2019-12-31")
    assert features.essential_h0.eq(1).all() and features.finite_h0.eq(23).all()
    assert features.zero_h0_merges.eq(0).all()
    for name, count in [("control-correlations.csv",72),("control-model-scores.csv",24),
                        ("window-sensitivity.csv",16),("diagram-stability.csv",480)]:
        assert len(pd.read_csv(out / name)) == count, name
    models = json.loads((out / "control-models.json").read_text())
    assert len(models) == 12
    assert all(m["fitted_rows"] == 1762 and m["fitted_last_date"] == "2016-12-30" for m in models.values())
    checks = pd.read_csv(out / "diagram-stability.csv")
    assert (checks.bottleneck_distance <= checks.max_distance_change + 2e-6).all()
    prices = pd.read_csv(ROOT / "data/processed/adjusted-prices.csv", index_col=0, parse_dates=True)
    assert prices.index.max() < pd.Timestamp(h["phases"]["final_holdout"][0])
    pngs = {}
    for path in sorted(out.glob("*.png")):
        with Image.open(path) as image:
            size = image.size
            image.verify()
        assert min(size) >= 500 and path.stat().st_size > 1000
        pngs[path.name] = {"bytes":path.stat().st_size,"pixels":size,"sha256":sha256(path)}
    assert len(pngs) == 4
    fig = json.loads((out / "explorer-figure.json").read_text())
    snapshots = json.loads((out / "monthly-diagrams.json").read_text())
    assert len(fig["frames"]) == 120 and len(snapshots) == 360
    assert len(fig["layout"]["sliders"][0]["steps"]) == 120
    assert len(fig["layout"]["updatemenus"][0]["buttons"]) == 2
    for frame in fig["frames"]:
        snapshot = snapshots[frame["name"] + "|126"]
        bars = np.asarray(snapshot["h1"]).reshape(-1,2)
        x = np.asarray(frame["data"][0]["x"])
        layers = np.asarray(frame["data"][0]["z"])
        assert layers.shape == (5,401) and np.all(layers >= 0)
        # Check each rendered sample directly against the interval definition.
        for j, threshold in enumerate(x):
            ordered = sorted([max(0., min(threshold-b, d-threshold)) for b,d in bars], reverse=True)
            expected = (ordered + [0.]*5)[:5]
            np.testing.assert_allclose(layers[:,j], expected, atol=1e-14)
        np.testing.assert_allclose(frame["data"][1]["x"], bars[:,0])
        np.testing.assert_allclose(frame["data"][1]["y"], bars[:,1])
    html = (out / "Persistence-Landscape-Explorer.html").read_text()
    assert "Plotly.addFrames" in html and "plotly.js" in html
    assert not re.search(r"<script\b[^>]*\bsrc=",html,re.I)
    assert "<h2>References</h2>" in html
    manuscript = (ROOT / "paper/manuscript.md").read_text()
    prose = re.sub(r"```.*?```", "", manuscript, flags=re.S)
    assert not re.search(r"\[\d+\]",prose)
    assert "<!--" not in manuscript
    counts = {}
    for kind, count in [("Equation",27),("Table",19),("Listing",12)]:
        numbers = [int(n) for n in re.findall(rf"^{kind} (\d+)\.",manuscript,flags=re.M)]
        assert numbers == list(range(1,count+1))
        counts[kind.lower()] = count
    figure_links = re.findall(r"!\[Figure (\d+)\. [^\]]+\]\(([^)]+)\)",manuscript)
    assert [int(n) for n,_ in figure_links] == list(range(1,13))
    for _, path in figure_links:
        target = (ROOT / "paper" / path).resolve()
        with Image.open(target) as image: image.verify()
    counts["figure"] = 12
    bibliography = manuscript.split("## References\n\n",1)[1].strip()
    assert bibliography == (ROOT / "paper/references-harvard.md").read_text().strip()
    references = bibliography.split("\n\n")
    assert len(references) == 22
    assert references == sorted(references,key=lambda s:s.split(" (")[0].casefold())
    for entry in references:
        assert re.match(r"[A-Z][^\n]+\(\d{4}\) ",entry)
        assert not any(term in entry for term in ["Primary source","Primary data","Not a scientific paper","Evidence:"])
    notebook_checks = {}
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path,as_version=4); nbformat.validate(notebook)
        codes = [c for c in notebook.cells if c.cell_type == "code"]
        assert all(c.execution_count is not None for c in codes)
        assert not any(o.output_type == "error" for c in codes for o in c.outputs)
        refs = [c for c in notebook.cells if c.cell_type == "markdown" and c.source.startswith("## References\n")]
        assert len(refs) == 1
        notebook_checks[path.name] = {"executed_cells":len(codes),"errors":0,"harvard_reference_list":True}
    assert notebook_checks["04-topology-features.ipynb"]["executed_cells"] == 10
    decisions = (ROOT / "docs/milestone-decisions.md").read_text()
    assert all(f"## Milestone {n}" in decisions for n in range(1,5))
    record = {"verified_utc":datetime.now(timezone.utc).isoformat(), "status":"passed",
              "feature_rows":len(features), "common_dates":len(calendars[0]),
              "numerical_output_hashes_verified":len(manifest["files"]), "diagram_bound_checks":len(checks),
              "pngs":pngs, "interactive_frames":120, "landscape_samples_verified":120*5*401,
              "browser_interaction":"Not executed in the build environment; numerical data and HTML configuration verified",
              "manuscript_counts":counts,"harvard_references":len(references),
              "notebooks":notebook_checks,"decision_log_milestones":[1,2,3,4],
              "pdf_compiled":False,"final_holdout_acquired_or_evaluated":False,
              "snapshot_sha256":p["input_sha256"],"protocol_sha256":manifest["protocol_sha256"]}
    (ROOT / "validation/milestone-4-artifacts.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record,indent=2))


if __name__ == "__main__":
    verify()
