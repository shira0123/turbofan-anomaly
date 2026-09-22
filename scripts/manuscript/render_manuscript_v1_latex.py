"""Render the controlled Markdown manuscript into a venue-neutral LaTeX source.

The renderer deliberately supports only the constructs used by MANUSCRIPT_V1.md.
Markdown tables are replaced by the checked, generated LaTeX table fragments.
No scientific data or model artifacts are opened.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT_DIR = ROOT / "docs" / "manuscript" / "v1"
SOURCE = MANUSCRIPT_DIR / "MANUSCRIPT_V1.md"
DESTINATION = MANUSCRIPT_DIR / "manuscript_v1.tex"


PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage[margin=1in]{geometry}
\usepackage[round,authoryear]{natbib}
\usepackage[hidelinks]{hyperref}
\usepackage{url}
\graphicspath{{./}}
\title{Context-Aware Reconstruction-Based Anomaly Alerting for Multi-Regime Turbofan Degradation}
\author{[AUTHOR 1] \and [AUTHOR 2]\\
[DEPARTMENT], [INSTITUTION], [CITY, COUNTRY]\\
Corresponding author: [CORRESPONDING EMAIL]}
\date{}
\begin{document}
\maketitle
"""


def protect(pattern: str, text: str, transform, tokens: list[str]) -> str:
    def replace(match: re.Match[str]) -> str:
        tokens.append(transform(match))
        return f"@@TOKEN{len(tokens) - 1}@@"

    return re.sub(pattern, replace, text)


def latex_text(text: str) -> str:
    """Convert the manuscript's restricted inline Markdown to LaTeX."""
    tokens: list[str] = []
    text = protect(r"\$[^$]+\$", text, lambda m: m.group(0), tokens)
    text = protect(
        r"\[(?=[^\]]*@core)[^\]]+\]",
        text,
        lambda m: "\\citep{" + ",".join(re.findall(r"@([A-Za-z0-9_:-]+)", m.group(0))) + "}",
        tokens,
    )
    text = protect(
        r"`([^`]+)`",
        text,
        lambda m: "\\texttt{" + escape_plain(m.group(1)) + "}",
        tokens,
    )
    text = protect(
        r"\*\*([^*]+)\*\*",
        text,
        lambda m: "\\textbf{" + escape_plain(m.group(1)) + "}",
        tokens,
    )
    text = escape_plain(text)
    for index, token in enumerate(tokens):
        text = text.replace(f"@@TOKEN{index}@@", token)
    return text


def escape_plain(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    escaped = "".join(replacements.get(char, char) for char in text)
    escaped = escaped.replace("–", "--").replace("—", "---")
    escaped = escaped.replace("“", "``").replace("”", "''").replace("’", "'")
    escaped = escaped.replace("×", r"\(\times\)")
    escaped = escaped.replace("→", r"\(\rightarrow\)")
    escaped = escaped.replace("≤", r"\(\leq\)").replace("≥", r"\(\geq\)")
    return escaped


def render(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").splitlines()
    if lines and lines[0] == "---":
        second = lines.index("---", 1)
        lines = lines[second + 1 :]

    output = [PREAMBLE.rstrip(), ""]
    in_abstract = False
    in_math = False
    skip_table = False
    skip_front_matter = True
    in_list: str | None = None

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append(f"\\end{{{in_list}}}")
            output.append("")
            in_list = None

    for line in lines:
        if skip_table:
            if line.strip() == "<!-- end-latex-table -->":
                skip_table = False
            continue

        table_match = re.fullmatch(r"<!-- latex-table: (.+) -->", line.strip())
        if table_match:
            close_list()
            output.extend([f"\\input{{{table_match.group(1)}}}", ""])
            skip_table = True
            continue

        if line.strip() == "$$":
            close_list()
            output.append(r"\]" if in_math else r"\[")
            output.append("")
            in_math = not in_math
            continue
        if in_math:
            output.append(line)
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            close_list()
            level, title = heading.groups()
            if level == "#":
                continue
            if title == "Abstract":
                skip_front_matter = False
                in_abstract = True
                output.append(r"\begin{abstract}")
                continue
            if in_abstract:
                output.extend([r"\end{abstract}", ""])
                in_abstract = False
            if title == "References":
                break
            command = "section" if level == "##" else "subsection"
            latex_title = re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", title)
            output.extend([f"\\{command}{{{latex_text(latex_title)}}}", ""])
            continue

        if skip_front_matter:
            continue

        figure = re.fullmatch(
            r"!\[(.+)\]\(([^)]+)\)\{#fig:([^\s}]+)\s+width=([0-9]+)%\}", line
        )
        if figure:
            close_list()
            caption, path, label, width = figure.groups()
            output.extend(
                [
                    r"\begin{figure}[tbp]",
                    r"\centering",
                    f"\\includegraphics[width={int(width) / 100:.2f}\\linewidth]{{{path}}}",
                    f"\\caption{{{latex_text(caption)}}}",
                    f"\\label{{fig:{label}}}",
                    r"\end{figure}",
                    "",
                ]
            )
            continue

        stripped = line.strip()
        if not stripped:
            close_list()
            output.append("")
            continue

        if stripped.startswith("**Keywords:**"):
            output.extend(
                [
                    r"\noindent\textbf{Keywords:} "
                    + latex_text(stripped.removeprefix("**Keywords:**").strip()),
                    "",
                ]
            )
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        if ordered or bullet:
            desired = "enumerate" if ordered else "itemize"
            if in_list != desired:
                close_list()
                in_list = desired
                output.append(f"\\begin{{{desired}}}")
            item = ordered.group(1) if ordered else bullet.group(1)
            output.append(r"\item " + latex_text(item))
            continue

        close_list()
        output.extend([latex_text(stripped), ""])

    close_list()
    if in_abstract:
        output.extend([r"\end{abstract}", ""])
    output.extend(
        [
            r"\bibliographystyle{plainnat}",
            r"\bibliography{references_v1}",
            r"\end{document}",
            "",
        ]
    )
    return "\n".join(output)


def main() -> None:
    rendered = render(SOURCE.read_text(encoding="utf-8"))
    DESTINATION.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {DESTINATION.relative_to(ROOT)} ({len(rendered.splitlines())} lines)")


if __name__ == "__main__":
    main()
