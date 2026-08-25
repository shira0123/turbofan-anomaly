"""Verify final-refit artifacts and reproduce validation-only LSTM scores."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import pandas as pd
import torch

from turbofan_anomaly.evaluation.ledger import load_run_ledger
from turbofan_anomaly.evaluation.provenance import (
    find_repository_root,
    resolve_repo_path,
    verify_registered_hash,
)
from turbofan_anomaly.models.lstm_training import (
    aligned_calibrated_score_ensemble,
    final_refit_artifact_name,
    load_lstm_artifact,
    reconstruction_errors,
    validate_sequence_collection,
)
from turbofan_anomaly.workflows.run_lstm_final_refit import (
    REGISTERED_SEEDS,
    expected_final_refit_ledger_run_ids,
    validate_allowed_input_path,
    validate_final_refit_protocol,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("configs/lstm/fd002-lstm-final-refit-results-v1.json"),
    )
    parser.add_argument(
        "--device", choices=["auto", "cpu", "cuda"], default="auto"
    )
    parser.add_argument("--batch-size", type=int, default=128)
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def _device(choice: str) -> torch.device:
    if choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable")
        return torch.device("cuda")
    if choice == "cpu":
        return torch.device("cpu")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main() -> None:
    args = parse_args()
    results_path = args.results.resolve()
    repo_root = find_repository_root(results_path.parent)
    results = _load_json(results_path)
    if results.get("status") != "completed":
        raise RuntimeError("Final-refit result does not claim completed status")
    if results.get("test_data_opened") or results.get("threshold_selected"):
        raise RuntimeError("Final-refit result violates its research boundary")

    protocol_path = resolve_repo_path(results["protocol_path"], repo_root)
    protocol_check = verify_registered_hash(
        protocol_path, results["protocol_sha256"]
    )
    if protocol_check.match_form != "raw":
        raise RuntimeError("Final-refit protocol raw hash does not match")
    protocol = _load_json(protocol_path)
    validate_final_refit_protocol(protocol)

    outputs = results["outputs"]
    report_dir = resolve_repo_path(outputs["report_directory"], repo_root)
    model_dir = resolve_repo_path(outputs["model_directory"], repo_root)
    for name, expected in outputs["report_sha256"].items():
        if verify_registered_hash(report_dir / name, expected).match_form != "raw":
            raise RuntimeError(f"Report hash is not an exact-byte match: {name}")
    for seed in REGISTERED_SEEDS:
        if verify_registered_hash(
            model_dir / final_refit_artifact_name(seed),
            outputs["model_sha256"][str(seed)],
        ).match_form != "raw":
            raise RuntimeError(f"Model hash is not an exact-byte match: seed {seed}")

    runtime = _load_json(report_dir / "runtime_provenance.json")
    missing_runtime_fields = set(protocol["runtime_provenance_required"]) - set(
        runtime
    )
    if missing_runtime_fields:
        raise RuntimeError(
            f"Runtime provenance is incomplete: {sorted(missing_runtime_fields)}"
        )
    expected_non_runtime_reports = {
        name: digest
        for name, digest in outputs["report_sha256"].items()
        if name != "runtime_provenance.json"
    }
    if runtime["output_sha256"] != {
        "model_artifacts": outputs["model_sha256"],
        "reports_excluding_runtime_provenance": expected_non_runtime_reports,
    }:
        raise RuntimeError("Runtime output hashes differ from the completed result")

    validation_reference = protocol["inputs"]["sequences"]["validation"]
    validate_allowed_input_path(validation_reference["path"], "validation")
    validation_path = resolve_repo_path(validation_reference["path"], repo_root)
    validation_check = verify_registered_hash(
        validation_path, validation_reference["sha256"]
    )
    if validation_check.match_form != validation_reference["hash_form"]:
        raise RuntimeError("Validation sequence hash form differs from registration")
    validation_sequences = np.load(
        validation_path, allow_pickle=False, mmap_mode="r"
    )
    validate_sequence_collection(
        validation_sequences,
        expected_window_shape=(30, 21),
        expected_count=9365,
        name="P1 validation sequences",
    )

    metadata_reference = protocol["inputs"]["metadata"]["validation"]
    validate_allowed_input_path(metadata_reference["path"], "validation")
    metadata_path = resolve_repo_path(metadata_reference["path"], repo_root)
    metadata_check = verify_registered_hash(
        metadata_path, metadata_reference["sha256"]
    )
    if metadata_check.match_form != metadata_reference["hash_form"]:
        raise RuntimeError("Validation metadata hash form differs from registration")
    validation_metadata = pd.read_csv(metadata_path)
    if len(validation_metadata) != len(validation_sequences):
        raise RuntimeError("Validation sequence/metadata lengths differ")
    if set(validation_metadata["split"].astype(str)) != {"validation"}:
        raise RuntimeError("Verifier may use only validation metadata")

    recorded_scores = pd.read_csv(report_dir / "validation_scores.csv")
    device = _device(args.device)
    observed_frames: dict[int, pd.DataFrame] = {}
    maximum_raw_difference = 0.0
    maximum_calibrated_difference = 0.0
    tolerances = protocol["reload_verification"]
    for seed in REGISTERED_SEEDS:
        artifact = model_dir / final_refit_artifact_name(seed)
        model, reference, metadata = load_lstm_artifact(
            artifact,
            expected_split_manifest_id="fd002-primary-v1",
            expected_preprocessing_decision_id="fd002-preprocessing-selection-v1",
        )
        if int(metadata["seed"]) != seed or metadata.get("test_data_opened"):
            raise RuntimeError(f"Artifact metadata boundary mismatch for seed {seed}")
        runtime_identity = metadata.get("runtime_identity", {})
        required_artifact_provenance = {
            "python_version",
            "numpy_version",
            "pandas_version",
            "scikit_learn_version",
            "torch_version",
            "operating_system",
            "device",
            "start_timestamp",
            "code_commit",
            "code_branch",
            "working_tree_clean",
            "deterministic_flags",
        }
        if required_artifact_provenance - set(runtime_identity):
            raise RuntimeError(f"Artifact provenance is incomplete for seed {seed}")
        if runtime_identity["code_commit"] != results["code_commit"]:
            raise RuntimeError(f"Artifact code identity differs for seed {seed}")
        model = model.to(device)
        raw = reconstruction_errors(
            model,
            validation_sequences,
            batch_size=args.batch_size,
            device=device,
        )
        calibrated = np.searchsorted(reference, raw, side="right").astype(float) / len(
            reference
        )
        recorded = recorded_scores[recorded_scores["seed"] == seed]
        if len(recorded) != 9365:
            raise RuntimeError(f"Recorded validation score count mismatch for seed {seed}")
        expected_ids = validation_metadata["window_id"].to_numpy()
        if not np.array_equal(recorded["window_id"].to_numpy(), expected_ids):
            raise RuntimeError(f"Recorded window-ID order mismatch for seed {seed}")
        recorded_raw = recorded["raw_reconstruction_error"].to_numpy(dtype=float)
        recorded_calibrated = recorded["calibrated_score"].to_numpy(dtype=float)
        if not np.allclose(
            raw,
            recorded_raw,
            rtol=tolerances["raw_scores"]["relative_tolerance"],
            atol=tolerances["raw_scores"]["absolute_tolerance"],
        ):
            raise RuntimeError(f"Raw validation scores do not reproduce for seed {seed}")
        if not np.allclose(
            calibrated,
            recorded_calibrated,
            rtol=tolerances["calibrated_scores"]["relative_tolerance"],
            atol=tolerances["calibrated_scores"]["absolute_tolerance"],
        ):
            raise RuntimeError(
                f"Calibrated validation scores do not reproduce for seed {seed}"
            )
        maximum_raw_difference = max(
            maximum_raw_difference, float(np.max(np.abs(raw - recorded_raw)))
        )
        maximum_calibrated_difference = max(
            maximum_calibrated_difference,
            float(np.max(np.abs(calibrated - recorded_calibrated))),
        )
        observed_frames[seed] = pd.DataFrame(
            {"window_id": expected_ids, "calibrated_score": calibrated}
        )

    observed_ensemble = aligned_calibrated_score_ensemble(observed_frames)
    recorded_ensemble = pd.read_csv(report_dir / "ensemble_validation_scores.csv")
    observed_by_id = observed_ensemble.set_index("window_id")
    recorded_by_id = recorded_ensemble.set_index("window_id")
    if set(observed_by_id.index) != set(recorded_by_id.index):
        raise RuntimeError("Recorded ensemble window IDs differ from reproduced IDs")
    reproduced = observed_by_id.loc[
        recorded_by_id.index, "ensemble_calibrated_score"
    ].to_numpy(dtype=float)
    if not np.allclose(
        reproduced,
        recorded_by_id["ensemble_calibrated_score"].to_numpy(dtype=float),
        rtol=0.0,
        atol=tolerances["calibrated_scores"]["absolute_tolerance"],
    ):
        raise RuntimeError("Recorded calibrated ensemble does not reproduce")

    ledger = load_run_ledger(repo_root / "experiments/runs_v2.jsonl")
    expected_run_ids = set(expected_final_refit_ledger_run_ids(results["study_id"]))
    final_rows = [record for record in ledger if record["run_id"] in expected_run_ids]
    if {record["run_id"] for record in final_rows} != expected_run_ids:
        raise RuntimeError("Final-refit ledger run IDs are incomplete")
    if len(final_rows) != int(outputs["ledger_records_appended"]):
        raise RuntimeError("Final-refit ledger record count mismatch")
    print(
        json.dumps(
            {
                "verified_artifacts": 3,
                "verified_validation_rows_per_seed": 9365,
                "verified_ensemble_rows": 9365,
                "maximum_raw_absolute_difference": maximum_raw_difference,
                "maximum_calibrated_absolute_difference": (
                    maximum_calibrated_difference
                ),
                "ledger_records": len(final_rows),
                "test_data_opened_by_verification": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
