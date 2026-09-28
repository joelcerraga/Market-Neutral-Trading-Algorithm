# Historical input data and reproduction

The research uses 24 retrospectively selected surviving stocks and SPY. These inputs are adjusted-price observations acquired from the Yahoo Finance chart endpoint. The original 2009–2019 acquisition and final acquisition covering 31 December 2018–31 December 2025 are separate frozen vintages.

## What each package contains

| Files | GitHub archive | Complete archive |
| --- | --- | --- |
| `download-manifest.json`, `final-download-manifest.json`, `final-snapshot.lock.json` | Included | Included |
| `cache/` | Omitted | Included: original ticker CSVs and metadata |
| `processed/adjusted-prices.csv` | Omitted | Included: original aligned input |
| `final-cache (separate from original frozen cache)/` | Omitted | Included: final ticker CSVs and metadata |
| `final-processed/adjusted-prices.csv` | Omitted | Included: final aligned input |

The 102 omitted files are vendor data inputs and cache metadata. Their omission separates the public research artifacts from the personal exact-data archive; no redistribution licence is supplied for the vendor observations. Manifests retain acquisition provenance, corporate-action metadata, row counts and hashes. All research outputs remain in both archives, including derived returns, portfolio ledgers and synthetic input data.

The final-cache directory name includes the parenthetical text literally. It is recorded in the frozen protocol. Do not rename it for convenience.

## Three reproducibility levels

1. **Inspect:** either package contains the paper, five executed notebooks, every saved output and four offline interactive explorers.
2. **Run without historical inputs:** either package can run the 41 focused tests and synthetic example after dependency installation.
3. **Replay the historical study:** the Complete archive supplies both acquired vintages and processed snapshots. `run_final.py` audits them, uses no network acquisition and regenerates the final stage.

Numerical library or platform differences may affect floating-point results. The archive's file hashes establish the exact delivered bytes; they do not promise bitwise identical newly generated graphics or runtime metadata across platforms.

## Fresh acquisition is a separate concern

`fetch_historical.py` requests the original declared date range and `fetch_final.py` requests the final date range. The final loader checks the original processed snapshot, frozen source files and development-fitted topology controls before acquisition. Fetching new data is therefore not a guaranteed route to the archived inputs, even when the ticker names and dates match.

If revised provider observations fail a snapshot guard, retain the old protocol and document a new experiment with the new provenance. Do not edit a hash or disable a guard to make revised data appear to be the frozen research snapshot. All evaluation periods in this study are now observed.
