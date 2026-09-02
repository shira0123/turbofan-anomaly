from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs" / "research"
COMPARISON = RESEARCH / "core_literature_comparability_v1.json"


def test_core_comparability_has_all_papers_and_strict_categories():
    payload = json.loads(COMPARISON.read_text(encoding="utf-8"))
    evidence = json.loads((RESEARCH / "CORE_MANUSCRIPT_EVIDENCE_V1.json").read_text(encoding="utf-8"))
    rows = payload["rows"]

    assert len(rows) == 20
    assert {row["paper_id"] for row in rows} == {
        paper["core_paper_id"] for paper in evidence["papers"]
    }
    counts = Counter(row["comparison_category"] for row in rows)
    assert {key: counts[key] for key in "ABCD"} == {"A": 0, "B": 2, "C": 11, "D": 7}
    assert payload["direct_equivalent_comparator_found"] is False
    assert not any(row["direct_comparison_permitted"] for row in rows)
    assert all(row["our_compatible_value"] == "NR; no Category A metric alignment" for row in rows)


def test_comparability_csv_and_required_conclusion_parse():
    with (RESEARCH / "core_literature_comparability_v1.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 20
    assert set(rows[0]) >= {
        "paper_id", "dataset_subset", "task", "split", "label_definition",
        "model", "metric", "published_value", "our_compatible_value",
        "comparison_category", "direct_comparison_permitted",
        "evidence_location", "caveat",
    }
    conclusion = (
        "No directly protocol-equivalent published comparator was identified "
        "in the manuscript-grade core literature set."
    )
    assert conclusion in (RESEARCH / "CORE_LITERATURE_COMPARABILITY_V1.md").read_text(encoding="utf-8")
    assert conclusion in (RESEARCH / "CORE_LITERATURE_CLAIMS_IMPLICATIONS_V1.md").read_text(encoding="utf-8")


def test_official_fd002_assessment_is_secondary_and_nonexecuting():
    text = (RESEARCH / "FD002_OFFICIAL_TEST_LITERATURE_ASSESSMENT_V1.md").read_text(encoding="utf-8")
    assert "LIT-009 | yes | yes" in text
    assert "LIT-018 | yes | yes" in text
    assert "Perform a preregistered secondary RUL-proxy evaluation" in text
    assert "does not open, hash, inspect, preprocess, score, or summarize" in text
    assert "No such evaluation is authorized or implemented" in text


def test_claim_implications_preserve_frozen_scientific_boundaries():
    text = (RESEARCH / "CORE_LITERATURE_CLAIMS_IMPLICATIONS_V1.md").read_text(encoding="utf-8")
    assert "does not modify or supersede `FINAL_CLAIMS_AUDIT.md`" in text
    assert "State of the art" in text
    assert "Physical localization claims" in text
    assert "requires separate authorization" in text


def test_new_artifact_manifest_hashes_match_canonical_lf_content():
    expected = {
        "CORE_MANUSCRIPT_EVIDENCE_V1.md": "680ab4cfbfab75c4b72845311324b49cdc88651c5c5e2972afbbb89f353c9d39",
        "CORE_MANUSCRIPT_EVIDENCE_V1.csv": "3537e82f4eae9db8cec4149e3bb0bc32c6b8b374dd4c94b793cd96daea35fc81",
        "CORE_MANUSCRIPT_EVIDENCE_V1.json": "a82cd444f16b521a328f8e87bb38423d59edb890122ce25d59d39c3062ff5099",
        "core_manuscript_extraction_summary_v1.json": "f26f2c2a34f4fb5636e0858795c302674322f9eb3555f630c74e9f44b770bdc1",
        "CORE_LITERATURE_SOURCE_VERIFICATION_V1.md": "49faf477b440cce0125e5af549dd027d068613ae88ec6bca7dd381345ff8dbdf",
        "MANUSCRIPT_CORE_CITATIONS_V1.bib": "b02b5ecd59269ec8135d0573868589133dd7f49ca25ceda16bbe99a858f2b716",
        "CORE_LITERATURE_COMPARABILITY_V1.md": "b5f987b5823ca123889e045e917d04e00e56d47a30dd15b18d30491fbb821178",
        "core_literature_comparability_v1.csv": "a2cf51b0b2e234643f636ac7e20d849bca23a26138347d1aa043d4879a016ffd",
        "core_literature_comparability_v1.json": "c8276c4524474119c073b1f217baa941931de563699caf8f05840558c5ef221d",
        "FD002_OFFICIAL_TEST_LITERATURE_ASSESSMENT_V1.md": "aecb55a7ee8f4db6be78a251730ac57241ce7507a08f9f06396feebadee03251",
        "CORE_LITERATURE_CLAIMS_IMPLICATIONS_V1.md": "4631e603c56746d0d2214efe0ce88ad103fbc1e849c34a4c5fb04e086d92c3c6",
    }
    manifest = (RESEARCH / "ARTIFACT_MANIFEST.md").read_text(encoding="utf-8")
    for name, digest in expected.items():
        canonical = (RESEARCH / name).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        assert hashlib.sha256(canonical).hexdigest() == digest
        assert digest in manifest
