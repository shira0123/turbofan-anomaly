"""Static, evidence-bounded verification for the manuscript V1 package.

This script reads manuscript sources, generated presentation assets, the verified
core bibliography, and provenance only. It never opens scientific datasets,
model artifacts, score traces, or per-engine results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


REQUIRED_SECTIONS = (
    "Abstract",
    "Introduction",
    "Related Work",
    "Dataset and Experimental Protocol",
    "Proposed Methodology",
    "Evaluation Metrics",
    "Performance Analysis and Results",
    "Discussion",
    "Limitations and Threats to Validity",
    "Reproducibility and Data Governance",
    "Conclusion and Future Work",
    "References",
)

REQUIRED_MD_SNIPPETS = (
    "Before accessing the internal held-out partition, the complete alerting configuration was locked",
    "P1/K=6",
    "5,037",
    "0.84969513",
    "0.83280767",
    "0.82212053",
    "0.78916934",
    "0.77240729",
    "265 false-positive active endpoints among 8,169",
    "67/7,095",
    "31/6,016",
    "3.2440%",
    "0.9443%",
    "0.5153%",
    "51.92%",
    "78.85%",
    "84.62%",
    "0.60267",
    "0.94762",
    "0.80974",
    "0.92673",
    "0.82745",
    "0.86758",
    "median of the three proxy-specific medians",
    "No directly protocol-equivalent published comparator was identified",
)

FIGURES = tuple(f"figures/figure_{index:02d}_" for index in range(1, 6))
TABLES = tuple(f"tables/table_{index:02d}_" for index in range(1, 5))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def balanced_braces(text: str) -> bool:
    depth = 0
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repo_root.resolve()
    manuscript_dir = root / "docs" / "manuscript" / "v1"

    md_path = manuscript_dir / "MANUSCRIPT_V1.md"
    tex_path = manuscript_dir / "manuscript_v1.tex"
    bib_path = manuscript_dir / "references_v1.bib"
    provenance_path = manuscript_dir / "ARTIFACT_PROVENANCE.json"
    core_bib_path = root / "docs" / "research" / "MANUSCRIPT_CORE_CITATIONS_V1.bib"
    for path in (md_path, tex_path, bib_path, provenance_path, core_bib_path):
        require(path.is_file(), f"Required file missing: {path.relative_to(root)}")

    md = md_path.read_text(encoding="utf-8")
    tex = tex_path.read_text(encoding="utf-8")
    bib = bib_path.read_text(encoding="utf-8")
    core_bib = core_bib_path.read_text(encoding="utf-8")

    countable = re.sub(r"\A---.*?---\s*", "", md, flags=re.DOTALL)
    countable = re.sub(
        r"<!-- latex-table:.*?<!-- end-latex-table -->",
        "",
        countable,
        flags=re.DOTALL,
    )
    countable = re.sub(r"^!\[.*$", "", countable, flags=re.MULTILINE)
    countable = re.sub(r"## References.*\Z", "", countable, flags=re.DOTALL)
    word_count = len(re.findall(r"\b[\w][\w'-]*\b", countable, flags=re.UNICODE))
    require(5500 <= word_count <= 7000, f"Markdown word count outside requested range: {word_count}")
    for section in REQUIRED_SECTIONS:
        require(section in md, f"Markdown section missing: {section}")
        if section == "Abstract":
            require("\\begin{abstract}" in tex, "LaTeX abstract environment missing")
        elif section != "References":
            require(section in tex, f"LaTeX section/content missing: {section}")

    for snippet in REQUIRED_MD_SNIPPETS:
        require(snippet in md, f"Required evidence wording/value missing from Markdown: {snippet}")
    require("Before accessing the internal held-out partition" in tex, "Freeze definition missing from LaTeX")
    for value in ("3.2440\\%", "0.9443\\%", "0.5153\\%", "51.92\\%", "78.85\\%", "84.62\\%"):
        require(value in tex, f"Required confirmatory value missing from LaTeX: {value}")

    md_citations = set(re.findall(r"@([A-Za-z0-9_:-]+)", md))
    tex_citations = {
        key
        for group in re.findall(r"\\citep\{([^}]+)\}", tex)
        for key in group.split(",")
    }
    bib_keys = set(re.findall(r"^@[A-Za-z]+\{([^,]+),", bib, flags=re.MULTILINE))
    require(len(md_citations) == 20, f"Expected 20 unique citations, found {len(md_citations)}")
    require(md_citations == tex_citations == bib_keys, "Markdown, LaTeX, and bibliography citation keys differ")
    require(bib.replace("\r\n", "\n").strip() == core_bib.replace("\r\n", "\n").strip(), "Manuscript bibliography is not a faithful cited subset of the verified core bibliography")

    require(md.count("<!-- latex-table:") == 4, "Expected four Markdown/LaTeX table controls")
    require(tex.count("\\input{tables/") == 4, "Expected four LaTeX table inputs")
    require(md.count("](figures/") == 5, "Expected five Markdown figures")
    require(tex.count("\\begin{figure}") == 5, "Expected five LaTeX figures")
    for prefix in FIGURES:
        matches = list((manuscript_dir / "figures").glob(Path(prefix).name + "*.png"))
        require(len(matches) == 1, f"Expected one PNG for {prefix}, found {len(matches)}")
    for prefix in TABLES:
        matches = list((manuscript_dir / "tables").glob(Path(prefix).name + "*.tex"))
        require(len(matches) == 1, f"Expected one LaTeX table for {prefix}, found {len(matches)}")

    for line in md.splitlines():
        if "Gate 4" in line:
            context = line.lower()
            require(
                "governance" in context or "pre-held-out policy freeze" in context,
                f"Unexplained Gate 4 occurrence: {line[:160]}",
            )
    lower_md = md.lower()
    for phrase in ("we propose a novel", "state-of-the-art", "outperforms", "superior to", "real-time system"):
        require(phrase not in lower_md, f"Unsupported promotional phrase present: {phrase}")

    require(balanced_braces(tex), "LaTeX braces are unbalanced")
    begins = re.findall(r"\\begin\{([^}]+)\}", tex)
    ends = re.findall(r"\\end\{([^}]+)\}", tex)
    require(sorted(begins) == sorted(ends), "LaTeX begin/end environments differ")
    require(tex.count("\\section{") == 10, "Expected ten numbered LaTeX sections")
    require("\\bibliography{references_v1}" in tex, "LaTeX bibliography link missing")

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    document_records = {item["path"]: item for item in provenance.get("manuscript_documents", [])}
    expected_documents = (
        "docs/manuscript/v1/MANUSCRIPT_V1.md",
        "docs/manuscript/v1/manuscript_v1.tex",
        "docs/manuscript/v1/references_v1.bib",
        "docs/manuscript/v1/MANUSCRIPT_CLAIMS_AUDIT_V1.md",
        "docs/manuscript/v1/MANUSCRIPT_REVIEW_CHECKLIST_V1.md",
        "docs/manuscript/v1/PLAIN_LANGUAGE_SUMMARY.md",
    )
    for relative in expected_documents:
        path = root / relative
        require(relative in document_records, f"Provenance document record missing: {relative}")
        require(document_records[relative]["sha256"] == sha256(path), f"Provenance hash mismatch: {relative}")

    print(f"Manuscript verification passed: {word_count} words excluding tables, captions, metadata, and references; {len(md_citations)} references, 5 figures, 4 tables.")
    print("Cross-format evidence, terminology, paths, bibliography, LaTeX structure, and provenance hashes passed.")


if __name__ == "__main__":
    main()
