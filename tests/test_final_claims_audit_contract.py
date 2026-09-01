import json
import re
import hashlib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs" / "research"

ALLOWED_STATUSES = {
    "supported_confirmatory",
    "supported_validation_only",
    "supported_implementation",
    "partially_supported",
    "not_supported",
    "future_work",
    "prohibited_wording",
}


def test_final_claims_audit_has_all_required_claims_and_fields():
    payload = json.loads(
        (RESEARCH / "final_claims_audit.json").read_text(encoding="utf-8")
    )
    claims = payload["claims"]

    assert payload["schema_version"] == "1.0.0"
    assert payload["audit_id"] == "fd002-final-claims-audit-v1"
    assert len(claims) == 17
    assert {claim["claim_id"] for claim in claims} == {
        f"FCA-{claim_id:03d}" for claim_id in range(1, 18)
    }
    assert all(claim["evidence_classification"] in ALLOWED_STATUSES for claim in claims)
    required = {
        "claim_id",
        "topic",
        "proposed_paper_wording",
        "evidence_sources",
        "evidence_classification",
        "limitations",
        "permitted_wording",
        "prohibited_or_exaggerated_wording",
    }
    assert all(required == set(claim) for claim in claims)
    assert all(claim["evidence_sources"] for claim in claims)
    assert all(
        (ROOT / source).exists()
        for claim in claims
        for source in claim["evidence_sources"]
    )
    assert all(
        claim["limitations"]
        and claim["permitted_wording"]
        and claim["prohibited_or_exaggerated_wording"]
        for claim in claims
    )


def test_claim_status_counts_and_boundaries_are_frozen():
    payload = json.loads(
        (RESEARCH / "final_claims_audit.json").read_text(encoding="utf-8")
    )
    claims = payload["claims"]
    observed = Counter(claim["evidence_classification"] for claim in claims)

    assert observed == {
        "supported_confirmatory": 8,
        "supported_validation_only": 2,
        "supported_implementation": 3,
        "partially_supported": 1,
        "not_supported": 2,
        "prohibited_wording": 1,
    }
    by_id = {claim["claim_id"]: claim for claim in claims}
    assert by_id["FCA-006"]["evidence_classification"] == "supported_confirmatory"
    assert "3.2440%" in by_id["FCA-006"]["permitted_wording"]
    assert by_id["FCA-007"]["evidence_classification"] == "supported_confirmatory"
    assert "25 cycles" in by_id["FCA-007"]["permitted_wording"]
    assert by_id["FCA-010"]["evidence_classification"] == "partially_supported"
    assert by_id["FCA-015"]["evidence_classification"] == "not_supported"
    assert by_id["FCA-016"]["evidence_classification"] == "not_supported"
    assert by_id["FCA-017"]["evidence_classification"] == "prohibited_wording"


def test_post_confirmatory_roadmap_preserves_result_and_attribution_math():
    roadmap = (RESEARCH / "POST_CONFIRMATORY_IMPLEMENTATION_ROADMAP.md").read_text(
        encoding="utf-8"
    )

    assert "## Frozen-result rule" in roadmap
    assert "## Research-required" in roadmap
    assert "## Implementation-required" in roadmap
    assert "## Optional or future research" in roadmap
    assert "cannot alter, replace, pool with, or retroactively optimize" in roadmap
    assert "squared residuals divided by 63" in roadmap
    assert "21 sensor contributions must sum" in roadmap
    assert "PCA reconstruction contribution" in roadmap
    assert "not SHAP" in roadmap
    assert "No online recalibration, score fusion, threshold selection" in roadmap


def test_post_confirmatory_docs_have_no_stale_pre_confirmatory_status():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "guides" / "PROJECT_UNDERSTANDING_GUIDE.md").read_text(
        encoding="utf-8"
    )

    assert "The first valid frozen internal held-out confirmatory run is complete" in readme
    assert "no held-out availability check or confirmatory evaluation has occurred" not in readme
    assert "Its final controlled refit is pending" not in guide
    assert "Threshold/event evaluation, sensitivity, and the untouched internal test remain pending" not in guide


def test_new_markdown_relative_links_resolve():
    documents = [
        ROOT / "README.md",
        RESEARCH / "FINAL_CLAIMS_AUDIT.md",
        RESEARCH / "LITERATURE_EVIDENCE_MATRIX_V4.md",
        RESEARCH / "LITERATURE_TO_PROJECT_METRIC_COMPARISON.md",
        RESEARCH / "CLAIMS_LEDGER.md",
    ]
    pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")

    for document in documents:
        for target in pattern.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            assert (document.parent / target).resolve().exists(), (
                f"Broken local link in {document.relative_to(ROOT)}: {target}"
            )


def test_registered_governance_derivative_hashes_match_manifest():
    registered = {
        "LITERATURE_EVIDENCE_MATRIX_V4.json": "7e78011c3feeaf6b96eae56d45ee3ae073046daaccf44d7ecfd5aa32a1792a86",
        "literature_to_project_metric_comparison.json": "9bc9920d05b77a0841cb698d87b98ba0ce519bcb113a99860c17fbb2983dcb5b",
        "literature_audit_summary.json": "ba60ed5801840fcf78074335859b52b46c011516cd83900595d95ce378dcb69f",
        "FINAL_CLAIMS_AUDIT.md": "3ac5147f005a6eddc945cf80d2410a157bef76578b3a9baeb5ae32ebde154384",
        "final_claims_audit.json": "f10cdeb3288d70ab43b99cee7eeb8bd4685b02f3f57e1e07108c63fb322f444c",
        "POST_CONFIRMATORY_IMPLEMENTATION_ROADMAP.md": "6b663f779ff343e900933632f1c79155b34361c5de805a59309305821fa200ab",
    }
    manifest = (RESEARCH / "ARTIFACT_MANIFEST.md").read_text(encoding="utf-8")

    for name, expected in registered.items():
        canonical_lf = (RESEARCH / name).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(canonical_lf).hexdigest() == expected
        assert expected in manifest
