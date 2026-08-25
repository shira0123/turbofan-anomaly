"""Independently verify the completed FD002 Phase 5 validation study."""

from __future__ import annotations

import argparse
from io import StringIO
import json
import os
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import pandas as pd
import torch
from pandas.testing import assert_frame_equal

from turbofan_anomaly.data.windows import summary_features
from turbofan_anomaly.evaluation.ledger import load_run_ledger
from turbofan_anomaly.evaluation.provenance import (
    find_repository_root,
    resolve_repo_path,
    verify_registered_hash,
)
from turbofan_anomaly.evaluation.proxies import training_eligible_windows
from turbofan_anomaly.models.classical import load_baseline_artifact
from turbofan_anomaly.models.lstm_training import (
    aligned_calibrated_score_ensemble,
    load_lstm_artifact,
    reconstruction_errors,
)
from turbofan_anomaly.workflows.run_alert_policy_study import (
    ALLOWED_SPLITS,
    REGISTERED_SEEDS,
    SCORE_SOURCE_ORDER,
    _load_json,
    _score_frame,
    build_alert_study_tables,
    expected_alert_policy_ledger_run_ids,
    load_allowed_inputs,
    score_frame_sha256,
    validate_alert_policy_protocol,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("configs/alerting/fd002-alert-policy-study-results-v1.json"),
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--batch-size", type=int, default=128)
    return parser.parse_args()


def _device(choice: str) -> torch.device:
    if choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable")
        return torch.device("cuda")
    if choice == "cpu":
        return torch.device("cpu")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _compare_report_frame(observed: pd.DataFrame, expected_path: Path) -> None:
    expected = pd.read_csv(expected_path)
    observed_round_trip = pd.read_csv(
        StringIO(observed.to_csv(index=False, lineterminator="\n"))
    )
    assert_frame_equal(
        observed_round_trip.reset_index(drop=True),
        expected.reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        rtol=1e-10,
        atol=1e-12,
    )


def _load_saved_score_frames(
    *,
    protocol: dict,
    results: dict,
    repo_root: Path,
    train_sequences: np.ndarray,
    validation_sequences: np.ndarray,
    train_metadata: pd.DataFrame,
    validation_metadata: pd.DataFrame,
    device: torch.device,
    batch_size: int,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    eligible = training_eligible_windows(train_metadata, 0.30).to_numpy(dtype=bool)
    if int(eligible.sum()) != 5037:
        raise RuntimeError("Verifier expected exactly 5,037 eligible training windows")
    eligible_metadata = train_metadata.loc[eligible].reset_index(drop=True)
    train_features = summary_features(train_sequences[eligible])
    validation_features = summary_features(validation_sequences)
    model_directory = resolve_repo_path(results["outputs"]["model_directory"], repo_root)
    training_frames: dict[str, pd.DataFrame] = {}
    validation_frames: dict[str, pd.DataFrame] = {}

    for detector_id in SCORE_SOURCE_ORDER[:4]:
        artifact_path = model_directory / f"{detector_id}.joblib"
        model, metadata = load_baseline_artifact(
            artifact_path,
            expected_split_manifest_id=protocol["inputs"]["split_manifest_id"],
            expected_preprocessing_decision_id=protocol["inputs"][
                "preprocessing_decision_id"
            ],
        )
        if metadata.get("test_data_opened") or metadata.get("artifact_role") != (
            "phase5_reproduction_not_retuning"
        ):
            raise RuntimeError(f"Phase 5 bundle boundary differs for {detector_id}")
        training_raw, training_calibrated = model.score(train_features)
        validation_raw, validation_calibrated = model.score(validation_features)
        training_frames[detector_id] = _score_frame(
            eligible_metadata,
            detector_id=detector_id,
            split="train",
            alert_score=training_calibrated,
            raw_score=training_raw,
        )
        validation_frames[detector_id] = _score_frame(
            validation_metadata,
            detector_id=detector_id,
            split="validation",
            alert_score=validation_calibrated,
            raw_score=validation_raw,
        )

    training_seed_frames: dict[int, pd.DataFrame] = {}
    validation_seed_frames: dict[int, pd.DataFrame] = {}
    for seed in REGISTERED_SEEDS:
        reference = protocol["inputs"]["final_lstm_models"][str(seed)]
        artifact_path = resolve_repo_path(reference["path"], repo_root)
        model, calibration_reference, metadata = load_lstm_artifact(
            artifact_path,
            expected_split_manifest_id=protocol["inputs"]["split_manifest_id"],
            expected_preprocessing_decision_id=protocol["inputs"][
                "preprocessing_decision_id"
            ],
        )
        if int(metadata["seed"]) != seed or metadata.get("test_data_opened"):
            raise RuntimeError(f"Final LSTM artifact boundary differs for seed {seed}")
        model = model.to(device)
        training_raw = reconstruction_errors(
            model, train_sequences[eligible], batch_size=batch_size, device=device
        )
        validation_raw = reconstruction_errors(
            model, validation_sequences, batch_size=batch_size, device=device
        )
        training_calibrated = np.searchsorted(
            calibration_reference, training_raw, side="right"
        ).astype(float) / len(calibration_reference)
        validation_calibrated = np.searchsorted(
            calibration_reference, validation_raw, side="right"
        ).astype(float) / len(calibration_reference)
        training_seed_frames[seed] = pd.DataFrame(
            {
                "window_id": eligible_metadata["window_id"].to_numpy(),
                "calibrated_score": training_calibrated,
            }
        )
        validation_seed_frames[seed] = pd.DataFrame(
            {
                "window_id": validation_metadata["window_id"].to_numpy(),
                "calibrated_score": validation_calibrated,
            }
        )
    training_ensemble = aligned_calibrated_score_ensemble(training_seed_frames)
    validation_ensemble = aligned_calibrated_score_ensemble(validation_seed_frames)
    training_values = training_ensemble.set_index("window_id").loc[
        eligible_metadata["window_id"], "ensemble_calibrated_score"
    ].to_numpy(dtype=float)
    validation_values = validation_ensemble.set_index("window_id").loc[
        validation_metadata["window_id"], "ensemble_calibrated_score"
    ].to_numpy(dtype=float)
    training_frames["lstm_calibrated_ensemble"] = _score_frame(
        eligible_metadata,
        detector_id="lstm_calibrated_ensemble",
        split="train",
        alert_score=training_values,
        raw_score=None,
    )
    validation_frames["lstm_calibrated_ensemble"] = _score_frame(
        validation_metadata,
        detector_id="lstm_calibrated_ensemble",
        split="validation",
        alert_score=validation_values,
        raw_score=None,
    )
    return training_frames, validation_frames


def main() -> None:
    args = parse_args()
    results_path = args.results.resolve()
    repo_root = find_repository_root(results_path.parent)
    results = _load_json(results_path)
    if results.get("status") != "completed":
        raise RuntimeError("Phase 5 result does not claim completed status")
    forbidden_true = (
        results.get("test_data_opened"),
        results.get("online_recalibration"),
        results.get("fusion_evaluated"),
        results.get("final_result"),
    )
    if any(bool(value) for value in forbidden_true):
        raise RuntimeError("Phase 5 result violates its registered evidence boundary")
    if results.get("gate_4_status") != "recommended_pending_owner_approval":
        raise RuntimeError("Gate 4 is not pending owner approval")

    protocol_path = resolve_repo_path(results["protocol_path"], repo_root)
    protocol_check = verify_registered_hash(protocol_path, results["protocol_sha256"])
    if protocol_check.match_form != "raw":
        raise RuntimeError("Phase 5 protocol raw hash differs")
    protocol = _load_json(protocol_path)
    validate_alert_policy_protocol(protocol)

    output = results["outputs"]
    report_directory = resolve_repo_path(output["report_directory"], repo_root)
    model_directory = resolve_repo_path(output["model_directory"], repo_root)
    for name, expected in output["report_sha256"].items():
        if verify_registered_hash(report_directory / name, expected).match_form != "raw":
            raise RuntimeError(f"Phase 5 report is not an exact-byte match: {name}")
    for detector_id, expected in output["model_bundle_sha256"].items():
        filename = (
            "lstm_calibrated_ensemble.json"
            if detector_id == "lstm_calibrated_ensemble"
            else f"{detector_id}.joblib"
        )
        if verify_registered_hash(model_directory / filename, expected).match_form != "raw":
            raise RuntimeError(f"Phase 5 model bundle hash differs: {detector_id}")

    runtime = _load_json(report_directory / "runtime_provenance.json")
    missing_runtime = set(protocol["runtime_provenance_required"]) - set(runtime)
    if missing_runtime:
        raise RuntimeError(f"Runtime provenance is incomplete: {sorted(missing_runtime)}")
    if runtime["test_data_opened"] or runtime["online_recalibration"] or runtime["fusion_evaluated"]:
        raise RuntimeError("Runtime provenance violates the Phase 5 boundary")

    manifest = pd.read_csv(report_directory / "artifact_manifest.csv")
    if len(manifest[manifest["artifact_type"] == "model_bundle"]) != 5:
        raise RuntimeError("Artifact manifest does not contain five model bundles")
    for row in manifest.to_dict(orient="records"):
        path = resolve_repo_path(row["path"], repo_root)
        if verify_registered_hash(path, row["sha256"]).match_form != "raw":
            raise RuntimeError(f"Artifact manifest hash differs: {row['path']}")

    train_sequences, validation_sequences, train_metadata, validation_metadata = (
        load_allowed_inputs(
            protocol,
            repo_root,
            verify_lifecycle_authorities=False,
        )
    )
    device = _device(args.device)
    training_frames, validation_frames = _load_saved_score_frames(
        protocol=protocol,
        results=results,
        repo_root=repo_root,
        train_sequences=train_sequences,
        validation_sequences=validation_sequences,
        train_metadata=train_metadata,
        validation_metadata=validation_metadata,
        device=device,
        batch_size=args.batch_size,
    )
    reproduction = pd.read_csv(
        report_directory / "validation_score_reproduction_summary.csv"
    ).set_index("detector_id")
    for detector_id in SCORE_SOURCE_ORDER:
        if score_frame_sha256(training_frames[detector_id]) != reproduction.loc[
            detector_id, "training_score_frame_sha256"
        ]:
            raise RuntimeError(f"Training score-frame hash differs: {detector_id}")
        if score_frame_sha256(validation_frames[detector_id]) != reproduction.loc[
            detector_id, "validation_score_frame_sha256"
        ]:
            raise RuntimeError(f"Validation score-frame hash differs: {detector_id}")

    tables = build_alert_study_tables(
        protocol=protocol,
        training_frames=training_frames,
        validation_frames=validation_frames,
        validation_metadata=validation_metadata,
    )
    for name, frame in tables.items():
        _compare_report_frame(frame, report_directory / f"{name}.csv")
    if len(tables["candidates"]) != 1280 or len(tables["candidate_policy_metrics"]) != 6400:
        raise RuntimeError("Independent verifier candidate counts differ")
    overall = tables["overall_recommendation"]
    expected_overall = results["overall_recommendation"]
    if overall.empty != (expected_overall is None):
        raise RuntimeError("Independent overall recommendation status differs")
    if not overall.empty and overall.iloc[0]["candidate_id"] != expected_overall["candidate_id"]:
        raise RuntimeError("Independent overall candidate ID differs")

    ledger = load_run_ledger(repo_root / "experiments/runs_v2.jsonl")
    expected_ids = set(expected_alert_policy_ledger_run_ids(results["study_id"]))
    phase5_records = [record for record in ledger if record["run_id"] in expected_ids]
    if {record["run_id"] for record in phase5_records} != expected_ids:
        raise RuntimeError("Phase 5 ledger run IDs are incomplete")
    if len(phase5_records) != int(output["ledger_records_appended"]):
        raise RuntimeError("Phase 5 ledger record count differs")
    if any(record["evidence_boundary"]["final_result"] for record in phase5_records):
        raise RuntimeError("A Phase 5 ledger row claims a final result")
    if any(
        record["evidence_boundary"]["held_out_internal_test_accessed"]
        for record in phase5_records
    ):
        raise RuntimeError("A Phase 5 ledger row claims test-data access")
    print(
        json.dumps(
            {
                "verified_score_sources": 5,
                "verified_training_rows_per_source": 5037,
                "verified_validation_rows_per_source": 9365,
                "verified_threshold_rows": len(tables["threshold_table"]),
                "verified_candidates": len(tables["candidates"]),
                "verified_candidate_policy_rows": len(tables["candidate_policy_metrics"]),
                "verified_ledger_records": len(phase5_records),
                "overall_candidate_id": (
                    None if overall.empty else str(overall.iloc[0]["candidate_id"])
                ),
                "gate_4_status": "recommended_pending_owner_approval",
                "test_data_opened_by_verification": False,
                "online_recalibration": False,
                "fusion_evaluated": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
