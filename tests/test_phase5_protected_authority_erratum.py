from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from turbofan_anomaly.workflows.run_alert_policy_study import (
    LIVING_DOCUMENTATION_PATH,
    _verify_reference,
    validate_phase5_protected_authority_erratum,
)


ROOT = Path(__file__).resolve().parents[1]
ERRATUM = ROOT / "configs/evaluation/fd002-phase5-protected-authority-erratum-v1.json"
PROTOCOL = ROOT / "configs/alerting/fd002-alert-policy-study-protocol-v2.json"


def _erratum() -> dict:
    return json.loads(ERRATUM.read_text(encoding="utf-8"))


def test_erratum_exempts_only_the_registered_living_documentation_path():
    erratum = _erratum()
    validate_phase5_protected_authority_erratum(erratum)
    assert erratum["excluded_from_immutable_scientific_authority_hashing"] == [LIVING_DOCUMENTATION_PATH]
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    protected = {reference["path"] for reference in protocol["authorities"]} - {LIVING_DOCUMENTATION_PATH}
    assert "configs/preprocessing/fd002-preprocessing-selection-v1.json" in protected
    assert "docs/research/MASTER_EXECUTION_BIBLE_V3_RESEARCH_IMPLEMENTATION_2026-08-23.md" in protected


@pytest.mark.parametrize("mutation", ["extra_path", "wrong_protocol_hash"])
def test_erratum_rejects_expanded_scope_and_wrong_protocol_hash(mutation):
    erratum = copy.deepcopy(_erratum())
    if mutation == "extra_path":
        erratum["excluded_from_immutable_scientific_authority_hashing"].append("models/alerting_v1/fd002-alert-policy-study-v1/pca_reconstruction.joblib")
    else:
        erratum["original_protocol"]["sha256"] = "0" * 64
    with pytest.raises(RuntimeError):
        validate_phase5_protected_authority_erratum(erratum)


def test_original_protocol_is_not_modified_by_erratum():
    erratum = _erratum()
    assert erratum["original_protocol"]["path"] == "configs/alerting/fd002-alert-policy-study-protocol-v2.json"
    assert PROTOCOL.read_bytes() == (ROOT / erratum["original_protocol"]["path"]).read_bytes()


def test_modified_scientific_artifact_still_fails_hash_verification(tmp_path):
    protected = tmp_path / "configs" / "protected-scientific-authority.json"
    protected.parent.mkdir(parents=True)
    protected.write_bytes(b'{"frozen":true}\n')
    reference = {
        "path": "configs/protected-scientific-authority.json",
        "sha256": "ff9f1f7bf5c634879f9ff3c4bd3bf42d40973c7846eb8734d5ae6ad47c744497",
        "hash_form": "raw",
    }
    protected.write_bytes(b'{"frozen":false}\n')
    with pytest.raises(ValueError):
        _verify_reference(reference, tmp_path)
