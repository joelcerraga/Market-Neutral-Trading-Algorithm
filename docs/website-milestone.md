# Website presentation milestone — 28 September 2026

The website gives the completed market-neutral research a landing page, a gallery and four dedicated interactive graph pages. It follows the SPX project's simple graph-directory approach and the author's white-background thumbnail preference. The main page links the paper, notebooks and problem-solving record, and states the negative final trading result directly.

## Deliverables

- `index.html`: research overview, method, final findings and four explorer entry points.
- `explorers/index.html`: graph gallery with a dedicated social-preview thumbnail.
- `explorers/correlations/`, `graph-diffusion/`, `persistence-landscapes/` and `final-test-landscapes/`: individual graph pages, each with interpretation, author-led literature references, saved-data links and access to the original standalone explorer.
- `assets/thumbnails/`: two white-background conceptual cover images and their prompts, created with the built-in image generator. These covers are not quantitative research figures.
- `assets/previews/`: four SVG previews derived from the saved graph snapshots, showing the first displayed date of each explorer. Preview regeneration uses Matplotlib and does not run a backtest.
- `scripts/build_site.py`, `verify_site.py` and `refresh_release_manifest.py`: static rebuild, link/metadata verification and manifest maintenance for reviewed changes.

## Setbacks, forks and responses

| Observed constraint or fork | Response | Remaining limit |
| --- | --- | --- |
| The four original HTML companions embed substantial Plotly code and data. Loading them together would make the gallery unnecessarily heavy. | Give each explorer its own page and load the interactive frame only when requested. The gallery uses lightweight previews. | The first interactive load still transfers the original artifact; a standalone link remains available. |
| A polished thumbnail could be mistaken for a measured research surface. | Use generated images only as conceptual cover/social graphics; derive graph-card previews directly from the saved numerical artifacts. | Cover artwork is illustrative. It carries no numerical or performance claim. |
| The saved explorers contain historical milestone context and are protected by release hashes. | Keep their bytes unchanged. Add current interpretation in the surrounding pages and adapt only iframe presentation in the browser. | Earlier milestone statements retain their original time context. |
| Scientific plots contain more axes and controls than a narrow phone screen comfortably supports. | Keep the page layout responsive and allow horizontal scrolling inside the graph viewport, with a standalone alternative. | Detailed 3D exploration benefits from a larger screen. |
| The local environment has Playwright but no browser executable; the official Chromium downloads returned unavailable HTML instead of an archive. The cloud browser also rejects localhost and local-file previews. | Complete static link, metadata, syntax and release checks, and preserve the standalone explorers. Record browser QA as pending rather than reporting an unperformed check. | Desktop/mobile visual review and 3D interaction checks must follow publication to an accessible public URL. |
| GitHub Pages was not enabled for the repository when this milestone began. The connected repository tools do not expose the Pages configuration setting. | Supply the complete static site at the repository root with `.nojekyll`, ready for `main` / root branch publication. | The repository owner must enable Pages in Settings before its public site URLs resolve. |

The user deliberately omitted `GITHUB_UPLOAD.md`; this milestone preserves that decision. The website sources and the manifest introduce no references to that guide.

## Verification and scientific scope

`python scripts/verify_site.py` checks all six pages, their local links, social-preview metadata, sitemap entries and the unchanged hashes of all 175 saved research outputs. The package verifier covers the newly added site files as part of the repository snapshot. Browser checks are recorded separately in `validation/website-validation.json`.

The original 41 research tests remain separate from site verification. No trading model, protocol, input snapshot, notebook or final-paper file is changed. The design remains a retrospective survivor-basket study, all evaluation periods are observed, and the website does not imply profitability or deployability.
