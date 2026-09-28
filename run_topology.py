"""Reproduce Milestone 4 from the frozen 2009–2019 cache without network access."""
from pathlib import Path
import json
from market_neutral.historical import assemble_dataset
from market_neutral.topology import run_topology

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    dataset, _ = assemble_dataset(ROOT)
    frame, manifest = run_topology(ROOT, dataset)
    from market_neutral.topology_plots import create_topology_figures
    create_topology_figures(ROOT)
    print(json.dumps(manifest, indent=2))
