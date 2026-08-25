"""Verify LSTM screen hashes and reproduce every recorded validation score."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import pandas as pd
import torch

from turbofan_anomaly.evaluation.provenance import (
    find_repository_root,
    resolve_repo_path,
    verify_registered_hash,
)
from turbofan_anomaly.models.lstm_training import (
    load_lstm_artifact,
    reconstruction_errors,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("configs/lstm/fd002-lstm-screen-results-v1.json"),
    )
    parser.add_argument(
        "--device", choices=["auto", "cpu", "cuda"], default="auto"
    )
    parser.add_argument("--batch-size", type=int, default=128)
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    protocol_path = resolve_repo_path(results["protocol_path"], repo_root)
    protocol_check = verify_registered_hash(
        protocol_path, results["protocol_sha256"]
    )
    print(
        f"HASH_OK path={protocol_path} match_form={protocol_check.match_form}",
        flush=True,
    )
    if results["test_data_opened_by_study"]:
        raise RuntimeError("Results incorrectly declare held-out test access")

    outputs = results["outputs"]
    report_paths: dict[str, Path] = {}
    for name, path_value in outputs["reports"].items():
        report_path = resolve_repo_path(path_value, repo_root)
        report_paths[name] = report_path
        expected = outputs["report_sha256"][name]
        check = verify_registered_hash(report_path, expected)
        print(
            f"HASH_OK path={report_path} match_form={check.match_form}",
            flush=True,
        )
    models_dir = resolve_repo_path(outputs["models_dir"], repo_root)
    for run_id, expected in outputs["model_sha256"].items():
        path = models_dir / f"{run_id}.pt"
        check = verify_registered_hash(path, expected)
        print(f"HASH_OK path={path} match_form={check.match_form}", flush=True)

    protocol = _load_json(protocol_path)
    score_frame = pd.read_csv(report_paths["validation_scores"])
    sequences_dir = resolve_repo_path(
        protocol["inputs"]["sequences_dir"], repo_root
    )
    device = _device(args.device)
    maximum_raw_difference = 0.0
    maximum_calibrated_difference = 0.0
    verified_runs = 0
    for run_id, expected_hash in sorted(outputs["model_sha256"].items()):
        artifact_path = models_dir / f"{run_id}.pt"
        model, sorted_reference, metadata = load_lstm_artifact(
            artifact_path,
            expected_split_manifest_id=results["split_manifest_id"],
            expected_preprocessing_decision_id=results[
                "preprocessing_decision_id"
            ],
        )
        verify_registered_hash(artifact_path, expected_hash)
        pipeline = str(metadata["pipeline"])
        sequences = np.load(
            sequences_dir / pipeline / "validation.npy", allow_pickle=False
        )
        model = model.to(device)
        observed_raw = reconstruction_errors(
            model, sequences, batch_size=args.batch_size, device=device
        )
        observed_calibrated = np.searchsorted(
            sorted_reference, observed_raw, side="right"
        ).astype(float) / len(sorted_reference)
        recorded = score_frame[score_frame["run_id"] == run_id]
        if len(recorded) != len(sequences):
            raise RuntimeError(f"Recorded score count mismatch: {run_id}")
        raw_difference = float(
            np.max(
                np.abs(
                    observed_raw
                    - recorded["raw_reconstruction_error"].to_numpy(dtype=float)
                )
            )
        )
        calibrated_difference = float(
            np.max(
                np.abs(
                    observed_calibrated
                    - recorded["calibrated_score"].to_numpy(dtype=float)
                )
            )
        )
        if not np.allclose(
            observed_raw,
            recorded["raw_reconstruction_error"].to_numpy(dtype=float),
            rtol=1e-5,
            atol=1e-6,
        ):
            raise RuntimeError(f"Raw scores do not reproduce: {run_id}")
        if not np.allclose(
            observed_calibrated,
            recorded["calibrated_score"].to_numpy(dtype=float),
            rtol=0.0,
            atol=1e-12,
        ):
            raise RuntimeError(f"Calibrated scores do not reproduce: {run_id}")
        maximum_raw_difference = max(maximum_raw_difference, raw_difference)
        maximum_calibrated_difference = max(
            maximum_calibrated_difference, calibrated_difference
        )
        verified_runs += 1
        print(
            f"VERIFIED {run_id} raw_max_abs_diff={raw_difference:.3e} "
            f"calibrated_max_abs_diff={calibrated_difference:.3e}",
            flush=True,
        )

    if verified_runs != int(results["completed_runs"]):
        raise RuntimeError("Verified run count differs from completed run count")
    print(
        json.dumps(
            {
                "verified_runs": verified_runs,
                "maximum_raw_absolute_difference": maximum_raw_difference,
                "maximum_calibrated_absolute_difference": (
                    maximum_calibrated_difference
                ),
                "test_data_opened_by_verification": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
