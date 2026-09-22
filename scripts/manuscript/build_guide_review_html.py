#!/usr/bin/env python3
"""Build a complete, self-contained guide-review HTML from manuscript Markdown.

This is a document rendering workflow only. It reads the manuscript, bibliography,
and committed figures; it does not open scientific data or recompute results.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def read_bib(path: Path) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^@\w+\{([^,]+),", line)
        if match:
            current = {"key": match.group(1)}
            entries[match.group(1)] = current
            continue
        if current is not None:
            field = re.match(r"^\s*(\w+)\s*=\s*\{(.*)\},?\s*$", line)
            if field:
                current[field.group(1).lower()] = field.group(2)
            elif line.strip() == "}":
                current = None
    return entries


def author_text(entry: dict[str, str]) -> str:
    authors = re.split(r"\s+and\s+", entry["author"])
    names = [author.split()[-1] for author in authors]
    if len(names) == 1:
        return names[0]
    elif len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]} et al."


def citation_labels(bib: dict[str, dict[str, str]]) -> dict[str, str]:
    groups: dict[tuple[str, str], list[str]] = {}
    for key, entry in bib.items():
        groups.setdefault((author_text(entry), entry["year"]), []).append(key)
    labels: dict[str, str] = {}
    for (authors, year), keys in groups.items():
        ordered = sorted(keys, key=lambda key: (bib[key].get("title", ""), key))
        for index, key in enumerate(ordered):
            suffix = chr(ord("a") + index) if len(ordered) > 1 else ""
            labels[key] = f"{authors}, {year}{suffix}"
    return labels


def citations(text: str, bib: dict[str, dict[str, str]]) -> str:
    labels = citation_labels(bib)

    def replace(match: re.Match[str]) -> str:
        keys = [part.strip().lstrip("@") for part in match.group(1).split(";")]
        missing = [key for key in keys if key not in bib]
        if missing:
            raise ValueError(f"Unresolved citation keys: {missing}")
        return "(" + "; ".join(labels[key] for key in keys) + ")"

    return re.sub(r"\[([^\]]*@[A-Za-z0-9_; @-]+)\]", replace, text)


INLINE_MATH = {
    r"100\times\mathrm{FAR}": "100×FAR",
    r"1{,}000\times\mathrm{FAR}": "1,000×FAR",
    r"30\times21": "30×21",
    "K=6": "K=6",
    "L_e": "L<sub>e</sub>",
    r"\alpha=0.20": "α=0.20",
    r"\hat{\mathbf{z}}_i": "ẑ<sub>i</sub>",
    r"\lfloor0.30L_e\rfloor": "⌊0.30L<sub>e</sub>⌋",
    r"\mathbf{z}_i\in\mathbb{R}^{63}": "z<sub>i</sub>∈ℝ<sup>63</sup>",
    r"\operatorname{median}(12,25,42.5)=25": "median(12, 25, 42.5)=25",
    r"\sum_{j=1}^{21}g_{ij}=a_i": "∑<sub>j=1</sub><sup>21</sup> g<sub>ij</sub>=a<sub>i</sub>",
    r"\tau_{r_i}": "τ<sub>r<sub>i</sub></sub>",
    r"\{a_n^{\mathrm{train}}\}_{n=1}^{N}": "{a<sub>n</sub><sup>train</sup>}<sub>n=1</sub><sup>N</sup>",
    "e": "e", "i": "i", "j": "j",
    "m_1=c_1": "m<sub>1</sub>=c<sub>1</sub>",
    "o_e(q)": "o<sub>e</sub>(q)",
    r"q\in\{0.10,0.20,0.30\}": "q∈{0.10, 0.20, 0.30}",
    r"t=1,\ldots,30": "t=1,…,30",
}


def inline_math_html(value: str) -> str:
    if value not in INLINE_MATH:
        raise ValueError(f"Unmapped inline equation: {value}")
    return f'<span class="math-inline">{INLINE_MATH[value]}</span>'


def rich_text(text: str, bib: dict[str, dict[str, str]]) -> str:
    text = citations(text, bib)
    maths: list[str] = []

    def hold_math(match: re.Match[str]) -> str:
        maths.append(match.group(1))
        return f"MATHPLACEHOLDER{len(maths) - 1}END"

    text = re.sub(r"\$([^$]+)\$", hold_math, text)
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    for index, value in enumerate(maths):
        escaped = escaped.replace(f"MATHPLACEHOLDER{index}END", inline_math_html(value))
    return escaped


EQUATIONS = {
    "o_e": "<math display='block'><msub><mi>o</mi><mi>e</mi></msub><mo>(</mo><mi>q</mi><mo>)</mo><mo>=</mo><mo>⌊</mo><msub><mi>L</mi><mi>e</mi></msub><mo>(</mo><mn>1</mn><mo>−</mo><mi>q</mi><mo>)</mo><mo>⌋</mo><mo>+</mo><mn>1</mn><mo>.</mo></math>",
    "barx": "<math display='block'><msub><mover><mi>x</mi><mo>¯</mo></mover><mrow><mi>i</mi><mi>j</mi></mrow></msub><mo>=</mo><mfrac><mn>1</mn><mn>30</mn></mfrac><munderover><mo>∑</mo><mrow><mi>t</mi><mo>=</mo><mn>1</mn></mrow><mn>30</mn></munderover><msub><mi>x</mi><mrow><mi>i</mi><mi>t</mi><mi>j</mi></mrow></msub><mo>,</mo></math>",
    "std": "<math display='block'><msub><mi>s</mi><mrow><mi>i</mi><mi>j</mi></mrow></msub><mo>=</mo><msqrt><mfrac><mn>1</mn><mn>30</mn></mfrac><munderover><mo>∑</mo><mrow><mi>t</mi><mo>=</mo><mn>1</mn></mrow><mn>30</mn></munderover><msup><mrow><mo>(</mo><msub><mi>x</mi><mrow><mi>i</mi><mi>t</mi><mi>j</mi></mrow></msub><mo>−</mo><msub><mover><mi>x</mi><mo>¯</mo></mover><mrow><mi>i</mi><mi>j</mi></mrow></msub><mo>)</mo></mrow><mn>2</mn></msup></msqrt><mo>,</mo></math>",
    "delta": "<math display='block'><mi>Δ</mi><msub><mi>x</mi><mrow><mi>i</mi><mi>j</mi></mrow></msub><mo>=</mo><msub><mi>x</mi><mrow><mi>i</mi><mo>,</mo><mn>30</mn><mo>,</mo><mi>j</mi></mrow></msub><mo>−</mo><msub><mi>x</mi><mrow><mi>i</mi><mo>,</mo><mn>1</mn><mo>,</mo><mi>j</mi></mrow></msub><mo>.</mo></math>",
    "score": "<math display='block'><msub><mi>a</mi><mi>i</mi></msub><mo>=</mo><mfrac><mn>1</mn><mn>63</mn></mfrac><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mn>63</mn></munderover><msup><mrow><mo>(</mo><msub><mi>z</mi><mrow><mi>i</mi><mi>k</mi></mrow></msub><mo>−</mo><msub><mover><mi>z</mi><mo>^</mo></mover><mrow><mi>i</mi><mi>k</mi></mrow></msub><mo>)</mo></mrow><mn>2</mn></msup><mo>.</mo></math>",
    "cdf": "<math display='block'><msub><mi>c</mi><mi>i</mi></msub><mo>=</mo><mfrac><mn>1</mn><mi>N</mi></mfrac><munderover><mo>∑</mo><mrow><mi>n</mi><mo>=</mo><mn>1</mn></mrow><mi>N</mi></munderover><mi>𝟙</mi><mo>(</mo><msubsup><mi>a</mi><mi>n</mi><mtext>train</mtext></msubsup><mo>≤</mo><msub><mi>a</mi><mi>i</mi></msub><mo>)</mo><mo>.</mo></math>",
    "ewma": "<math display='block'><msub><mi>m</mi><mi>i</mi></msub><mo>=</mo><mi>α</mi><msub><mi>c</mi><mi>i</mi></msub><mo>+</mo><mo>(</mo><mn>1</mn><mo>−</mo><mi>α</mi><mo>)</mo><msub><mi>m</mi><mrow><mi>i</mi><mo>−</mo><mn>1</mn></mrow></msub><mo>,</mo><mspace width='2em'/><mi>α</mi><mo>=</mo><mn>0.20</mn><mo>,</mo></math>",
    "violation": "<math display='block'><msub><mi>v</mi><mi>i</mi></msub><mo>=</mo><mi>𝟙</mi><mo>(</mo><msub><mi>m</mi><mi>i</mi></msub><mo>&gt;</mo><msub><mi>τ</mi><msub><mi>r</mi><mi>i</mi></msub></msub><mo>)</mo><mo>.</mo></math>",
    "contribution": "<math display='block'><msub><mi>g</mi><mrow><mi>i</mi><mi>j</mi></mrow></msub><mo>=</mo><mfrac><mrow><msup><mrow><mo>(</mo><msubsup><mi>z</mi><mrow><mi>i</mi><mi>j</mi></mrow><mi>μ</mi></msubsup><mo>−</mo><msubsup><mover><mi>z</mi><mo>^</mo></mover><mrow><mi>i</mi><mi>j</mi></mrow><mi>μ</mi></msubsup><mo>)</mo></mrow><mn>2</mn></msup><mo>+</mo><msup><mrow><mo>(</mo><msubsup><mi>z</mi><mrow><mi>i</mi><mi>j</mi></mrow><mi>σ</mi></msubsup><mo>−</mo><msubsup><mover><mi>z</mi><mo>^</mo></mover><mrow><mi>i</mi><mi>j</mi></mrow><mi>σ</mi></msubsup><mo>)</mo></mrow><mn>2</mn></msup><mo>+</mo><msup><mrow><mo>(</mo><msubsup><mi>z</mi><mrow><mi>i</mi><mi>j</mi></mrow><mi>Δ</mi></msubsup><mo>−</mo><msubsup><mover><mi>z</mi><mo>^</mo></mover><mrow><mi>i</mi><mi>j</mi></mrow><mi>Δ</mi></msubsup><mo>)</mo></mrow><mn>2</mn></msup></mrow><mn>63</mn></mfrac><mo>.</mo></math>",
    "far": "<math display='block'><mi>FAR</mi><mo>=</mo><mfrac><mtext>false-positive active endpoints</mtext><mtext>proxy-healthy endpoints</mtext></mfrac><mo>,</mo></math>",
}


def equation_html(latex: str) -> str:
    value = re.sub(r"\s+", " ", latex).strip()
    if value.startswith("o_e"):
        key = "o_e"
    elif value.startswith(r"\bar{x}"):
        key = "barx"
    elif value.startswith("s_{ij}"):
        key = "std"
    elif value.startswith(r"\Delta x"):
        key = "delta"
    elif value.startswith("a_i"):
        key = "score"
    elif value.startswith("c_i"):
        key = "cdf"
    elif value.startswith("m_i"):
        key = "ewma"
    elif value.startswith("v_i"):
        key = "violation"
    elif value.startswith("g_{ij}"):
        key = "contribution"
    elif value.startswith(r"\mathrm{FAR}"):
        key = "far"
    else:
        raise ValueError(f"Unmapped display equation: {value}")
    return f'<div class="equation">{EQUATIONS[key]}</div>'


def parse_row(line: str) -> list[str]:
    return [cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def table_html(headers: list[str], rows: list[list[str]], bib: dict[str, dict[str, str]]) -> str:
    def one_table(columns: list[int], css_class: str = "") -> str:
        head = "".join(f"<th>{rich_text(headers[index], bib)}</th>" for index in columns)
        body = "".join(
            "<tr>" + "".join(f"<td>{rich_text(row[index], bib)}</td>" for index in columns) + "</tr>"
            for row in rows
        )
        return f'<table class="{css_class}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'

    if "Exact evidence" in headers:
        evidence = headers.index("Exact evidence")
        study = headers.index("Study")
        main = [index for index in range(len(headers)) if index != evidence]
        return (
            '<section class="landscape">' + one_table(main, "dense")
            + '<h4>Table 4 evidence locators (audit detail retained from the source table)</h4>'
            + one_table([study, evidence], "evidence") + "</section>"
        )
    css = "dense" if len(headers) >= 7 else ""
    return f'<section>{one_table(list(range(len(headers))), css)}</section>'


CSS = r"""
@page { size: A4 portrait; margin: 16mm 16mm 18mm; }
@page landscape { size: A4 landscape; margin: 13mm; }
* { box-sizing: border-box; }
body { font-family: Georgia, 'Times New Roman', serif; color: #172033; font-size: 10pt; line-height: 1.36; margin: 0; }
.cover { min-height: 245mm; display: flex; flex-direction: column; justify-content: center; text-align: center; page-break-after: always; }
.cover h1 { font-size: 25pt; line-height: 1.12; color: #17365d; margin: 0 0 12mm; }
.cover .notice { border: 1px solid #4f81bd; background: #edf4fb; padding: 4mm; margin: 10mm auto; max-width: 155mm; font-family: Arial, sans-serif; font-size: 9pt; }
h2 { font-family: Arial, sans-serif; color: #17365d; font-size: 16pt; border-bottom: 1px solid #9eb6ce; padding-bottom: 1.5mm; margin: 7mm 0 3mm; break-after: avoid; }
h3 { font-family: Arial, sans-serif; color: #24527a; font-size: 12pt; margin: 5mm 0 2mm; break-after: avoid; }
h4 { font-family: Arial, sans-serif; color: #24527a; font-size: 10pt; margin: 4mm 0 2mm; break-after: avoid; }
p { margin: 0 0 2.5mm; orphans: 3; widows: 3; }
ol, ul { margin: 1mm 0 3mm 6mm; padding-left: 5mm; }
li { margin-bottom: 1mm; }
.keywords { font-family: Arial, sans-serif; font-size: 9pt; }
.math-inline { font-family: Cambria Math, 'STIX Two Math', serif; white-space: nowrap; }
.equation { font-family: Cambria Math, 'STIX Two Math', serif; text-align: center; font-size: 12pt; margin: 3mm 0; break-inside: avoid; }
math { font-family: Cambria Math, 'STIX Two Math', serif; }
figure { margin: 5mm 0; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; max-height: 185mm; object-fit: contain; }
figcaption, .table-caption { font-family: Arial, sans-serif; font-size: 8.5pt; line-height: 1.25; text-align: left; margin: 1.5mm 0 3mm; }
table { border-collapse: collapse; width: 100%; margin: 2mm 0 4mm; font-family: Arial, sans-serif; font-size: 7.5pt; line-height: 1.18; }
thead { display: table-header-group; }
th { background: #dce6f1; color: #17365d; font-weight: 700; }
th, td { border: 0.35pt solid #8799aa; padding: 1.2mm; vertical-align: top; overflow-wrap: anywhere; }
tr { break-inside: avoid; }
.dense { font-size: 6.4pt; line-height: 1.12; }
.evidence { font-size: 6.8pt; }
.landscape { page: landscape; page-break-before: always; page-break-after: always; }
.references p { font-size: 8.3pt; padding-left: 6mm; text-indent: -6mm; margin-bottom: 2mm; }
code { font-family: Consolas, monospace; font-size: 0.9em; }
a { color: #1f4e79; text-decoration: none; }
"""


def build(repo: Path, output: Path) -> None:
    manuscript_dir = repo / "docs" / "manuscript" / "v1"
    lines = (manuscript_dir / "MANUSCRIPT_V1.md").read_text(encoding="utf-8").splitlines()
    bib = read_bib(manuscript_dir / "references_v1.bib")
    parts = ["<!doctype html><html><head><meta charset='utf-8'>", f"<style>{CSS}</style></head><body>"]
    parts.append("""<section class="cover"><h1>Context-Aware Reconstruction-Based Anomaly Alerting for Multi-Regime Turbofan Degradation</h1><p><strong>[AUTHOR 1], [AUTHOR 2]</strong></p><p>[DEPARTMENT], [INSTITUTION], [CITY, COUNTRY]</p><p>Corresponding author: [CORRESPONDING EMAIL]</p><div class="notice"><strong>Guide-review copy.</strong> Alternative Microsoft Edge HTML/MathML rendering; not a LaTeX compilation. Manuscript V1 · independent audit completed · guide review requested.</div></section>""")
    in_yaml = False
    yaml_done = False
    in_equation = False
    equation: list[str] = []
    skip_reference_stub = False
    before_abstract = True
    list_kind: str | None = None
    index = 0

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            parts.append(f"</{list_kind}>")
            list_kind = None

    while index < len(lines):
        line = lines[index]
        if not yaml_done and line.strip() == "---":
            in_yaml = not in_yaml
            if not in_yaml:
                yaml_done = True
            index += 1
            continue
        if in_yaml or line.startswith("# "):
            index += 1
            continue
        if line.strip() == "$$":
            close_list()
            if not in_equation:
                in_equation = True
                equation = []
            else:
                parts.append(equation_html(" ".join(equation)))
                in_equation = False
            index += 1
            continue
        if in_equation:
            equation.append(line)
            index += 1
            continue
        if line.startswith("<!--"):
            index += 1
            continue
        figure = re.match(r"^!\[(.+)\]\(([^)]+)\)", line)
        if figure:
            close_list()
            caption = figure.group(1)
            relative = figure.group(2).split("){", 1)[0]
            image_path = (manuscript_dir / relative).resolve()
            if not image_path.is_file():
                raise FileNotFoundError(image_path)
            parts.append(f"<figure><img src='{image_path.as_uri()}' alt='{html.escape(caption)}'><figcaption>{rich_text(caption, bib)}</figcaption></figure>")
            index += 1
            continue
        if line.startswith("|"):
            close_list()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            headers = parse_row(table_lines[0])
            rows = [parse_row(row) for row in table_lines[2:]]
            parts.append(table_html(headers, rows, bib))
            continue
        heading = re.match(r"^(#{2,4})\s+(.+)$", line)
        if heading:
            close_list()
            level = len(heading.group(1))
            text = heading.group(2)
            if text == "References":
                skip_reference_stub = True
            else:
                if text == "Abstract":
                    before_abstract = False
                parts.append(f"<h{level}>{rich_text(text, bib)}</h{level}>")
            index += 1
            continue
        if line.startswith("**Table "):
            close_list()
            parts.append(f"<p class='table-caption'>{rich_text(line, bib)}</p>")
            index += 1
            continue
        numbered = re.match(r"^\d+\.\s+(.+)$", line)
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if numbered or bullet:
            desired = "ol" if numbered else "ul"
            if list_kind != desired:
                close_list()
                list_kind = desired
                parts.append(f"<{desired}>")
            match = numbered or bullet
            assert match
            parts.append(f"<li>{rich_text(match.group(1), bib)}</li>")
            index += 1
            continue
        close_list()
        if not line.strip() or skip_reference_stub or before_abstract:
            index += 1
            continue
        css_class = " class='keywords'" if line.startswith("**Keywords:") else ""
        parts.append(f"<p{css_class}>{rich_text(line, bib)}</p>")
        index += 1
    close_list()
    parts.append("<section class='references'><h2>References</h2>")
    labels = citation_labels(bib)
    for entry in sorted(bib.values(), key=lambda item: (item["author"].split(" and ")[0].split()[-1], item["year"], item["title"])):
        venue = entry.get("journal", entry.get("booktitle", ""))
        identifier = f"https://doi.org/{entry['doi']}" if entry.get("doi") else entry.get("url", "")
        authors = entry["author"].replace(" and ", ", ")
        year_label = labels[entry["key"]].rsplit(", ", 1)[-1]
        parts.append(f"<p>{html.escape(authors)} ({html.escape(year_label)}). {html.escape(entry['title'])}. <em>{html.escape(venue)}</em>. {html.escape(identifier)}</p>")
    parts.append("</section></body></html>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")
    rendered = output.read_text(encoding="utf-8")
    if rendered.count("<figure>") != 5 or rendered.count("<table") != 5 or rendered.count("<math") != 10:
        raise RuntimeError("Guide HTML completeness check failed")
    if len(bib) != 20:
        raise RuntimeError("Guide HTML bibliography must contain 20 entries")
    print(f"Wrote {output}")
    print("Completeness: 5 figures, 4 source tables (Table 4 split into two displays), 10 equations, 20 references")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.repo_root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
