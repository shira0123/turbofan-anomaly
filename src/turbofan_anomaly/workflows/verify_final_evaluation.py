"""Independently verify the frozen final-evaluation protocol and readiness.

The default readiness audit never resolves or opens held-out or official-test
inputs.  It verifies only registered authorities and training-fitted artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from turbofan_anomaly.evaluation.provenance import find_repository_root


DEFAULT_PROTOCOL = Path(
    "configs/evaluation/fd002-final-evaluation-protocol-v1.json"
)
EXPECTED_PRIMARY_CANDIDATE = (
    "pca_reconstruction__per_mode__quantile_0.995__"
    "ewma_alpha_0.20__persistence_8"
)
EXPECTED_PROTOCOL_SHA256 = (
    "ed5d3ca6a847365256a238684086266fae8bab72a79ff6b4f9d8af3fa6a84133"
)
EXPECTED_PRIMARY_THRESHOLDS = (
    (0, 0.9974190986698431, 756),
    (1, 0.9908675799086758, 768),
    (2, 0.9948381973396864, 719),
    (3, 0.9922572960095295, 765),
    (4, 0.996624975183641, 747),
    (5, 0.9932499503672821, 1282),
)
EXPECTED_PROXY_POLICIES = (
    "normalized_life_last_10pct_endpoint",
    "normalized_life_last_20pct_endpoint",
    "normalized_life_last_30pct_endpoint",
    "normalized_life_last_20pct_full_window",
    "normalized_life_last_30pct_full_window",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--result",
        type=Path,
        help="Optional future result manifest; never causes test-input access.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON readiness/verification report destination.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Return a failure when any pre-test artifact is not ready.",
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_path(repo_root: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"Repository-relative path required: {value}")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as error:
        raise RuntimeError(f"Path escapes repository: {value}") from error
    return resolved


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_final_evaluation_protocol(protocol: dict[str, Any]) -> None:
    """Reject any drift from the owner-approved Gate 4 freeze."""
    _require(protocol.get("schema_version") == "1.0.0", "Protocol schema changed")
    _require(
        protocol.get("protocol_id") == "fd002-final-evaluation-protocol-v1",
        "Final-evaluation protocol identity changed",
    )
    approval = protocol.get("gate_4_approval", {})
    _require(approval.get("status") == "approved", "Gate 4 is not approved")
    _require(
        approval.get("approved_candidate_id") == EXPECTED_PRIMARY_CANDIDATE,
        "Gate 4 selected candidate changed",
    )
    _require(
        approval.get("evidence_basis") == "validation_proxy_only",
        "Gate 4 evidence boundary changed",
    )
    _require(
        approval.get("endpoint_false_positive_target_achieved_on_validation_proxies")
        is True,
        "Validation-proxy endpoint FAR acknowledgement changed",
    )
    _require(
        approval.get("aggregate_detection_delay_aspiration_achieved") is False
        and approval.get("validation_aggregate_median_delay_cycles") == 23,
        "Detection-delay limitation changed",
    )
    _require(
        approval.get("not_final_test_performance") is True,
        "Validation evidence was upgraded to final performance",
    )

    boundary = protocol.get("access_boundary", {})
    for field in (
        "held_out_internal_test_access_authorized",
        "official_nasa_test_access_authorized",
        "test_data_opened_during_registration",
        "test_data_preprocessed_during_registration",
        "test_data_scored_during_registration",
        "test_data_summarized_during_registration",
        "threshold_refit_allowed",
        "model_refit_allowed",
        "calibration_refit_allowed",
        "online_recalibration_allowed",
        "score_or_decision_fusion_allowed",
        "candidate_search_allowed",
        "policy_change_allowed",
    ):
        _require(boundary.get(field) is False, f"Forbidden boundary changed: {field}")
    _require(
        boundary.get("official_nasa_test_is_out_of_scope") is True,
        "Official NASA test boundary changed",
    )

    lineage = protocol.get("preprocessing_lineage", {})
    _require(lineage.get("pipeline_id") == "p1_k6", "Pipeline changed")
    _require(lineage.get("n_clusters") == 6, "Operating-mode count changed")
    _require(lineage.get("random_state") == 42, "Preprocessing seed changed")
    _require(lineage.get("n_init") == 20, "KMeans n_init changed")
    _require(lineage.get("healthy_fraction") == 0.3, "Healthy fraction changed")
    _require(lineage.get("window_shape") == [30, 21], "Window shape changed")
    _require(lineage.get("window_stride") == 1, "Window stride changed")
    _require(lineage.get("summary_feature_count") == 63, "Feature count changed")
    _require(
        lineage.get("window_context_semantics")
        == "p1_k6_endpoint_cycle_mode_v1",
        "Endpoint-mode context semantics changed",
    )
    for field in (
        "reclustering_allowed",
        "sensor_mode_inference_allowed",
        "majority_vote_allowed",
    ):
        _require(lineage.get(field) is False, f"Forbidden lineage change: {field}")

    detector = protocol.get("frozen_primary_detector", {})
    _require(detector.get("detector_id") == "pca_reconstruction", "Detector changed")
    _require(
        detector.get("artifact", {}).get("sha256")
        == "d56a6d41e63c0781da763565f71c4a13b144eacd487a351428113c8ebf2ba9aa",
        "PCA artifact hash changed",
    )
    _require(detector.get("parameters", {}).get("n_components") == 0.9, "PCA changed")
    _require(detector.get("fit_window_count") == 5037, "PCA fit population changed")
    calibration = detector.get("calibration", {})
    _require(calibration.get("method") == "training_empirical_cdf", "Calibration changed")
    _require(calibration.get("reference_count") == 5037, "Calibration population changed")
    _require(
        calibration.get("sorted_reference_sha256_float64_le")
        == "b7daa56d0251263012f579d98bff9eb595141f915756087a0675d40b9f08efec",
        "Calibration reference hash changed",
    )
    _require(
        calibration.get("validation_or_test_statistics_allowed") is False
        and calibration.get("online_update_allowed") is False,
        "Calibration update boundary changed",
    )

    policy = protocol.get("frozen_primary_alert_policy", {})
    _require(policy.get("candidate_id") == EXPECTED_PRIMARY_CANDIDATE, "Policy changed")
    _require(policy.get("threshold_context") == "per_mode", "Threshold context changed")
    _require(policy.get("threshold_rule_id") == "quantile_0.995", "Threshold rule changed")
    _require(policy.get("quantile_method") == "higher", "Quantile method changed")
    _require(policy.get("comparison") == "strict_greater_than", "Comparison changed")
    _require(policy.get("ewma_alpha") == 0.2, "EWMA alpha changed")
    _require(policy.get("persistence") == 8, "Persistence changed")
    observed_thresholds = tuple(
        (row.get("operating_mode"), row.get("threshold"), row.get("reference_count"))
        for row in policy.get("thresholds", [])
    )
    _require(observed_thresholds == EXPECTED_PRIMARY_THRESHOLDS, "Frozen thresholds changed")
    state = policy.get("state_contract", {})
    expected_state = {
        "chronology": "stable_sort_by_engine_then_end_cycle",
        "ewma_initialization": "first_score",
        "reset_on_engine_boundary": True,
        "reset_on_nonconsecutive_end_cycle": True,
        "reset_on_mode_change": False,
        "persistence_counter": "consecutive_strict_threshold_violations",
        "alert_begins": "eighth_violating_window_without_backdating",
        "point_adjustment": False,
    }
    for field, value in expected_state.items():
        _require(state.get(field) == value, f"Alert state contract changed: {field}")

    comparator = protocol.get("frozen_deep_temporal_comparator", {})
    _require(
        comparator.get("detector_id") == "lstm_calibrated_ensemble"
        and comparator.get("role") == "comparator_not_primary",
        "LSTM comparator role changed",
    )
    _require(comparator.get("fusion_with_primary_allowed") is False, "Fusion enabled")
    _require(len(comparator.get("source_models", [])) == 3, "LSTM ensemble changed")

    proxy = protocol.get("proxy_and_metric_contract", {})
    _require(
        tuple(row.get("policy_id") for row in proxy.get("policies", []))
        == EXPECTED_PROXY_POLICIES,
        "Proxy policies changed",
    )
    _require(proxy.get("full_window_overlap") == "ambiguous_and_excluded", "Proxy exclusion changed")
    _require(proxy.get("crossing_event_detection") is False, "Crossing events enabled")
    _require(proxy.get("selection_after_test_allowed") is False, "Post-test selection enabled")

    authorities = protocol.get("frozen_authorities", [])
    authority_ids = [item.get("artifact_id") for item in authorities]
    _require(len(authority_ids) == len(set(authority_ids)), "Duplicate authority ID")
    _require(all(item.get("sha256") for item in authorities), "Authority lacks hash")

    required = protocol.get("required_artifacts_before_test_access", [])
    required_ids = [item.get("artifact_id") for item in required]
    _require(len(required_ids) == len(set(required_ids)), "Duplicate required artifact")
    preprocessor = next(
        (item for item in required if item.get("artifact_id") == "p1_k6_fitted_preprocessor"),
        None,
    )
    _require(preprocessor is not None, "Fitted P1/K=6 preprocessor requirement missing")
    _require(
        preprocessor.get("sha256") is None
        and preprocessor.get("readiness") == "missing_and_hash_not_registered",
        "Missing preprocessor readiness gap was concealed",
    )
    held_out = protocol.get("held_out_inputs_registered_but_not_accessed", [])
    _require(len(held_out) == 4, "Held-out input contract changed")
    _require(all(item.get("sha256") is None for item in held_out), "Held-out content was hashed")
    readiness = protocol.get("readiness_audit", {})
    _require(readiness.get("test_paths_resolved_or_opened") is False, "Test path access claimed")
    _require(readiness.get("ready_for_confirmatory_evaluation") is False, "Readiness gap hidden")
    _require(
        readiness.get("missing_frozen_artifacts") == ["p1_k6_fitted_preprocessor"],
        "Missing frozen artifact record changed",
    )


def audit_final_evaluation_readiness(
    protocol: dict[str, Any], repo_root: Path
) -> dict[str, Any]:
    """Verify pre-test artifacts without resolving any held-out input path."""
    validate_final_evaluation_protocol(protocol)
    authority_checks: list[dict[str, Any]] = []
    for artifact in protocol["frozen_authorities"]:
        path = _repo_path(repo_root, artifact["path"])
        _require(path.is_file(), f"Frozen authority missing: {artifact['artifact_id']}")
        observed = _sha256(path)
        _require(
            observed == artifact["sha256"],
            f"Frozen authority hash mismatch: {artifact['artifact_id']}",
        )
        authority_checks.append(
            {"artifact_id": artifact["artifact_id"], "status": "hash_verified"}
        )

    artifact_checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    for artifact in protocol["required_artifacts_before_test_access"]:
        _require(
            artifact.get("access_class") == "training_fitted_model",
            f"Readiness attempted a non-training artifact: {artifact.get('artifact_id')}",
        )
        expected = artifact.get("sha256")
        if not expected:
            status = "blocked_missing_registered_hash"
            blockers.append(str(artifact["artifact_id"]))
        else:
            path = _repo_path(repo_root, artifact["path"])
            if not path.is_file():
                status = "blocked_missing_file"
                blockers.append(str(artifact["artifact_id"]))
            elif _sha256(path) != expected:
                status = "blocked_hash_mismatch"
                blockers.append(str(artifact["artifact_id"]))
            else:
                status = "hash_verified"
        artifact_checks.append(
            {"artifact_id": artifact["artifact_id"], "status": status}
        )

    return {
        "schema_version": "1.0.0",
        "protocol_id": protocol["protocol_id"],
        "audit_date": protocol["readiness_audit"]["audit_date"],
        "verification_scope": "protocol_authorities_and_training_fitted_artifacts_only",
        "authority_checks": authority_checks,
        "artifact_checks": artifact_checks,
        "held_out_inputs_checked": 0,
        "held_out_inputs_opened": False,
        "official_nasa_test_checked": False,
        "official_nasa_test_opened": False,
        "blockers": blockers,
        "ready_for_confirmatory_evaluation": not blockers,
        "status": "ready" if not blockers else "blocked_before_test_access",
    }


def verify_final_evaluation_result_manifest(
    protocol: dict[str, Any], result: dict[str, Any], repo_root: Path
) -> dict[str, Any]:
    """Verify a future result manifest without opening its evaluation inputs."""
    validate_final_evaluation_protocol(protocol)
    _require(
        result.get("protocol_id") == protocol["protocol_id"],
        "Result references a different protocol",
    )
    _require(
        result.get("protocol_sha256") == EXPECTED_PROTOCOL_SHA256,
        "Result protocol hash changed",
    )
    _require(
        result.get("primary_candidate_id") == EXPECTED_PRIMARY_CANDIDATE,
        "Result primary policy changed",
    )
    for field in (
        "online_recalibration",
        "score_or_decision_fusion",
        "threshold_refit",
        "model_refit",
        "calibration_refit",
    ):
        _require(result.get(field) is False, f"Forbidden result behavior: {field}")
    _require(
        result.get("official_nasa_test_accessed") is False,
        "Official NASA test access claimed",
    )
    outputs = result.get("outputs", [])
    _require(outputs, "Result manifest has no outputs")
    checks: list[dict[str, str]] = []
    for artifact in outputs:
        path_text = str(artifact.get("path", ""))
        _require(
            path_text.startswith("reports/final_evaluation_v1/"),
            "Result output is outside the registered report directory",
        )
        path = _repo_path(repo_root, path_text)
        _require(path.is_file(), f"Result output missing: {path_text}")
        _require(_sha256(path) == artifact.get("sha256"), f"Result hash mismatch: {path_text}")
        checks.append({"path": path_text, "status": "hash_verified"})
    return {
        "result_manifest_verified": True,
        "output_checks": checks,
        "evaluation_inputs_opened_by_verifier": False,
        "scope": "frozen-contract_and_output-manifest_integrity",
    }


def _atomic_write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    args = parse_args()
    repo_root = find_repository_root(Path.cwd())
    protocol_path = _repo_path(repo_root, args.protocol.as_posix())
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    report = audit_final_evaluation_readiness(protocol, repo_root)
    report["protocol_path"] = args.protocol.as_posix()
    report["protocol_sha256"] = _sha256(protocol_path)
    if args.result is not None:
        result_path = _repo_path(repo_root, args.result.as_posix())
        result = json.loads(result_path.read_text(encoding="utf-8"))
        report["result_verification"] = verify_final_evaluation_result_manifest(
            protocol, result, repo_root
        )
    if args.output is not None:
        _atomic_write_json(report, _repo_path(repo_root, args.output.as_posix()))
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.require_ready and not report["ready_for_confirmatory_evaluation"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
