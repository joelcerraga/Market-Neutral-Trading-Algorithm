# Validation records

Milestone 5 records:

- `milestone-5-tests.txt`: 41 focused automated checks.
- `milestone-5-notebook-execution.json`: ten code cells executed with captured rich outputs and no errors.
- `milestone-5-artifacts.json`: every final ledger, inference family, input/source hash, figure, interactive frame, manuscript and notebook check.
- `milestone-5-package-sha256.json`: hashes of files included in the release, excluding the hash file itself.
- `final-initial-run-manifest.json`: the first evaluation's original record, including the empty sensitivity-ledger hash.
- `final-artifact-repair.json`: observed failure, verification response and replay outcome. The original summary and every unaffected numerical artifact must reproduce exactly.

Run `python run_final.py` for the full final replay, `python -m unittest discover -s tests -v` for the focused suite and `python scripts/verify_milestone_5.py` for the historical Milestone 5 artifact checks. `python paper/update_manuscript.py` refreshes the Markdown manuscript and Harvard bibliography. The final paper is compiled separately with `python paper/assemble_final_paper.py` after the author's presentation instructions.

`final-paper-validation.json` records the final assembly checks: A4 portrait page geometry, centred captions, complete registers and references, rendered-page inspection, copied figure hashes and unchanged numerical artifacts. The assembly does not rerun or select trading models. Historical Milestone 5 manuscript and PDF-status checks describe that earlier snapshot; the final paper now includes a discussion, conclusion and reproduction appendix.

Milestone 1–4 records, test counts, package hashes and verification scripts are historical release snapshots. Their historical counts and then-current holdout status are not assertions about the current project. Earlier notebook prose was converted to Harvard references and now carries a current-status note; its retained numerical outputs preserve the earlier execution context.

The build environment runs trusted notebook cells sequentially in IPython because kernel sockets are unavailable. Browser interaction and local VS Code kernel connectivity remain local environment checks. The interactive artifact's dates, numerical layer values, embedded JavaScript and control configuration are verified separately.
