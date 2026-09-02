from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs" / "research"
EVIDENCE = RESEARCH / "CORE_MANUSCRIPT_EVIDENCE_V1.json"
SUMMARY = RESEARCH / "core_manuscript_extraction_summary_v1.json"
PROTOCOL = ROOT / "configs/research/fd002-core-literature-extraction-protocol-v1.json"

FULL_TEXT_LEVELS = {
    "publisher_full_text_verified",
    "author_manuscript_verified",
    "arxiv_full_text_verified",
    "institutional_repository_verified",
    "authoritative_html_verified",
}


def _payload():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_core_evidence_identity_access_and_replacement_contract():
    payload = _payload()
    papers = payload["papers"]
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    assert len(papers) == 20
    assert 15 <= len(papers) <= 25
    assert len({paper["core_paper_id"] for paper in papers}) == 20
    assert len({paper["title"].casefold() for paper in papers}) == 20
    assert len({paper["stable_identifier"].casefold() for paper in papers}) == 20
    assert all(paper["authors"] and "NR" not in paper["authors"] for paper in papers)
    assert {paper["evidence_access_level"] for paper in papers} <= FULL_TEXT_LEVELS
    assert all(re.fullmatch(r"[0-9a-f]{64}", paper["source_document_sha256"]) for paper in papers)
    assert payload["replacement_log"] == [{
        "selected_paper_id": "LIT-019",
        "replacement_paper_id": "LIT-051",
        "reserve_order": 1,
        "reason": "Publisher metadata and abstract were accessible, but a legal complete manuscript exposing methodology/results/limitations was not located; replacement followed the preregistered order before extracting replacement results.",
    }]
    assert protocol["ordered_reserve"][0]["paper_id"] == "LIT-051"
    assert "LIT-019" not in {paper["core_paper_id"] for paper in papers}


def test_numerical_evidence_is_located_full_text_and_never_direct():
    payload = _payload()
    papers = {paper["core_paper_id"]: paper for paper in payload["papers"]}
    values = payload["numerical_values"]

    assert len(values) == 43
    assert len({value["value_id"] for value in values}) == len(values)
    for value in values:
        assert papers[value["paper_id"]]["evidence_access_level"] in FULL_TEXT_LEVELS
        assert value["page"] != "NR"
        assert value["section"] != "NR"
        assert value["table_or_figure"] != "NR"
        assert value["row"] != "NR"
        assert value["column"] != "NR"
        assert value["result_scope"] in {"test", "test_proxy", "official_test_rul"}
        assert value["directly_comparable_with_project"] is False
    declared = {value["value_id"] for value in values}
    linked = {item for paper in papers.values() for item in paper["numerical_value_ids"]}
    assert linked == declared


def test_category_and_project_metric_boundaries_are_exact():
    payload = _payload()
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    categories = Counter(paper["comparison_category"] for paper in payload["papers"])

    assert {key: categories[key] for key in "ABCD"} == {"A": 0, "B": 2, "C": 11, "D": 7}
    assert not any(paper["direct_numerical_comparison_permitted"] for paper in payload["papers"])
    assert payload["conclusion"] == (
        "No directly protocol-equivalent published comparator was identified "
        "in the manuscript-grade core literature set."
    )
    authority = json.loads((ROOT / "configs/evaluation/fd002-confirmatory-results-v1.json").read_text(encoding="utf-8"))
    extracted = payload["project_metrics"]
    for row, registered in zip(extracted["rows"], authority["primary_endpoint_results"], strict=True):
        assert row["far_percent"] == round(registered["endpoint_false_alert_rate_percent"], 4)
        assert row["coverage_percent"] == round(registered["engine_detection_coverage_percent"], 2)
        assert row["median_delay_cycles"] == registered["median_delay_cycles"]
        assert row["pr_auc"] == round(registered["pr_auc"], 5)
        assert row["roc_auc"] == round(registered["roc_auc"], 5)
    assert extracted["aggregate_median_delay_cycles"] == 25
    assert extracted["delay_aspiration_met"] is False
    assert summary["verified_numerical_value_count"] == 43
    assert summary["direct_comparison_count"] == 0


def test_csv_bibtex_and_protected_literature_authorities():
    with (RESEARCH / "CORE_MANUSCRIPT_EVIDENCE_V1.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 20
    assert {row["core_paper_id"] for row in rows} == {
        paper["core_paper_id"] for paper in _payload()["papers"]
    }

    bib = (RESEARCH / "MANUSCRIPT_CORE_CITATIONS_V1.bib").read_text(encoding="utf-8")
    assert len(re.findall(r"^@(article|inproceedings)\{core\d{3},$", bib, re.MULTILINE)) == 20
    assert bib.count("\n}\n") == 20

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for authority in protocol["preserved_authorities"]:
        observed = hashlib.sha256((ROOT / authority["path"]).read_bytes()).hexdigest()
        assert observed == authority["sha256"]


def test_no_binary_manuscript_is_a_tracked_output():
    evidence_paths = {
        "docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.md",
        "docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.csv",
        "docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json",
        "docs/research/CORE_LITERATURE_SOURCE_VERIFICATION_V1.md",
        "docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib",
        "docs/research/core_manuscript_extraction_summary_v1.json",
    }
    assert all(not path.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")) for path in evidence_paths)
    assert _payload()["scientific_boundaries"] == {
        "held_out_or_official_data_opened": False,
        "modeling_tuning_or_recalibration": False,
        "project_metrics_recalculated": False,
        "pdfs_committed": False,
    }
