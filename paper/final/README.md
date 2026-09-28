# Final paper and editable source

Open `Market-Neutral-Trading-Algorithm-Final-Paper.pdf` for the assembled paper. It follows the supplied style examples using A4 portrait pages, a 12-point Arial-compatible body, numbered headings and smaller centred captions beneath figures, tables and equations. The discussion, conclusion and reproduction appendix complete the research narrative.

The revised title page reads March 2026. Every main chapter and each “List of…” section begins on a new page, and the appendix follows the reference list. The contents, caption registers and bookmarks reflect this order.

The source archive includes the project, frozen research artifacts, interactive HTML companions, section files and the final typesetting source. It is a private research snapshot; the public GitHub export remains a subsequent step. The appendix explains the difference between exact offline replay and acquisition of a new data vintage.

## Compile the included typesetting source

From this directory, run:

```bash
python compile_source.py
```

This runs XeLaTeX four times so the contents, caption registers and page links settle. It uses the supplied `.tex` file and `assets/` figures and does not run the trading experiments. Keep those files together.

The verified build uses XeLaTeX from TeX Live 2023 on Debian/Ubuntu, with the packages `geometry`, `fontspec`, `unicode-math`, `amsmath`, `graphicx`, `booktabs`, `array`, `longtable`, `ragged2e`, `xcolor`, `caption`, `fvextra`, `needspace`, `placeins`, `titlesec`, `tocloft`, `fancyhdr`, `enumitem`, `xurl`, `hyperref` and `setspace`. The fonts are Nimbus Sans, DejaVu Sans Mono and Latin Modern Math. A typical TeX Live installation with its recommended fonts and extra LaTeX packages supplies the TeX dependencies; Nimbus Sans is supplied by `fonts-urw-base35` on Debian/Ubuntu.

The preamble explicitly locates the four Nimbus Sans faces at `/usr/share/fonts/opentype/urw-base35/`. If your system stores them elsewhere, change the `Path` option in both font declarations to that font directory. Do not replace the typeface silently if you need to preserve the delivered page layout. Different TeX or font versions may change line and page breaks even when the content is identical.

## Edit the manuscript and regenerate

From the project root, after installing the pinned research dependencies:

```bash
python paper/build_paper.py
```

This refreshes `paper/manuscript.md` from `paper/sections/`, the saved result tables, selected implementation excerpts and `paper/references.json`, then runs `paper/assemble_final_paper.py`. It does not rerun or select trading models. Edit the section files for lasting prose changes; direct changes to the generated Markdown or LaTeX will be replaced on the next regeneration. The standalone `.tex` remains useful for presentation-only editing and compilation.

The bibliography in the PDF and `references-harvard.md` contains Harvard references only. Claim-support and access notes remain in the separate source register. The generated `references.bib` is included for later citation-manager use; compilation of the supplied `.tex` does not require BibTeX.

## Verification

`validation/final-paper-validation.json` records the delivered PDF's page geometry, caption numbering and centring, register page checks, reference count, rendered-page review and preservation of the frozen research artifacts. `docs/milestone-decisions.md` records the actual assembly issues and fixes alongside the earlier research milestones. The numerical tests and historical validation records retain their original context; final assembly adds document checks rather than new performance evidence.

After compilation, install `requirements-paper.txt` and run `python scripts/verify_final_paper.py` from the project root for the automated document checks. With Poppler installed, `python scripts/render_final_paper.py` creates verified page images and review sheets under `paper/final/qa/`. Inspect every rendered page before running the verifier with `--record-visual-review`; that flag records an actual review and does not perform one automatically. The QA images and intermediate TeX files are excluded from the source archive and can be regenerated locally.
