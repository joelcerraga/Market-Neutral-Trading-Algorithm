"""Assemble the Harvard-referenced working manuscript; never compiles a PDF."""
from pathlib import Path
import inspect
import json
import re
import sys
import html
import textwrap
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from market_neutral import topology, final_data, final_inference, final_evaluation


def harvard_reference(ref):
    authors = ref["bibtex_author"].strip("{}").split(" and ")
    authors = [re.sub(r"(?<=\.) (?=[A-Z]\.)", "", a) for a in authors]
    author = authors[0] if len(authors) == 1 else ", ".join(authors[:-1]) + " and " + authors[-1]
    fields = ref["bibtex_fields"]
    start = f"{author} ({ref['year']}{ref.get('year_suffix','')}) "
    title = html.unescape(ref["title"])
    pages = fields.get("pages", "").replace("--", "–")
    if ref["type"] == "article":
        volume = fields["volume"] + (f"({fields['number']})" if fields.get("number") else "")
        page_label = "p." if pages.isdigit() else "pp."
        entry = start + f"‘{title}’, *{fields['journal']}*, {volume}, {page_label} {pages}."
    elif ref["type"] == "book":
        ordinal = {"1":"1st","2":"2nd","3":"3rd"}.get(fields.get("edition"),f"{fields.get('edition')}th")
        edition = f" {ordinal} edn." if fields.get("edition") else ""
        series = (f" {fields['series']}" + (f", {fields['volume']}" if fields.get("volume") else "") + ".") if fields.get("series") else ""
        entry = start + f"*{title}*.{edition}{series} {fields['publisher']}."
    elif ref["type"] == "inproceedings":
        entry = start + f"‘{title}’, in *{fields['booktitle']}*, pp. {pages}."
    else:
        entry = start + f"*{title}*."
    if ref.get("doi"):
        entry += f" doi: [{ref['doi']}](https://doi.org/{ref['doi']})."
    else:
        url = html.unescape(ref["url"])
        entry += f" Available at: [{url}]({url}) (Accessed: {ref.get('accessed','21 September 2026')})."
    return entry


def build_bibliography():
    refs = json.loads((ROOT / "paper/references.json").read_text())
    refs.sort(key=lambda r: (r["bibtex_author"].strip("{}").casefold(), r["year"]))
    bibliography = "\n\n".join(harvard_reference(r) for r in refs) + "\n"
    (ROOT / "paper/references-harvard.md").write_text(bibliography, encoding="utf-8")
    entries = []
    for ref in refs:
        fields = {"author":ref["bibtex_author"], "year":str(ref["year"]), "title":ref["title"],
                  **ref["bibtex_fields"], "url":html.unescape(ref["url"])}
        if ref.get("doi"): fields["doi"] = ref["doi"]
        entries.append("@" + ref["type"] + "{" + ref["key"] + ",\n" +
                       ",\n".join("  " + k + " = {" + v + "}" for k,v in fields.items()) + "\n}")
    (ROOT / "paper/references.bib").write_text("\n\n".join(entries) + "\n", encoding="utf-8")
    return bibliography


def result_tables():
    out = ROOT / "outputs/topology"
    corr = pd.read_csv(out / "control-correlations.csv")
    corr = corr.loc[(corr.window == 126) & (corr.control == "mean_correlation")].pivot(index="feature", columns="phase", values="spearman")
    score = pd.read_csv(out / "control-model-scores.csv")
    score = score.loc[score.window == 126].pivot(index="feature", columns="phase", values="r2")
    labels = {"h0_mean":"H0 mean", "h0_max":"H0 maximum", "h1_total":"H1 total", "h1_max":"H1 maximum"}
    sections = []
    for number, title, frame in [(15,"Primary-window Spearman correlation with mean correlation",corr),
                                 (16,"Primary-window feature approximation using development-fitted controls; R²",score)]:
        lines = [f"Table {number}. {title}", "", "| Feature | Development | Validation |", "| --- | ---: | ---: |"]
        for feature in topology.FEATURES:
            lines.append(f"| {labels[feature]} | {frame.loc[feature,'development']:.3f} | {frame.loc[feature,'validation']:.3f} |")
        sections.append("\n".join(lines))
    windows = pd.read_csv(out / "window-sensitivity.csv")
    lines = ["Table 17. Paired-date Spearman correlations with the primary 126-session feature", "",
             "| Feature | Development: 63 | Development: 252 | Validation: 63 | Validation: 252 |", "| --- | ---: | ---: | ---: | ---: |"]
    for feature in topology.FEATURES:
        frame = windows.loc[windows.feature == feature].set_index(["phase","window"])
        values = [frame.loc[(phase,w),"spearman"] for phase,w in [("development",63),("development",252),("validation",63),("validation",252)]]
        lines.append("| " + labels[feature] + " | " + " | ".join(f"{x:.3f}" for x in values) + " |")
    sections.append("\n".join(lines))
    return "\n\n".join(sections)


def extract_code(match):
    function, start, end = match.groups()
    module_name, _, name = function.rpartition(".")
    module = {"":topology,"final_data":final_data,"final_inference":final_inference,"final_evaluation":final_evaluation}[module_name]
    lines = inspect.getsource(getattr(module,name or function)).splitlines()
    first = next(i for i,line in enumerate(lines) if line.startswith(start))
    last = next(i for i,line in enumerate(lines[first:], first) if line.startswith(end))
    excerpt = textwrap.dedent("\n".join(lines[first:last+1]))
    return "```python\n" + excerpt + "\n```"


def assemble():
    bibliography = build_bibliography()
    sections = sorted((ROOT / "paper/sections").glob("*.md"))
    manuscript = "\n\n".join(path.read_text().strip() for path in sections)
    manuscript = manuscript.replace("<!-- GENERATED_RESULTS -->", result_tables())
    if "<!-- FINAL_TABLE:" in manuscript:
        from final_section_tables import final_tables
        tables = final_tables(ROOT)
        manuscript = re.sub(r"<!-- FINAL_TABLE: (\w+) -->",lambda match:tables[match.group(1)],manuscript)
    manuscript = re.sub(r"<!-- CODE:([^:]+):([^:]+):(.+?) -->", extract_code, manuscript)
    main_text, appendix = manuscript.split("## Appendix A. ", 1)
    manuscript = (main_text.rstrip() + "\n\n## References\n\n" + bibliography.strip()
                  + "\n\n## Appendix A. " + appendix.strip() + "\n")
    headings = re.findall(r"^#{2,3} ((?:\d|Appendix|A\.|References)[^\n]*)", manuscript, flags=re.M)
    nav = ["## Table of contents", ""]
    for heading in headings:
        anchor = re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
        nav.append(f"- [{heading}](#{anchor})")
    for kind, title in [("Table","List of tables"),("Figure","List of figures"),("Equation","List of equations"),("Listing","List of code listings")]:
        pattern = r"!\[(Figure \d+\. [^\]]+)\]" if kind == "Figure" else rf"^({kind} \d+\. [^\n]+)"
        captions = re.findall(pattern, manuscript, flags=re.M)
        numbers = [int(re.search(r"\d+", c).group()) for c in captions]
        if numbers != list(range(1,len(numbers)+1)):
            raise ValueError(f"Nonsequential {kind} captions: {numbers}")
        nav += ["", f"## {title}", ""] + [f"- {caption}" for caption in captions]
    manuscript = manuscript.replace("<!-- GENERATED_NAVIGATION -->", "\n".join(nav))
    (ROOT / "paper/manuscript.md").write_text(manuscript, encoding="utf-8")
    print(f"Updated manuscript from {len(sections)} sections. Harvard references only; PDF typesetting is a separate command.")


if __name__ == "__main__":
    assemble()
