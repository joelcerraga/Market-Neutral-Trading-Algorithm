# Saved research outputs

Both release archives retain **175 files under `outputs/`**, with identical bytes. [output-inventory.csv](output-inventory.csv) lists every relative path, file type, byte count and SHA-256 hash. The paper, notebooks and historical validation records are additional files outside that count.

## Read the project in order

| Stage | Notebook | Saved outputs | Files |
| --- | --- | --- | ---: |
| 1. Synthetic mechanics | [01-foundations](../notebooks/01-foundations.ipynb) | [synthetic](../outputs/synthetic/) | 14 |
| 2. Historical baseline | [02-historical-baseline](../notebooks/02-historical-baseline.ipynb) | [historical](../outputs/historical/) | 18 |
| 3. Graph comparison | [03-graph-comparison](../notebooks/03-graph-comparison.ipynb) | [comparison](../outputs/comparison/) | 71 |
| 4. Topology descriptors | [04-topology-features](../notebooks/04-topology-features.ipynb) | [topology](../outputs/topology/) | 16 |
| 5. Final evaluation | [05-final-evaluation](../notebooks/05-final-evaluation.ipynb) | [final](../outputs/final/) | 56 |

Earlier notebooks retain their historical stage context. The complete final evaluation is now observed. The [milestone decision log](milestone-decisions.md) explains the genuine setbacks and responses; [release notes](release-notes.md) add packaging decisions.

## Interactive companions

Download these HTML files and open them locally in a browser. JavaScript is embedded, so they work offline without a Python server. GitHub's source preview does not execute them.

| Explorer | Artifact |
| --- | --- |
| Historical correlation surfaces | [Historical-Correlation-Explorer.html](../outputs/historical/Historical-Correlation-Explorer.html) |
| Graph diffusion | [Graph-Diffusion-Explorer.html](../outputs/comparison/Graph-Diffusion-Explorer.html) |
| Development/validation persistence landscapes | [Persistence-Landscape-Explorer.html](../outputs/topology/Persistence-Landscape-Explorer.html) |
| Final-test monthly persistence landscapes | [Final-Test-Landscape-Explorer.html](../outputs/final/topology/Final-Test-Landscape-Explorer.html) |

## Main final results

| Artifact | Contents |
| --- | --- |
| [milestone-5-results.md](../outputs/final/milestone-5-results.md) | Concise findings and limitations |
| [final-summary.csv](../outputs/final/final-summary.csv) | All 22 declared cases |
| [mean-inference.csv](../outputs/final/mean-inference.csv) | Paired and family-adjusted inference |
| [calendar-year-results.csv](../outputs/final/calendar-year-results.csv) | All six test years |
| [evidence-gate.json](../outputs/final/evidence-gate.json) | Four predeclared necessary conditions |
| [exposure-diagnostics.csv](../outputs/final/exposure-diagnostics.csv) | Exposure diagnostics |
| [topology/features.csv](../outputs/final/topology/features.csv) | Final topology descriptors |
| [topology/control-model-scores.csv](../outputs/final/topology/control-model-scores.csv) | Transfer of the frozen control models |
| [run-manifest.json](../outputs/final/run-manifest.json) | Provenance and recorded output hashes |

The same folder retains every scenario ledger, decision-weight file, paired-return series, bootstrap mean, diagnostic and figure. Earlier stage folders likewise retain all saved cases; no favourable subset has been selected for publication.

## Paper and source

The authoritative document is [Market-Neutral-Trading-Algorithm-Final-Paper.pdf](../paper/final/Market-Neutral-Trading-Algorithm-Final-Paper.pdf). The [Markdown manuscript](../paper/manuscript.md), section files, Harvard references, BibTeX, LaTeX source and figure assets are included. The final paper has 55 A4 portrait pages, a discussion and conclusion, and an appendix following its reference list.

`paper/archive/` preserves earlier authoring snapshots; `paper/output/` preserves earlier PDF drafts and their manifests. Those drafts are historical evidence and do not replace the final paper or its Harvard-only reference list. Old manuscript or PDF-status checks refer to their original release context.
