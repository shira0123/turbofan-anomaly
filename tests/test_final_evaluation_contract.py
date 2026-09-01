from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest

from turbofan_anomaly.workflows import verify_final_evaluation as verifier


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = (
    REPO_ROOT / "configs/evaluation/fd002-final-evaluation-protocol-v1.json"
)
PROTOCOL_V2_PATH = (
    REPO_ROOT / "configs/evaluation/fd002-final-evaluation-protocol-v2.json"
)


def _protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_audit_protocol(tmp_path: Path) -> dict:
    protocol = _protocol()
    authority = tmp_path / "authority.json"
    authority.write_text('{"synthetic": true}\n', encoding="utf-8")
    protocol["frozen_authorities"] = [
        {
            "artifact_id": "synthetic_authority",
            "path": "authority.json",
            "sha256": _sha256(authority),
            "hash_form": "raw",
        }
    ]
    for artifact in protocol["required_artifacts_before_test_access"]:
        if artifact["artifact_id"] == "p1_k6_fitted_preprocessor":
            artifact["path"] = "missing-preprocessor.joblib"
            continue
        path = tmp_path / f"{artifact['artifact_id']}.bin"
        path.write_bytes(f"synthetic:{artifact['artifact_id']}".encode())
        artifact["path"] = path.name
        artifact["sha256"] = _sha256(path)
    return protocol


def test_registered_protocol_validates() -> None:
    verifier.validate_final_evaluation_protocol(_protocol())


def test_v2_changes_only_recovered_preprocessing_provenance_and_readiness() -> None:
    registered = json.loads(PROTOCOL_V2_PATH.read_text(encoding="utf-8"))
    effective = verifier.materialize_final_evaluation_protocol(registered, REPO_ROOT)
    verifier.validate_final_evaluation_protocol(effective)
    base = _protocol()
    assert effective["frozen_primary_detector"] == base["frozen_primary_detector"]
    assert effective["frozen_primary_alert_policy"] == base["frozen_primary_alert_policy"]
    assert effective["frozen_deep_temporal_comparator"] == base[
        "frozen_deep_temporal_comparator"
    ]
    assert effective["proxy_and_metric_contract"] == base[
        "proxy_and_metric_contract"
    ]
    assert effective["required_artifacts_before_test_access"][0]["sha256"] == (
        "c4f626743a8f6710dbca0487c12455169b819f928d847c6033f2ef365aa4a10a"
    )
    report = verifier.audit_final_evaluation_readiness(effective, REPO_ROOT)
    assert report["pre_test_training_fitted_artifacts_ready"]
    assert report["ready_for_separately_authorized_held_out_provisioning"]
    assert not report["ready_for_confirmatory_evaluation"]
    assert report["held_out_inputs_checked"] == 0
    assert report["status"] == (
        "ready_except_for_separately_authorized_held_out_provisioning"
    )


def test_gate4_primary_policy_is_exactly_frozen() -> None:
    protocol = _protocol()
    assert protocol["gate_4_approval"]["approved_candidate_id"] == (
        verifier.EXPECTED_PRIMARY_CANDIDATE
    )
    rows = protocol["frozen_primary_alert_policy"]["thresholds"]
    assert tuple(
        (row["operating_mode"], row["threshold"], row["reference_count"])
        for row in rows
    ) == verifier.EXPECTED_PRIMARY_THRESHOLDS


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    [
        ("gate_4_approval", "approved_candidate_id", "different", "selected candidate"),
        ("access_boundary", "online_recalibration_allowed", True, "online_recalibration"),
        ("access_boundary", "score_or_decision_fusion_allowed", True, "score_or_decision_fusion"),
        ("access_boundary", "official_nasa_test_access_authorized", True, "official_nasa"),
        ("frozen_primary_alert_policy", "persistence", 5, "Persistence"),
        ("frozen_primary_alert_policy", "ewma_alpha", 0.5, "EWMA"),
    ],
)
def test_protocol_drift_is_rejected(
    section: str, field: str, value: object, message: str
) -> None:
    protocol = _protocol()
    protocol[section][field] = value
    with pytest.raises(RuntimeError, match=message):
        verifier.validate_final_evaluation_protocol(protocol)


def test_endpoint_context_and_preprocessing_lineage_are_frozen() -> None:
    lineage = _protocol()["preprocessing_lineage"]
    assert lineage["pipeline_id"] == "p1_k6"
    assert lineage["n_clusters"] == 6
    assert lineage["window_shape"] == [30, 21]
    assert lineage["window_context_semantics"] == "p1_k6_endpoint_cycle_mode_v1"
    assert lineage["window_context_assignment"] == (
        "window.op_mode = cycle_frame.op_mode[(engine, window.end_cycle)]"
    )
    assert not lineage["reclustering_allowed"]
    assert not lineage["sensor_mode_inference_allowed"]
    assert not lineage["majority_vote_allowed"]


def test_proxy_exclusions_and_metrics_are_frozen() -> None:
    contract = _protocol()["proxy_and_metric_contract"]
    assert tuple(row["policy_id"] for row in contract["policies"]) == (
        verifier.EXPECTED_PROXY_POLICIES
    )
    assert contract["full_window_overlap"] == "ambiguous_and_excluded"
    assert contract["valid_post_onset_detection"] == (
        "first_event_with_confirmed_start_at_or_after_onset_cycle"
    )
    assert not contract["crossing_event_detection"]
    assert contract["persistence_delay_included"]
    assert not contract["selection_after_test_allowed"]


def test_lstm_remains_unfused_nonprimary_comparator() -> None:
    comparator = _protocol()["frozen_deep_temporal_comparator"]
    assert comparator["role"] == "comparator_not_primary"
    assert comparator["detector_id"] == "lstm_calibrated_ensemble"
    assert len(comparator["source_models"]) == 3
    assert not comparator["fusion_with_primary_allowed"]


def test_readiness_audit_skips_all_held_out_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _synthetic_audit_protocol(tmp_path)
    original = verifier._repo_path

    def reject_test_paths(repo_root: Path, value: str) -> Path:
        if value in {
            item["canonical_path"]
            for item in protocol["held_out_inputs_registered_but_not_accessed"]
        }:
            raise AssertionError("held-out path was resolved")
        return original(repo_root, value)

    monkeypatch.setattr(verifier, "_repo_path", reject_test_paths)
    report = verifier.audit_final_evaluation_readiness(protocol, tmp_path)
    assert report["held_out_inputs_checked"] == 0
    assert not report["held_out_inputs_opened"]
    assert not report["official_nasa_test_checked"]
    assert not report["ready_for_confirmatory_evaluation"]
    assert report["blockers"] == ["p1_k6_fitted_preprocessor"]


def test_missing_or_unregistered_preprocessor_cannot_be_hidden() -> None:
    protocol = _protocol()
    preprocessor = protocol["required_artifacts_before_test_access"][0]
    preprocessor["sha256"] = "0" * 64
    preprocessor["readiness"] = "available_hash_verified"
    with pytest.raises(RuntimeError, match="readiness gap was concealed"):
        verifier.validate_final_evaluation_protocol(protocol)


def test_authority_hash_mismatch_is_substantive_failure(tmp_path: Path) -> None:
    protocol = _synthetic_audit_protocol(tmp_path)
    (tmp_path / "authority.json").write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Frozen authority hash mismatch"):
        verifier.audit_final_evaluation_readiness(protocol, tmp_path)


def test_future_result_manifest_rejects_policy_change(tmp_path: Path) -> None:
    result = {
        "protocol_id": "fd002-final-evaluation-protocol-v1",
        "protocol_sha256": verifier.EXPECTED_PROTOCOL_SHA256,
        "primary_candidate_id": "different",
        "online_recalibration": False,
        "score_or_decision_fusion": False,
        "threshold_refit": False,
        "model_refit": False,
        "calibration_refit": False,
        "official_nasa_test_accessed": False,
        "outputs": [],
    }
    with pytest.raises(RuntimeError, match="primary policy changed"):
        verifier.verify_final_evaluation_result_manifest(_protocol(), result, tmp_path)


def test_future_result_manifest_verifies_only_registered_outputs(tmp_path: Path) -> None:
    output = tmp_path / "reports/final_evaluation_v1/synthetic/metrics.csv"
    output.parent.mkdir(parents=True)
    output.write_text("metric,value\nsynthetic,1\n", encoding="utf-8")
    result = {
        "protocol_id": "fd002-final-evaluation-protocol-v1",
        "protocol_sha256": verifier.EXPECTED_PROTOCOL_SHA256,
        "primary_candidate_id": verifier.EXPECTED_PRIMARY_CANDIDATE,
        "online_recalibration": False,
        "score_or_decision_fusion": False,
        "threshold_refit": False,
        "model_refit": False,
        "calibration_refit": False,
        "official_nasa_test_accessed": False,
        "outputs": [
            {
                "path": "reports/final_evaluation_v1/synthetic/metrics.csv",
                "sha256": _sha256(output),
            }
        ],
    }
    report = verifier.verify_final_evaluation_result_manifest(
        _protocol(), result, tmp_path
    )
    assert report["result_manifest_verified"]
    assert not report["evaluation_inputs_opened_by_verifier"]


def test_readiness_json_writer_uses_deterministic_lf(tmp_path: Path) -> None:
    output = tmp_path / "readiness.json"
    verifier._atomic_write_json({"status": "synthetic", "ready": False}, output)
    data = output.read_bytes()
    assert data.endswith(b"\n")
    assert b"\r\n" not in data


def test_final_evaluation_script_and_console_help_do_not_access_data() -> None:
    subprocess.run(
        [sys.executable, "-m", "scripts.verify_final_evaluation", "--help"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        target = tomllib.load(handle)["project"]["scripts"][
            "turbofan-verify-final-evaluation"
        ]
    module, function = target.split(":", 1)
    subprocess.run(
        [sys.executable, "-c", f"from {module} import {function}; {function}()", "--help"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
