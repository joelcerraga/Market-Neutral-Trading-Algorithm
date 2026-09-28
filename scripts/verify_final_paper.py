"""Check the compiled paper against its manuscript and frozen research artifacts.

This checks document artifacts; it does not rerun any financial experiment.
Use --record-visual-review only after inspecting every rendered page of this PDF.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "paper/final"
NAME = "Market-Neutral-Trading-Algorithm-Final-Paper"
EXPECTED = {"Figure": 16, "Table": 27, "Equation": 30, "Listing": 15}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(line):
    """Read the outer braced arguments in a LaTeX contents entry."""
    result, level, start = [], 0, 0
    for i, char in enumerate(line):
        if i and line[i - 1] == "\\":
            continue
        if char == "{":
            if level == 0:
                start = i + 1
            level += 1
        elif char == "}":
            level -= 1
            if level == 0:
                result.append(line[start:i])
    assert level == 0
    return result


def verify(record_visual_review=False):
    path = FINAL / (NAME + ".pdf")
    pdf = fitz.open(path)
    captions = {kind: [] for kind in EXPECTED}
    labels, texts, outside = [], [], []
    for index, page in enumerate(pdf):
        assert abs(page.rect.width - 595.276) < 0.05
        assert abs(page.rect.height - 841.890) < 0.05
        assert page.rotation == 0
        labels.append(page.get_label())
        texts.append(page.get_text())
        for block in page.get_text("dict")["blocks"]:
            for line_index, line in enumerate(block.get("lines", [])):
                spans = line["spans"]
                text = "".join(span["text"] for span in spans)
                if line["bbox"][0] < 55 or line["bbox"][2] > page.rect.width - 55:
                    outside.append([index + 1, text])
                match = re.match(r"^(Figure|Table|Equation|Listing) (\d+)\. ", text)
                if not match or "Italic" not in spans[0]["font"] or not 9.8 < spans[0]["size"] < 10.1:
                    continue
                kind, number = match[1], int(match[2])
                offsets = []
                for following in block["lines"][line_index:]:
                    # A caption is a separate italic paragraph. Math spans may differ.
                    if not any("Italic" in s["font"] and 9.8 < s["size"] < 10.1 for s in following["spans"]):
                        break
                    x0, _, x1, _ = following["bbox"]
                    offsets.append(abs((x0 + x1) / 2 - page.rect.width / 2))
                assert offsets and max(offsets) < 1, (kind, number, offsets)
                captions[kind].append({"number": number, "physical_page": index + 1,
                    "printed_page": page.get_label(), "max_centre_offset_pt": max(offsets)})
    assert not outside, outside
    for kind, count in EXPECTED.items():
        assert [row["number"] for row in captions[kind]] == list(range(1, count + 1)), kind

    register_entries = 0
    for extension, kind in [("lof", "Figure"), ("lot", "Table"), ("loe", "Equation"), ("lol", "Listing")]:
        lines = (FINAL / (NAME + "." + extension)).read_text().splitlines()
        entries = [fields(line) for line in lines if line.startswith("\\contentsline")]
        assert len(entries) == EXPECTED[kind]
        for entry, caption in zip(entries, captions[kind]):
            assert int(re.search(r"\\numberline \{(\d+)\}", entry[1])[1]) == caption["number"]
            assert entry[2] == caption["printed_page"], (kind, caption["number"])
            register_entries += 1
    toc = [fields(line) for line in (FINAL / (NAME + ".toc")).read_text().splitlines()
           if line.startswith("\\contentsline")]
    outline = pdf.get_toc()
    assert len(toc) == len(outline)
    for entry, bookmark in zip(toc, outline):
        assert labels[bookmark[2] - 1] == entry[2], (entry, bookmark)

    assert "March 2026" in texts[0] and "September 2026" not in texts[0]
    list_starts = [item for item in outline if item[0] == 1 and item[1].lower().startswith("list of ")]
    chapter_starts = [item for item in outline if item[0] == 1 and re.match(r"^\d+ ", item[1])]
    assert len(list_starts) == 6 and len(chapter_starts) == 13
    assert len({item[2] for item in list_starts + chapter_starts}) == 19
    for _, title, physical_page in list_starts + chapter_starts:
        page = pdf[physical_page - 1]
        body_lines = [line for block in page.get_text("dict")["blocks"]
                      for line in block.get("lines", []) if 50 < line["bbox"][1] < 800]
        body_lines.sort(key=lambda line: (line["bbox"][1], line["bbox"][0]))
        first_line = "".join(span["text"] for span in body_lines[0]["spans"])
        assert title.lower().startswith(first_line.lower()), (title, first_line)
        assert body_lines[0]["bbox"][1] < 100, title
    reference_page = next(item[2] for item in outline if item[1] == "References")
    appendix_page = next(item[2] for item in outline if item[0] == 1 and item[1].startswith("A "))
    assert reference_page < appendix_page
    assert all(index + 1 < appendix_page for index, page in enumerate(pdf)
               if any("uri" in link for link in page.get_links()))

    log = (FINAL / (NAME + ".log")).read_text()
    unwanted = [line for line in log.splitlines() if any(term in line.lower() for term in
                 ("overfull", "missing character", "font warning", "undefined reference", "undefined control"))]
    assert not unwanted, unwanted
    bibliography = (ROOT / "paper/references-harvard.md").read_text().strip()
    references = bibliography.split("\n\n")
    assert len(references) == 24
    assert all(re.match(r".+ \(\d{4}[ab]?\) ", ref) for ref in references)
    assert not any(term in bibliography.lower() for term in
                   ("primary source", "not a scientific paper", "not a research paper", "evidence:", "source quality"))
    manuscript = (ROOT / "paper/manuscript.md").read_text()
    assert manuscript.split("## References\n\n", 1)[1].split("## Appendix A. ", 1)[0].strip() == bibliography
    reference_urls = re.findall(r"\[[^\]]+\]\(((?:[^()]|\([^()]*\))+)\)", bibliography)
    pdf_urls = {link["uri"] for page in pdf for link in page.get_links() if "uri" in link}
    assert set(reference_urls) == pdf_urls, (set(reference_urls) - pdf_urls, pdf_urls - set(reference_urls))
    text = "\n".join(texts)
    assert "13 Conclusion and future work" in text and "12 Discussion and limitations" in text
    assert "List of mathematical symbols" in text and "List of abbreviations" in text
    assert "??" not in text
    commands = re.findall(r"`(python [^`]+)`", manuscript)
    normalised_text = " ".join(text.split())
    assert all(command in normalised_text for command in commands), commands
    markdown_code = re.findall(r"```python\n(.*?)\n```", manuscript, flags=re.S)
    latex = (FINAL / (NAME + ".tex")).read_text()
    latex_code = re.findall(r"\\begin\{Verbatim\}\[[^\n]+\]\n(.*?)\n\\end\{Verbatim\}", latex, flags=re.S)
    assert markdown_code == latex_code and len(markdown_code) == 15

    figures = {}
    for number, relative in re.findall(r"!\[Figure (\d+)\. [^\]]+\]\(([^)]+)\)", manuscript):
        source = (ROOT / "paper" / relative).resolve()
        copied = FINAL / "assets" / f"figure-{int(number):02}.png"
        assert sha256(source) == sha256(copied)
        figures[number] = {"source": str(source.relative_to(ROOT)), "sha256": sha256(source)}
    assert len(figures) == 16
    run = json.loads((ROOT / "outputs/final/run-manifest.json").read_text())
    for relative, expected in run["files"].items():
        assert sha256(ROOT / "outputs/final" / relative) == expected, relative
    for relative, expected in run["source_sha256"].items():
        assert sha256(ROOT / relative) == expected, relative
    frozen = json.loads((ROOT / "validation/milestone-5-package-sha256.json").read_text())["files"]
    protected = {name: digest for name, digest in frozen.items()
                 if name.startswith(("market_neutral/", "tests/", "protocol/", "data/", "outputs/", "notebooks/", "run_"))}
    for relative, expected in protected.items():
        assert sha256(ROOT / relative) == expected, relative

    reviewed = []
    if record_visual_review:
        render = json.loads((FINAL / "qa/render-manifest.json").read_text())
        assert render["pdf_sha256"] == sha256(path) and render["page_count"] == len(pdf)
        assert len(render["pages"]) == len(pdf)
        for name, expected in render["pages"].items():
            assert sha256(FINAL / "qa/final-pages" / name) == expected
        reviewed = list(range(1, len(pdf) + 1))

    report = {"verified_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if record_visual_review else "automated_checks_passed; visual review pending",
        "pdf_sha256": sha256(path), "pages": len(pdf), "all_pages_a4_portrait": True,
        "title_page_date": "March 2026", "list_sections_start_on_new_pages": list_starts,
        "main_chapters_start_on_new_pages": chapter_starts,
        "references_physical_page": reference_page, "appendix_physical_page": appendix_page,
        "appendix_follows_reference_list": True,
        "captions": captions, "captions_position": "beneath their objects; checked in rendered-page review" if reviewed else "visual review pending",
        "max_caption_centre_offset_pt": max(c["max_centre_offset_pt"] for values in captions.values() for c in values),
        "caption_register_entries_verified": register_entries, "contents_and_bookmark_pages_verified": len(toc),
        "missing_glyphs_overfull_boxes_or_reference_warnings": unwanted,
        "harvard_references": len(references), "reference_urls_preserved": len(set(reference_urls)),
        "inline_commands_preserve_spaces": len(commands), "code_excerpts_preserved_verbatim": len(markdown_code),
        "figure_copies_verified": figures, "frozen_research_files_unchanged": len(protected),
        "final_numerical_outputs_unchanged": len(run["files"]), "research_experiments_rerun_for_assembly": False,
        "rendered_physical_pages_visually_reviewed": reviewed,
        "review_scope": "All page layouts, page density, table and formula legibility, captions, code blocks and reference formatting",
        "style_examples": ["SPX Option Implied Density Final Paper", "Final Year Project - Medical Cooler",
                           "Power Systems - Laboratory Logbook Portfolio", "Communications and Electromagnetic Waves assignments"],
        "research_status": "Frozen evaluation complete; no demonstrated profitable alpha; public GitHub release remains pending"}
    target = ROOT / "validation/final-paper-validation.json"
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ["status", "pages", "caption_register_entries_verified",
        "contents_and_bookmark_pages_verified", "harvard_references", "reference_urls_preserved",
        "max_caption_centre_offset_pt", "frozen_research_files_unchanged", "final_numerical_outputs_unchanged"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-visual-review", action="store_true")
    verify(parser.parse_args().record_visual_review)
