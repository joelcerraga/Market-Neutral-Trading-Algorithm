# Complete project release — 28 September 2026

This packaging milestone prepares the completed study for download and a later author-controlled GitHub publication. It changes navigation, setup instructions and packaging tools. It does not select new models, acquire new prices, rerun historical tests or alter the frozen research findings.

## Contents and preservation

Both archives contain all five executed notebooks, all 175 research output files, all four interactive HTML explorers, the revised final PDF, editable paper sources, earlier authoring/PDF drafts, four locked protocols, research code, tests and the existing CI workflow. The Complete archive additionally contains the original 102 vendor input/cache files. The GitHub archive retains data provenance and hashes without those files.

The final PDF is retained byte-for-byte. Its 55-page layout keeps March 2026 on the title page, every list and main chapter on a new page, and the appendix after the references. Acquisition and validation timestamps keep their actual dates. The saved outputs, input snapshots, research source, tests, notebooks and protocols are not edited during packaging.

## Setbacks, forks and responses

| Observed issue or design fork | Response | Remaining limit |
| --- | --- | --- |
| The old quick start ran `run_final.py` immediately, although a public checkout would lack its frozen input snapshots. | Split the setup into a public test/synthetic example and Complete-archive historical replay; preserve both vintages privately. | Fresh provider acquisition may not reproduce the archived vintage. |
| Exact-byte protocol guards can conflict with Git line-ending conversion on another operating system. | Add `.gitattributes` with `* -text`, retain checksums, and check a Git staging round trip with `core.autocrlf=true`. | Editors can still deliberately change bytes; a mismatch must be investigated. |
| Historical milestone verifiers assert earlier manuscript counts and status text. | Retain those records as historical evidence and distinguish current download verification from document rebuild checks. | The full paper verifier needs the private files and regenerated TeX auxiliaries. |
| The project contains both final paper source and superseded drafts. | Preserve meaningful historical drafts and explicitly identify `paper/final/` as authoritative. | Historical prose can describe a holdout that has since been consumed. |
| Three pinned research packages were absent from the packaging environment. | Install the declared Plotly, Ripser and Persim versions before checking the extracted public package. | Dependency installation requires suitable Python wheels or a build environment. |
| The initial redirected test log ended before the suite summary despite a zero process exit code. | Retain that incomplete record, rerun with captured output, require the explicit 41-test/OK summary, and save the complete log with an atomic write. | The cause of the first truncated record was not established; an exit code alone was insufficient evidence. |
| An archive can appear complete while silently dropping a ledger, figure or notebook. | Enumerate every output, hash every packaged file, check ZIP integrity and verify both extracted profiles. | Checksums establish byte preservation, not the truth of financial claims. |

## Verification scope

`validation/release-tests.txt` records all 41 focused tests passing from an extracted GitHub package without vendor inputs; `release-tests-initial-incomplete.txt` preserves the incomplete first capture. `validation/release-validation.json` records the successful synthetic smoke run, Git byte-preservation check, output completeness and unchanged scientific files. Earlier validation records retain their historical meaning. Hosted GitHub Actions and the user's local notebook kernel remain checks to perform after publication/setup.

Each archive contains a profile-specific `PACKAGE_README.md` and `package-manifest.json`. Run `python scripts/verify_release.py` immediately after extraction. It reports missing or changed listed files and does not inspect unlisted additions. The manifest is not a digital signature or an author identity certificate.

To rebuild the archives from a complete extracted project:

```bash
python scripts/package_release.py --profile all --destination ../release-build
```

From the public package, use `--profile github` instead. Building the Complete profile requires all 102 original vendor input/cache files. Packaging uses a fixed ZIP timestamp and sorted paths; identical input bytes and compression environment reproduce the same archive bytes. The manifest excludes itself to avoid a circular hash.

Environments, temporary render images, TeX intermediates, caches of Python bytecode, Git internals and nested ZIPs are omitted. No supplied style-example paper or unrelated personal document is part of this project release. No software licence is assigned. The project is packaged, not yet published to GitHub by this workflow.

## PDF ending revision — 28 September 2026

At the author's request, the final PDF's last physical page (printed page 46) has been removed, including Appendix A.2 and A.3. Their contents entries and bookmarks have also been removed. The document ends at printed page 45 and contains 54 physical pages including the front matter. The editable appendix and generated sources match this change.

Deleting only the page would have left broken contents entries. The revision removes those entries while retaining the layout of every other page; 53 retained pages are text- and pixel-identical to the prior PDF. The revised contents and final page were rendered and visually inspected. The original packaging checks and historical archive hashes above retain their original context; `validation/final-paper-validation.json` and `package-manifest.json` identify the current document. No research outputs or calculations changed.
