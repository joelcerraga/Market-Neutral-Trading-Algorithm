# Market-Neutral Trading Algorithm: local setup

## 1. Extract and inspect

Extract your ZIP and open the inner `Market-Neutral-Trading-Algorithm` folder in Visual Studio Code. `README.md`, `run_final.py` and `market_neutral/` should be together. `PACKAGE_README.md` identifies whether you have the **GitHub** or **Complete** archive.

Read the [final paper](paper/final/Market-Neutral-Trading-Algorithm-Final-Paper.pdf) and [concise findings](outputs/final/milestone-5-results.md). Browse the five executed notebooks and the [output index](docs/OUTPUTS.md). Downloaded HTML explorers open directly in a browser; they include their JavaScript and do not require Python.

Python 3.12 is recommended; Python 3.11–3.13 is the declared range. Open **Terminal → New Terminal** at the project root. Run commands separately.

## 2. Windows: verify and run the public example

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe scripts/verify_release.py
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe run_research.py --output tmp/synthetic-demo
```

These commands call the environment directly, so PowerShell activation and execution-policy changes are unnecessary. If Python 3.12 is unavailable, select an installed supported interpreter.

## 3. macOS or Linux: verify and run the public example

```bash
python3 -m venv .venv
.venv/bin/python scripts/verify_release.py
.venv/bin/python -m pip install -r requirements-notebook.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python run_research.py --output tmp/synthetic-demo
```

Select a supported interpreter if `python3` is outside the declared range. The package verifier uses only Python's standard library. Dependencies require installation once; the tests and synthetic example do not download market data. The synthetic generator deliberately contains mean reversion, so its performance does not establish a market trading advantage.

The focused suite should report **41 tests / OK**. The example writes its own files under `tmp/synthetic-demo`, leaving all delivered research outputs intact. The manifest verifier checks delivered bytes; running an experiment into its original output folder or editing tracked files may change them. Unlisted extra files are not checked by the manifest.

## 4. Exact historical replay: Complete archive

Use the **Complete** archive in a separate folder. Keep its `data/` directory structure unchanged, including the literal final-cache directory name recorded in the frozen protocol. It contains both coherent adjusted-price vintages and both processed snapshots. With the environment above installed, run:

```powershell
.\.venv\Scripts\python.exe run_final.py
```

On macOS/Linux, use `.venv/bin/python run_final.py` instead. This audits cached inputs and performs no network acquisition. It regenerates files under `outputs/final/`; retain an untouched extracted copy if you want to compare release hashes afterwards.

The final stage retains 22 cases and 1,508 sessions per ledger, all six calendar years, paired and family-adjusted intervals, cost/exposure diagnostics, 4,524 topology rows, 288 diagram-bound checks, four figures and the 72-frame explorer. Default-cost CAGR is approximately −5.57% for the baseline and −4.80% for graph τ = 1. All four necessary evidence conditions are false. These are the retained research findings.

The **GitHub** archive omits the input caches and cannot directly replay the historical study. Reacquiring observations from the provider can produce a revised vintage; the final acquisition script itself checks the original snapshot before continuing. A mismatch needs a new documented experiment, not a bypass of the retained locks. See [data/README.md](data/README.md).

## 5. Notebooks

All five supplied notebooks retain their executed outputs and can be read without a rerun. To rerun a notebook, install Microsoft's Python and Jupyter VS Code extensions, open it, choose **Select Kernel → Python Environments** and select this project's `.venv` executable.

The foundation notebook uses synthetic data. Historical notebooks 02–05 require the corresponding data from the Complete archive. The fifth notebook contains ten executed code cells. Its original build used sequential IPython execution with captured rich outputs because kernel sockets were unavailable; a local interactive kernel remains environment-dependent. The trusted in-process alternative, from the project root with the environment selected, is:

```bash
python scripts/execute_notebook.py notebooks/05-final-evaluation.ipynb
```

## 6. Paper source and compilation

The supplied PDF is the final 55-page revision: March 2026 on the title page, separate pages for every “List of…” section and chapter, and the appendix after the reference list. You do not need LaTeX to read it.

Install XeLaTeX and the fonts described in [paper/final/README.md](paper/final/README.md). To compile the included typesetting source without the research dependencies, run from the project root:

```bash
python paper/final/compile_source.py
```

For manuscript changes, edit `paper/sections/`, install `requirements-paper.txt`, then use `python paper/build_paper.py`. This rebuilds the manuscript and PDF from the saved outputs; it does not rerun the trading study. Font paths need adjustment outside the original Linux environment, and different TeX/font versions may change pagination.

`validation/final-paper-validation.json` records the delivered document checks. The broader `scripts/verify_final_paper.py` also checks private frozen files and fresh TeX auxiliary files; run it only with the Complete archive after compilation. The package verifier checks the delivered PDF's exact hash without those dependencies. Earlier `verify_milestone_*` scripts validate historical release snapshots, whose manuscript counts and status text can differ from today's final assembly.

## 7. Earlier milestones and publication

`run_research.py` is the synthetic foundation; `run_historical.py` the baseline; `run_comparison.py` the 44 earlier comparison cases; and `run_topology.py` the original descriptor study. Read notebooks 01–04 in order for their historical context. The fifth stage has now consumed the reserved test period; historical references to an untouched holdout describe that earlier stage only.

Use [GITHUB_UPLOAD.md](GITHUB_UPLOAD.md) for publication. Use the GitHub archive for the repository and keep the Complete archive for personal replay. [Release notes](docs/release-notes.md) record the packaging decisions and remaining limitations.
