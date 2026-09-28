# Methodology and academic source guide

The combined derivation is in `paper/manuscript.md`. Edit `paper/sections/` and run `python paper/update_manuscript.py` to refresh the manuscript, result tables, code excerpts and Harvard references. Run `python paper/assemble_final_paper.py` to compile the final A4 portrait PDF using XeLaTeX. `python paper/build_paper.py` performs both steps.

| Topic | Manuscript section | Implementation |
| --- | --- | --- |
| Historical data and sample limits | 2 | `market_neutral/historical.py` |
| Reversal score and beta | 3 | `historical.py`, `portfolio.py` |
| Projection and exposure ceilings | 4 | `portfolio.py` |
| Correlation graph and heat diffusion | 5 | `graph.py`, `strategy.py` |
| Execution, costs and accounting | 6 | `backtest.py` |
| Baseline outcomes | 7 | `historical.py` |
| Graph comparison and paired uncertainty | 8 | `comparison.py`, `inference.py` |
| Persistence, control models and window checks | 9 | `topology.py`, `topology_plots.py` |
| Final evaluation, joint uncertainty and topology transfer | 10 | `final_data.py`, `final_evaluation.py`, `final_inference.py` |
| Setbacks and decisions | 11 | `docs/milestone-decisions.md` |
| Discussion and limitations | 12 | Interpretation of the completed comparison and topology study |
| Conclusion and future work | 13 | Research findings and limits of the financial claims |
| Reproduction and interactive companions | Appendix A | Protocols, scripts and validation records |

The source register `paper/references.json` records access versions and the claims each source supports. Those notes are separate from the clean alphabetical bibliography in `paper/references-harvard.md`. Established relationships, project-specific parameters and observed empirical findings are distinguished in the manuscript.

The synthetic generator deliberately includes mean reversion. Historical baseline and graph returns are negative at default costs, and the graph comparison does not demonstrate a reliable advantage. Topology is now implemented and verified as a descriptor; no topology trading rule was introduced. The fixed final graph test did not meet its necessary evidence conditions.
