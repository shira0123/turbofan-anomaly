"""Independently verify recovered P1/K=6 provenance without test access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from turbofan_anomaly.data.preprocessing import load_preprocessor
from turbofan_anomaly.evaluation.provenance import (
    find_repository_root,
    resolve_repo_path,
    sha256_file,
)
from turbofan_anomaly.workflows.recover_p1_preprocessor import (
    DEFAULT_PROTOCOL,
    load_recovery_protocol,
    preprocessor_state_fingerprints,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--result",
        type=Path,
        default=Path(
            "reports/preprocessing_recovery/"
            "fd002-p1-k6-recovery-v1/result.json"
        ),
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_recovery_result(
    protocol: dict[str, Any], result: dict[str, Any], repo_root: Path
) -> dict[str, Any]:
    _require(result.get("protocol_id") == protocol["protocol_id"], "Protocol linkage changed")
    _require(
        result.get("status") == "verified_recovery_complete_before_test_access",
        "Recovery result is not verified",
    )
    _require(
        result.get("selected_recovery_route")
        in {"route_a_byte_exact", "route_b_governed_semantic_reconstruction"},
        "Unknown recovery route",
    )
    access = result.get("access_audit", {})
    _require(access == {**access, **protocol["access_boundary"]}, "Access boundary drifted")
    for field in (
        "internal_held_out_split_artifact_opened",
        "official_nasa_test_artifact_opened",
        "held_out_rows_retained",
        "held_out_rows_summarized",
        "held_out_rows_exported",
        "held_out_rows_used_for_fit_selection_or_evaluation",
        "confirmatory_evaluation_executed",
    ):
        _require(access.get(field) is False, f"Forbidden access recorded: {field}")

    artifact_record = result["preprocessor"]
    artifact_path = resolve_repo_path(artifact_record["path"], repo_root)
    _require(artifact_path.is_file(), "Recovered preprocessor is missing")
    _require(sha256_file(artifact_path) == artifact_record["sha256"], "Recovered preprocessor hash mismatch")
    _require(artifact_path.stat().st_size == artifact_record["size_bytes"], "Recovered preprocessor size mismatch")
    preprocessor, metadata = load_preprocessor(
        artifact_path,
        expected_split_manifest_id=protocol["frozen_partition"]["manifest_id"],
    )
    normalized_metadata = json.loads(json.dumps(metadata))
    _require(normalized_metadata == artifact_record["metadata"], "Serialized metadata changed")
    _require(
        preprocessor_state_fingerprints(preprocessor)
        == artifact_record["state_fingerprints"],
        "Serialized preprocessor state fingerprint changed",
    )
    lineage = result["source_lineage"]
    source = resolve_repo_path(
        protocol["source_lineage_correction"]["authorized_local_source"]["path"],
        repo_root,
    )
    manifest = resolve_repo_path(protocol["frozen_partition"]["manifest_path"], repo_root)
    validation = resolve_repo_path(protocol["registered_validation_split"]["canonical_path"], repo_root)
    _require(sha256_file(source) == lineage["authorized_local_source_sha256"], "Source hash changed")
    _require(sha256_file(manifest) == lineage["split_manifest_sha256"], "Manifest hash changed")
    _require(sha256_file(validation) == lineage["validation_csv_sha256"], "Validation split hash changed")
    reproduction = result.get("reproduction", {})
    _require(reproduction.get("endpoint_context_exact") == {"train": True, "validation": True}, "Endpoint context not exact")
    _require(reproduction.get("training_sequences", {}).get("maximum_absolute_difference", 1.0) <= protocol["reproduction_tolerances"]["float32_sequences"]["atol"], "Training sequence mismatch")
    _require(reproduction.get("validation_sequences", {}).get("maximum_absolute_difference", 1.0) <= protocol["reproduction_tolerances"]["float32_sequences"]["atol"], "Validation sequence mismatch")
    pca = reproduction.get("pca", {})
    _require(pca.get("bundle_sha256") == protocol["registered_reproduction_targets"]["frozen_pca_bundle"]["sha256"], "PCA bundle changed")
    _require(pca.get("maximum_ranking_metric_difference", 1.0) <= protocol["reproduction_tolerances"]["pca_scores"]["atol"], "PCA metrics changed")
    phase5 = reproduction.get("phase5_alert_policy", {})
    _require(phase5.get("candidate_id") == protocol["frozen_gate_4_candidate"], "Phase 5 policy changed")
    _require(phase5.get("thresholds_exact") is True, "Frozen thresholds changed")
    _require(phase5.get("maximum_alert_metric_difference", 1.0) <= protocol["reproduction_tolerances"]["pca_scores"]["atol"], "Phase 5 alert metrics changed")
    _require(phase5.get("threshold_refitted_or_selected") is False, "Phase 5 threshold was refitted")
    _require(reproduction.get("frozen_gate_4_candidate") == protocol["frozen_gate_4_candidate"], "Gate 4 policy changed")
    _require(reproduction.get("threshold_refitted_or_selected") is False, "Threshold was refitted")
    return {
        "schema_version": "1.0.0",
        "protocol_id": protocol["protocol_id"],
        "status": "verified_before_test_access",
        "recovered_preprocessor_sha256": artifact_record["sha256"],
        "state_fingerprints_verified": True,
        "source_lineage_verified": True,
        "downstream_reproduction_verified": True,
        "held_out_inputs_checked": 0,
        "held_out_inputs_opened": False,
        "official_nasa_test_opened": False,
        "confirmatory_evaluation_executed": False,
    }


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> None:
    args = parse_args()
    repo_root = find_repository_root(Path.cwd())
    protocol = load_recovery_protocol(resolve_repo_path(args.protocol, repo_root))
    result = json.loads(resolve_repo_path(args.result, repo_root).read_text(encoding="utf-8"))
    report = verify_recovery_result(protocol, result, repo_root)
    if args.output is not None:
        _write_json(report, resolve_repo_path(args.output, repo_root))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
