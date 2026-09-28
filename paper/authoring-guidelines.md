# Authoring requirements for all subsequent milestones

Use Joel Cerraga's undergraduate reports as the structural reference: numbered sections, displayed and numbered equations, symbol explanations and explicit links between calculations, figures and findings.

Use Harvard referencing throughout, with author–date in-text citations and an alphabetical reference list. Introduce sources in the prose. For example: “As Lo and MacKinlay (1990) explain in *When Are Contrarian Profits Due to Stock Market Overreaction?*, contrarian returns do not establish overreaction as the only mechanism. For this reason, the present signal is treated as a hypothesis to test.” Do not append a numbered citation.

The reference list must contain only the Harvard references. Do not add labels such as “Primary source”, “Not a scientific paper”, evidence notes or explanations of source quality. Keep provenance/access-version notes in `paper/references.json` outside the displayed bibliography. Use one consistent Harvard variant: surnames and initials; year; article title in quotation marks; italic journal/book title; volume/issue and pages; DOI or URL/access date as appropriate.

Prioritise peer-reviewed journals, scholarly books and research papers. Use official provider documentation for dataset-specific facts and official software documentation for implementation details. Do not present a website as a substitute for the underlying scientific paper. Check authors, year, title, venue and DOI; distinguish a working-paper version from the journal version.

Separate established relationships from project choices. In particular, the five-day signal, 126-day windows, graph threshold, scaling rule, costs and sample selection are research assumptions, not parameter values proved by the cited literature. Explain when this project differs from a paper's data or method.

The final PDF must include a title page, abstract, table of contents, list of tables, list of figures, list of equations, abbreviations, mathematical symbols and references. Keep equation numbers stable within each paper version and refer to them in the text. Add a list of code listings as well.

Do not compile a PDF per milestone. Maintain the working manuscript, equation/caption registers and code excerpts now; compile the complete final document only at the end, after Joel supplies its formatting, style, layout and presentation requirements. `paper/update_manuscript.py` assembles Markdown and references only.

Every milestone must include genuine setbacks or design forks, the evidence, the response and any remaining limitation. Maintain `docs/milestone-decisions.md`; distinguish observed failures, preventive design choices and unresolved empirical limitations. Do not invent problems or describe a negative financial result as fixed merely because its reporting improved.

Show only code that explains a consequential step. Extract excerpts from the real modules, number and caption them, identify their source and explain their purpose. Keep the complete implementation in the reproducible repository. Do not paste notebook screenshots as a substitute for legible code.

Include interactive, rotatable 3D visualisations as companion artifacts. Keep scientific meaning clear: asset categories are discrete, visual interpolation is not a statistical estimate, and a correlation surface is not a predicted-return surface.

The final presentation should include a reproducible GitHub repository and a LinkedIn-ready research page. Do not publish private input caches or claim empirical improvements before completing the comparison. Report negative findings with the same prominence as favourable results.
