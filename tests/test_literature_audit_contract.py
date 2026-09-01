import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs" / "research"
V3_PATH = RESEARCH / "Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx"
V3_SHA256 = "ae173e281fbcbccae7da91920980f4d208a908d2f1a6a6dcfb54af5ebdf05ac3"

ACCESS_LEVELS = {
    "full_text_verified",
    "author_manuscript_verified",
    "authoritative_html_full_text_verified",
    "abstract_only",
    "metadata_only",
    "full_text_unavailable",
    "pending_verification",
}


def _load_json(name: str):
    return json.loads((RESEARCH / name).read_text(encoding="utf-8"))


def test_v4_matrix_schema_identity_and_protected_source_hash():
    payload = _load_json("LITERATURE_EVIDENCE_MATRIX_V4.json")
    records = payload["records"]

    assert payload["schema_version"] == "4.0.0"
    assert len(records) == 100
    assert len({record["paper_id"] for record in records}) == 100
    assert len({record["title"].casefold() for record in records}) == 100
    assert len({record["doi_or_stable_identifier"].casefold() for record in records}) == 100
    assert {record["evidence_access_level"] for record in records} <= ACCESS_LEVELS
    assert hashlib.sha256(V3_PATH.read_bytes()).hexdigest() == V3_SHA256
    assert payload["source_authority"]["sha256"] == V3_SHA256
    assert payload["source_authority"]["preserved_unchanged"] is True


def test_numeric_evidence_and_comparison_category_boundaries():
    records = _load_json("LITERATURE_EVIDENCE_MATRIX_V4.json")["records"]
    numeric_records = [
        record for record in records
        if record["exact_reported_metric_values"] != "NR"
    ]

    assert {record["paper_id"] for record in numeric_records} == {
        "LIT-007",
        "LIT-012",
        "LIT-013",
    }
    assert all(
        record["evidence_access_level"]
        in {
            "full_text_verified",
            "author_manuscript_verified",
            "authoritative_html_full_text_verified",
        }
        and record["evidence_location"] != "NR"
        for record in numeric_records
    )
    assert all(
        record["exact_reported_metric_values"] == "NR"
        for record in records
        if record["evidence_access_level"] in {"abstract_only", "metadata_only"}
    )
    assert all(record["comparison_category"] in "ABCD" for record in records)
    assert all(
        record["direct_comparison_permitted"]
        == (record["comparison_category"] == "A")
        for record in records
    )
    assert not any(record["direct_comparison_permitted"] for record in records)


def test_audit_summary_counts_are_complete_and_consistent():
    summary = _load_json("literature_audit_summary.json")

    assert summary["total_unique_papers"] == 100
    assert summary["category_counts"] == {"A": 0, "B": 2, "C": 23, "D": 75}
    assert summary["full_text_equivalent_count"] == 69
    assert summary["evidence_access_counts"]["abstract_only"] == 27
    assert summary["evidence_access_counts"]["metadata_only"] == 4
    assert summary["direct_numerical_comparison_count"] == 0
    assert summary["duplicates_removed"] == 0
    assert summary["invalid_records_removed"] == 0


def test_comparison_table_schema_and_exact_project_authority_values():
    comparison = _load_json("literature_to_project_metric_comparison.json")
    authority = _load_json("../../configs/evaluation/fd002-confirmatory-results-v1.json")
    rows = comparison["rows"]

    required = {
        "paper",
        "dataset_subset",
        "task",
        "split",
        "label_definition",
        "model",
        "metric",
        "published_value",
        "our_compatible_value",
        "comparison_category",
        "direct_comparison_permitted",
        "evidence_location",
        "caveat",
    }
    assert all(required <= set(row) for row in rows)
    assert {row["paper_id"] for row in rows} == {
        f"LIT-{paper_id:03d}" for paper_id in range(1, 101)
    }
    assert comparison["direct_equivalent_comparator_found"] is False
    assert not any(row["direct_comparison_permitted"] for row in rows)

    expected = authority["primary_endpoint_results"]
    actual = comparison["project_results"]
    assert len(actual) == len(expected) == 3
    for observed, registered in zip(actual, expected, strict=True):
        assert observed["far_percent"] == registered["endpoint_false_alert_rate_percent"]
        assert observed["engine_coverage_percent"] == registered["engine_detection_coverage_percent"]
        assert observed["median_delay_cycles"] == registered["median_delay_cycles"]
        assert observed["pr_auc"] == registered["pr_auc"]
        assert observed["roc_auc"] == registered["roc_auc"]
        assert math.isclose(
            observed["far_per_1000"],
            registered["endpoint_false_alert_rate_percent"] * 10,
            rel_tol=0.0,
            abs_tol=1e-14,
        )
    assert comparison["aggregate_median_delay_cycles"] == 25.0
    assert comparison["aggregate_delay_aspiration_met"] is False


def test_machine_readable_csvs_parse_and_markdown_declares_no_direct_comparator():
    for name in (
        "LITERATURE_EVIDENCE_MATRIX_V4.csv",
        "literature_to_project_metric_comparison.csv",
    ):
        with (RESEARCH / name).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert rows

    comparison_md = (RESEARCH / "LITERATURE_TO_PROJECT_METRIC_COMPARISON.md").read_text(
        encoding="utf-8"
    )
    assert (
        "No directly protocol-equivalent published comparator was identified "
        "in the verified literature set."
    ) in comparison_md
