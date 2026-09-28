## Appendix A. Reproducibility and interactive companions

Table 27. Research artifacts and reproduction status

| Artifact | Current state |
| --- | --- |
| Historical inputs | Original cache preserved; separate final-period vintage with 2019 warm-up, hashes and overlap audit |
| Trading comparison | All 44 graph/baseline scenarios retained with uncertainty and exposure controls |
| Topology | Four features, three windows, complete control comparisons, fitted coefficients and monthly diagrams |
| Interactive companions | Historical correlation surface, graph/score explorer and earlier/final-period persistence landscapes |
| Walkthroughs | Five notebooks; final evaluation executed with captured outputs |
| Scientific text | Current manuscript uses Harvard author–date citations and an alphabetical reference list |
| Engineering verification | 41 automated checks; 480 earlier and 288 final-period diagram bounds; artifact and causal checks |
| Final test | 2020–2025 released after a new protocol lock; all 22 cases completed; now observed |
| Public release | Reproducible source structure and CI prepared; GitHub/LinkedIn publication remains a later deliverable |

Run `python run_final.py` for the complete final experiment after installing the pinned dependencies. `python -m unittest discover -s tests -v` runs the focused checks. The private research ZIP includes the acquired observations for exact offline replay. An eventual public checkout will exclude vendor caches because redistribution rights cannot be assumed. A fresh acquisition may have a different data vintage and requires a documented revision rather than a bypass of the input hash guard.

The editable manuscript is assembled by `python paper/update_manuscript.py` from section files, implementation excerpts, result tables and the source register. `python paper/assemble_final_paper.py` prepares the portrait typesetting source, copies the declared figures and compiles the final PDF. The accompanying source package includes a standalone LaTeX file and its figure assets. Caption registers and page references are generated from the compiled document.

### A.1. Interactive companions

The historical-correlation companion displays 120 monthly matrices. The graph-diffusion companion links 120 monthly networks to unconstrained scores. The earlier persistence companion displays 120 monthly landscapes and birth–death diagrams; the final-period companion adds 72 months covering 2020–2025. Each HTML file embeds its plotting library for offline use after download. Rotation, date selection, hover and playback support inspection of the underlying numerical objects. The PDF contains static figures; the HTML files provide the dynamic views.

Numerical frame values, dates and control configuration were checked. Live browser interaction and local VS Code kernel connectivity were not exercised in the build environment and remain local setup checks. These limits concern the execution environment, whereas the saved numerical results and notebook cells were executed and verified.

### A.2. Publication status and future changes

The scientific evaluation and final paper are complete for the frozen design. Public GitHub publication and the CV/LinkedIn release are subsequent presentation steps. Claims should describe the implemented methods, verification and empirical findings, including the negative economic result. The evidence does not support a claim of demonstrated profitable alpha. All three research periods are observed; future model changes need newly reserved evidence.

### A.3. Final document assembly

The final assembly follows the author's supplied style examples while retaining the research sequence developed for this project. All pages use A4 portrait dimensions, with numbered equations and centred captions below figures, tables and equations. The build generates the contents and caption registers from the typeset document. Initial checks exposed sparse front-matter continuations and caption-box and font issues; compact register tables, explicit font selection and revised caption placement resolved them. Rendered-page inspection and position checks verify presentation separately from the numerical research. This assembly is recorded in the sixth milestone's decision log; public publication remains pending.
