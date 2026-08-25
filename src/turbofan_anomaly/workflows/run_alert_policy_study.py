"""Run the registered FD002 Phase 5 alert-policy study on validation only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import joblib
import numpy as np
import pandas as pd
import sklearn
import torch

from turbofan_anomaly.alerting.persistence import apply_alert_policy
from turbofan_anomaly.alerting.thresholds import (
    FittedThresholds,
    ThresholdRule,
    fit_thresholds,
    generate_alert_candidates,
    registered_threshold_rules,
)
from turbofan_anomaly.data.windows import summary_features
from turbofan_anomaly.evaluation.alerts import (
    aggregate_candidate_metrics,
    evaluate_alert_policy,
    select_best_candidates,
)
from turbofan_anomaly.evaluation.ledger import (
    append_run_record,
    load_run_ledger,
    validate_run_record,
)
from turbofan_anomaly.evaluation.provenance import (
    canonical_repo_relative,
    find_repository_root,
    repo_relative_posix,
    resolve_repo_path,
    sha256_file,
    verify_registered_hash,
)
from turbofan_anomaly.evaluation.proxies import (
    registered_validation_policies,
    training_eligible_windows,
)
from turbofan_anomaly.evaluation.ranking import proxy_ranking_metrics
from turbofan_anomaly.models.classical import (
    ClassicalAnomalyModel,
    load_baseline_artifact,
    save_baseline_artifact,
)
from turbofan_anomaly.models.lstm_training import (
    aligned_calibrated_score_ensemble,
    load_lstm_artifact,
    reconstruction_errors,
    validate_sequence_collection,
)


ALLOWED_SPLITS = ("train", "validation")
SCORE_SOURCE_ORDER = (
    "lof",
    "one_class_svm",
    "isolation_forest",
    "pca_reconstruction",
    "lstm_calibrated_ensemble",
)
REGISTERED_SEEDS = (43, 44, 45)
_RUN_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")
_FORBIDDEN_PATH_MARKERS = (
    "held_out_internal_test",
    "official_nasa_test",
    "internal_test",
    "test_fd002",
    "rul_fd002",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("configs/alerting/fd002-alert-policy-study-protocol-v1.json"),
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Explicit run ID; v1 requires fd002-alert-policy-study-v1",
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument(
        "--ledger", type=Path, default=Path("experiments/runs_v2.jsonl")
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def _atomic_write_json(payload: Mapping[str, Any], path: Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing JSON output: {destination}")
    temporary = destination.with_name(f".{destination.name}.tmp")
    if temporary.exists():
        raise FileExistsError(f"Refusing stale temporary JSON: {temporary}")
    try:
        temporary.write_text(
            json.dumps(_json_safe(dict(payload)), indent=2, sort_keys=True, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n")


def _git_value(repo_root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args], cwd=repo_root, check=True, capture_output=True
    )
    return process.stdout.decode("utf-8").strip()


def _device(choice: str) -> torch.device:
    if choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable")
        return torch.device("cuda")
    if choice == "cpu":
        return torch.device("cpu")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def validate_allowed_split_name(split_name: str) -> str:
    value = str(split_name)
    if value not in ALLOWED_SPLITS:
        raise ValueError(f"Split is not allowed by Phase 5 protocol: {value}")
    return value


def validate_allowed_input_path(path_value: str | Path, split_name: str) -> str:
    split = validate_allowed_split_name(split_name)
    canonical = canonical_repo_relative(path_value)
    lowered = canonical.lower()
    if any(marker in lowered for marker in _FORBIDDEN_PATH_MARKERS):
        raise ValueError(f"Prohibited Phase 5 input path: {canonical}")
    if split not in Path(canonical).name.lower():
        raise ValueError(f"Input filename does not identify {split}: {canonical}")
    return canonical


def validate_alert_policy_protocol(protocol: Mapping[str, Any]) -> None:
    """Reject any drift from the committed Phase 5 design before execution."""
    if protocol.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported Phase 5 protocol schema")
    if protocol.get("study_id") != "fd002-alert-policy-study-v1":
        raise ValueError("Unexpected Phase 5 study ID")
    if protocol.get("status") != "registered_before_execution":
        raise RuntimeError("Phase 5 protocol was not registered before execution")
    boundary = protocol["evidence_boundary"]
    if boundary["allowed_splits"] != ["train", "validation"]:
        raise RuntimeError("Phase 5 split allow-list changed")
    if not {"held_out_internal_test", "official_nasa_test"}.issubset(
        boundary["prohibited_inputs"]
    ):
        raise RuntimeError("Phase 5 prohibited-input policy is incomplete")
    if any(
        bool(boundary[field])
        for field in (
            "test_data_may_be_opened",
            "final_result",
            "online_recalibration",
            "fusion_evaluated",
            "healthy_fraction_sensitivity_authorized",
            "additional_onset_policies_authorized",
        )
    ):
        raise RuntimeError("Phase 5 evidence boundary was weakened")
    if boundary["gate_4_status_after_execution"] != "recommended_pending_owner_approval":
        raise RuntimeError("Gate 4 status differs from registration")

    contract = protocol["window_contract"]
    expected_contract = {
        "shape": [30, 21],
        "eligible_training_windows": 5037,
        "validation_windows": 9365,
        "training_engines": 156,
        "validation_engines": 52,
        "train_validation_engine_overlap": 0,
        "operating_mode_count": 6,
        "minimum_eligible_training_windows_per_mode": 100,
    }
    if any(contract[key] != value for key, value in expected_contract.items()):
        raise RuntimeError("Phase 5 window contract differs from registration")
    if tuple(item["detector_id"] for item in protocol["score_sources"]) != SCORE_SOURCE_ORDER:
        raise RuntimeError("Phase 5 score-source order differs from registration")
    grid = protocol["grid"]
    if tuple(grid["score_source_order"]) != SCORE_SOURCE_ORDER:
        raise RuntimeError("Phase 5 grid detector order differs from registration")
    if grid["threshold_context_order"] != ["global", "per_mode"]:
        raise RuntimeError("Phase 5 threshold contexts changed")
    if len(grid["threshold_rules"]) != 8 or len(grid["ewma_states"]) != 4:
        raise RuntimeError("Phase 5 threshold/EWMA grid changed")
    if grid["persistence_values"] != [1, 3, 5, 8]:
        raise RuntimeError("Phase 5 persistence grid changed")
    candidate_count = (
        len(grid["score_source_order"])
        * len(grid["threshold_context_order"])
        * len(grid["threshold_rules"])
        * len(grid["ewma_states"])
        * len(grid["persistence_values"])
    )
    if candidate_count != int(grid["expected_candidate_count"]):
        raise RuntimeError("Phase 5 candidate count changed")
    if candidate_count != 1280 or candidate_count * len(protocol["proxy_policies"]) != 6400:
        raise RuntimeError("Phase 5 candidate-policy count changed")
    if grid["comparison"] != "strict_greater_than" or grid["threshold_clipping"]:
        raise RuntimeError("Phase 5 threshold comparison changed")
    selection = protocol["selection_objective"]
    if selection["feasibility"]["maximum"] != 60.0:
        raise RuntimeError("Phase 5 feasibility constraint changed")
    if selection["result_status"] != "recommended_pending_owner_approval":
        raise RuntimeError("Phase 5 selection status changed")
    if protocol["complementarity"]["fusion_evaluated"]:
        raise RuntimeError("Fusion is outside the Phase 5 protocol")
    for split in ALLOWED_SPLITS:
        validate_allowed_input_path(protocol["inputs"]["sequences"][split]["path"], split)
        validate_allowed_input_path(protocol["inputs"]["metadata"][split]["path"], split)


def _verify_reference(reference: Mapping[str, Any], repo_root: Path) -> Path:
    path = resolve_repo_path(reference["path"], repo_root)
    verification = verify_registered_hash(path, reference["sha256"])
    if verification.match_form != reference["hash_form"]:
        raise RuntimeError(
            f"Registered hash form mismatch for {reference['path']}: "
            f"expected {reference['hash_form']}, observed {verification.match_form}"
        )
    return path


def verify_pre_execution_references(
    protocol: Mapping[str, Any],
    repo_root: Path,
    *,
    verify_lifecycle_authorities: bool = True,
) -> dict[str, Path]:
    """Verify every registered authority, report, array, metadata, and model input."""
    resolved: dict[str, Path] = {}
    for reference in protocol["authorities"]:
        if reference["lifecycle_update_after_execution"] and not verify_lifecycle_authorities:
            continue
        resolved[str(reference["authority_id"])] = _verify_reference(reference, repo_root)
    for family in ("registered_classical_reports", "registered_final_refit_reports"):
        for reference in protocol["inputs"][family]:
            resolved[str(reference["path"])] = _verify_reference(reference, repo_root)
    for split in ALLOWED_SPLITS:
        for kind in ("sequences", "metadata"):
            reference = protocol["inputs"][kind][split]
            validate_allowed_input_path(reference["path"], split)
            resolved[f"{kind}:{split}"] = _verify_reference(reference, repo_root)
    for seed, reference in protocol["inputs"]["final_lstm_models"].items():
        resolved[f"lstm_model:{seed}"] = _verify_reference(reference, repo_root)
    return resolved


def load_allowed_inputs(
    protocol: Mapping[str, Any],
    repo_root: Path,
    *,
    verify_lifecycle_authorities: bool = True,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame, pd.DataFrame]:
    """Load only hash-verified training/validation arrays and metadata."""
    paths = verify_pre_execution_references(
        protocol,
        repo_root,
        verify_lifecycle_authorities=verify_lifecycle_authorities,
    )
    train_sequences = np.load(
        paths["sequences:train"], allow_pickle=False, mmap_mode="r"
    )
    validation_sequences = np.load(
        paths["sequences:validation"], allow_pickle=False, mmap_mode="r"
    )
    train_metadata = pd.read_csv(paths["metadata:train"])
    validation_metadata = pd.read_csv(paths["metadata:validation"])
    expected_shape = tuple(map(int, protocol["window_contract"]["shape"]))
    validate_sequence_collection(
        train_sequences,
        expected_window_shape=expected_shape,
        expected_count=len(train_metadata),
        name="P1 training sequences",
    )
    validate_sequence_collection(
        validation_sequences,
        expected_window_shape=expected_shape,
        expected_count=int(protocol["window_contract"]["validation_windows"]),
        name="P1 validation sequences",
    )
    required = {
        "window_id",
        "engine",
        "start_cycle",
        "end_cycle",
        "max_cycle",
        "split",
        "split_manifest_id",
        "op_mode",
    }
    for metadata, split in (
        (train_metadata, "train"),
        (validation_metadata, "validation"),
    ):
        missing = required - set(metadata.columns)
        if missing:
            raise ValueError(f"Missing {split} metadata columns: {sorted(missing)}")
        if set(metadata["split"].astype(str)) != {split}:
            raise RuntimeError(f"Unexpected {split} metadata split identity")
        if set(metadata["split_manifest_id"].astype(str)) != {
            protocol["inputs"]["split_manifest_id"]
        }:
            raise RuntimeError(f"Unexpected {split} metadata manifest identity")
        if metadata["window_id"].isna().any() or metadata["window_id"].duplicated().any():
            raise RuntimeError(f"{split} metadata window IDs are not unique")
        if metadata["op_mode"].isna().any():
            raise RuntimeError(f"{split} metadata contains null operating modes")
        numeric_modes = metadata["op_mode"].to_numpy(dtype=float)
        if not np.isfinite(numeric_modes).all() or not np.equal(
            numeric_modes, np.floor(numeric_modes)
        ).all():
            raise RuntimeError(f"{split} metadata operating modes are not finite integers")
        metadata["op_mode"] = numeric_modes.astype(int)
    train_engines = set(train_metadata["engine"].astype(int))
    validation_engines = set(validation_metadata["engine"].astype(int))
    if train_engines & validation_engines:
        raise RuntimeError("Training and validation engines overlap")
    if len(train_engines) != 156 or len(validation_engines) != 52:
        raise RuntimeError("Unexpected train/validation engine counts")
    validation_modes = set(validation_metadata["op_mode"].astype(int))
    if len(validation_modes) != 6:
        raise RuntimeError("Validation metadata must contain exactly six P1 modes")
    return train_sequences, validation_sequences, train_metadata, validation_metadata


def _score_frame(
    metadata: pd.DataFrame,
    *,
    detector_id: str,
    split: str,
    alert_score: np.ndarray,
    raw_score: np.ndarray | None,
) -> pd.DataFrame:
    validate_allowed_split_name(split)
    values = np.asarray(alert_score, dtype=float).reshape(-1)
    if len(values) != len(metadata) or not np.isfinite(values).all():
        raise ValueError("Alert scores are not finite and metadata-aligned")
    if np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("Calibrated alert scores must lie in [0, 1]")
    frame = metadata[
        ["window_id", "engine", "start_cycle", "end_cycle", "max_cycle", "op_mode"]
    ].copy()
    frame["raw_score"] = np.nan if raw_score is None else np.asarray(raw_score, dtype=float)
    frame["alert_score"] = values
    frame["detector_id"] = detector_id
    frame["pipeline_id"] = "p1_k6"
    frame["split"] = split
    if frame["window_id"].isna().any() or frame["window_id"].duplicated().any():
        raise RuntimeError("Score-frame window IDs are not unique")
    return frame


def score_frame_sha256(frame: pd.DataFrame) -> str:
    """Hash a deterministic LF CSV view of a score frame without writing it."""
    payload = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _assert_close(
    observed: np.ndarray,
    expected: np.ndarray,
    tolerance: Mapping[str, Any],
    label: str,
) -> float:
    observed_values = np.asarray(observed, dtype=float)
    expected_values = np.asarray(expected, dtype=float)
    if observed_values.shape != expected_values.shape:
        raise RuntimeError(f"{label} shape differs from registration")
    if not np.allclose(
        observed_values,
        expected_values,
        rtol=float(tolerance["relative_tolerance"]),
        atol=float(tolerance["absolute_tolerance"]),
    ):
        difference = float(np.max(np.abs(observed_values - expected_values)))
        raise RuntimeError(f"{label} does not reproduce; max difference={difference}")
    return float(np.max(np.abs(observed_values - expected_values)))


def reproduce_score_sources(
    *,
    protocol: Mapping[str, Any],
    repo_root: Path,
    train_sequences: np.ndarray,
    validation_sequences: np.ndarray,
    train_metadata: pd.DataFrame,
    validation_metadata: pd.DataFrame,
    model_directory: Path,
    device: torch.device,
) -> tuple[
    dict[str, pd.DataFrame],
    dict[str, pd.DataFrame],
    pd.DataFrame,
    dict[str, str],
]:
    """Reproduce the five frozen score sources without model or parameter search."""
    eligible = training_eligible_windows(train_metadata, 0.30).to_numpy(dtype=bool)
    if int(eligible.sum()) != 5037:
        raise RuntimeError("Expected exactly 5,037 eligible training windows")
    eligible_metadata = train_metadata.loc[eligible].reset_index(drop=True)
    training_modes = set(eligible_metadata["op_mode"].astype(int))
    validation_modes = set(validation_metadata["op_mode"].astype(int))
    if len(training_modes) != 6 or training_modes != validation_modes:
        raise RuntimeError("Eligible-training/validation P1 modes must be the same six modes")
    counts = eligible_metadata["op_mode"].value_counts()
    minimum = int(protocol["window_contract"]["minimum_eligible_training_windows_per_mode"])
    if int(counts.min()) < minimum:
        raise RuntimeError("An eligible-training mode has fewer than 100 windows")

    policy_frames = [
        policy.apply(validation_metadata) for policy in registered_validation_policies()
    ]
    train_features = summary_features(train_sequences[eligible])
    validation_features = summary_features(validation_sequences)
    registered_scores_path = resolve_repo_path(
        "reports/baselines_v2/validation_scores.csv", repo_root
    )
    registered_scores = pd.read_csv(registered_scores_path)
    registered_scores = registered_scores[registered_scores["pipeline"] == "p1_k6"]
    classical_tolerance = protocol["score_reproduction_tolerances"][
        "classical_ranking_metrics"
    ]
    training_frames: dict[str, pd.DataFrame] = {}
    validation_frames: dict[str, pd.DataFrame] = {}
    reproduction_rows: list[dict[str, Any]] = []
    bundle_hashes: dict[str, str] = {}

    source_by_id = {item["detector_id"]: item for item in protocol["score_sources"]}
    for detector_id in SCORE_SOURCE_ORDER[:4]:
        source = source_by_id[detector_id]
        model_name = str(source.get("model_detector_name", detector_id))
        parameters = dict(source["parameters"])
        parameters.pop("novelty", None)
        random_state = int(parameters.pop("random_state", 42))
        model = ClassicalAnomalyModel(
            model_name, parameters, random_state=random_state
        ).fit(train_features)
        training_raw, training_calibrated = model.score(train_features)
        validation_raw, validation_calibrated = model.score(validation_features)
        registered_detector = model_name
        expected = registered_scores[registered_scores["detector"] == registered_detector]
        if len(expected) != 9365 or set(expected["window_id"]) != set(
            validation_metadata["window_id"]
        ):
            raise RuntimeError(f"Registered validation scores are incomplete for {detector_id}")
        expected = expected.set_index("window_id").loc[
            validation_metadata["window_id"]
        ]
        raw_difference = _assert_close(
            validation_raw,
            expected["raw_score"].to_numpy(dtype=float),
            classical_tolerance,
            f"{detector_id} raw validation scores",
        )
        calibrated_difference = _assert_close(
            validation_calibrated,
            expected["calibrated_score"].to_numpy(dtype=float),
            classical_tolerance,
            f"{detector_id} calibrated validation scores",
        )
        _, observed_pr, observed_roc = proxy_ranking_metrics(
            validation_calibrated, policy_frames
        )
        metric_difference = max(
            abs(observed_pr - float(source["registered_selection_mean_pr_auc"])),
            abs(observed_roc - float(source["registered_selection_mean_roc_auc"])),
        )
        if not np.isclose(
            observed_pr,
            float(source["registered_selection_mean_pr_auc"]),
            rtol=float(classical_tolerance["relative_tolerance"]),
            atol=float(classical_tolerance["absolute_tolerance"]),
        ) or not np.isclose(
            observed_roc,
            float(source["registered_selection_mean_roc_auc"]),
            rtol=float(classical_tolerance["relative_tolerance"]),
            atol=float(classical_tolerance["absolute_tolerance"]),
        ):
            raise RuntimeError(f"{detector_id} ranking metrics do not reproduce")
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
        artifact_path = model_directory / f"{detector_id}.joblib"
        save_baseline_artifact(
            model,
            {
                "study_id": protocol["study_id"],
                "pipeline": "p1_k6",
                "detector_id": detector_id,
                "parameters": parameters,
                "random_state": random_state,
                "fit_window_count": 5037,
                "split_manifest_id": protocol["inputs"]["split_manifest_id"],
                "preprocessing_decision_id": protocol["inputs"][
                    "preprocessing_decision_id"
                ],
                "score_calibration": "empirical_cdf_fitted_on_eligible_training_scores",
                "artifact_role": "phase5_reproduction_not_retuning",
                "historical_serialization_hash_expected_to_match": False,
                "test_data_opened": False,
            },
            artifact_path,
        )
        bundle_hashes[detector_id] = sha256_file(artifact_path)
        reproduction_rows.append(
            {
                "detector_id": detector_id,
                "validation_rows": 9365,
                "maximum_raw_score_difference": raw_difference,
                "maximum_calibrated_score_difference": calibrated_difference,
                "observed_selection_mean_pr_auc": observed_pr,
                "registered_selection_mean_pr_auc": source[
                    "registered_selection_mean_pr_auc"
                ],
                "observed_selection_mean_roc_auc": observed_roc,
                "registered_selection_mean_roc_auc": source[
                    "registered_selection_mean_roc_auc"
                ],
                "maximum_ranking_metric_difference": metric_difference,
                "reproduced": True,
            }
        )

    per_seed_training: dict[int, pd.DataFrame] = {}
    per_seed_validation: dict[int, pd.DataFrame] = {}
    final_validation_scores = pd.read_csv(
        resolve_repo_path(
            "reports/lstm_final_v1/fd002-lstm-final-refit-v1/validation_scores.csv",
            repo_root,
        )
    )
    raw_tolerance = protocol["score_reproduction_tolerances"]["lstm_raw_scores"]
    calibrated_tolerance = protocol["score_reproduction_tolerances"][
        "lstm_calibrated_scores"
    ]
    max_lstm_raw = 0.0
    max_lstm_calibrated = 0.0
    for seed in REGISTERED_SEEDS:
        reference = protocol["inputs"]["final_lstm_models"][str(seed)]
        artifact_path = _verify_reference(reference, repo_root)
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
            model, train_sequences[eligible], batch_size=128, device=device
        )
        validation_raw = reconstruction_errors(
            model, validation_sequences, batch_size=128, device=device
        )
        training_calibrated = np.searchsorted(
            calibration_reference, training_raw, side="right"
        ).astype(float) / len(calibration_reference)
        validation_calibrated = np.searchsorted(
            calibration_reference, validation_raw, side="right"
        ).astype(float) / len(calibration_reference)
        expected = final_validation_scores[final_validation_scores["seed"] == seed]
        if len(expected) != 9365:
            raise RuntimeError(f"Registered final LSTM scores are incomplete for seed {seed}")
        expected = expected.set_index("window_id").loc[
            validation_metadata["window_id"]
        ]
        max_lstm_raw = max(
            max_lstm_raw,
            _assert_close(
                validation_raw,
                expected["raw_reconstruction_error"].to_numpy(dtype=float),
                raw_tolerance,
                f"LSTM seed {seed} raw validation scores",
            ),
        )
        max_lstm_calibrated = max(
            max_lstm_calibrated,
            _assert_close(
                validation_calibrated,
                expected["calibrated_score"].to_numpy(dtype=float),
                calibrated_tolerance,
                f"LSTM seed {seed} calibrated validation scores",
            ),
        )
        per_seed_training[seed] = pd.DataFrame(
            {
                "window_id": eligible_metadata["window_id"].to_numpy(),
                "calibrated_score": training_calibrated,
            }
        )
        per_seed_validation[seed] = pd.DataFrame(
            {
                "window_id": validation_metadata["window_id"].to_numpy(),
                "calibrated_score": validation_calibrated,
            }
        )
    training_ensemble = aligned_calibrated_score_ensemble(per_seed_training)
    validation_ensemble = aligned_calibrated_score_ensemble(per_seed_validation)
    training_ensemble_scores = training_ensemble.set_index("window_id").loc[
        eligible_metadata["window_id"], "ensemble_calibrated_score"
    ].to_numpy(dtype=float)
    validation_ensemble_scores = validation_ensemble.set_index("window_id").loc[
        validation_metadata["window_id"], "ensemble_calibrated_score"
    ].to_numpy(dtype=float)
    registered_ensemble = pd.read_csv(
        resolve_repo_path(
            "reports/lstm_final_v1/fd002-lstm-final-refit-v1/ensemble_validation_scores.csv",
            repo_root,
        )
    ).set_index("window_id").loc[validation_metadata["window_id"]]
    ensemble_difference = _assert_close(
        validation_ensemble_scores,
        registered_ensemble["ensemble_calibrated_score"].to_numpy(dtype=float),
        protocol["score_reproduction_tolerances"]["lstm_ensemble_scores"],
        "Final LSTM calibrated ensemble validation scores",
    )
    source = source_by_id["lstm_calibrated_ensemble"]
    _, observed_pr, observed_roc = proxy_ranking_metrics(
        validation_ensemble_scores, policy_frames
    )
    if not np.isclose(
        observed_pr,
        float(source["registered_selection_mean_pr_auc"]),
        rtol=0.0,
        atol=1e-12,
    ) or not np.isclose(
        observed_roc,
        float(source["registered_selection_mean_roc_auc"]),
        rtol=0.0,
        atol=1e-12,
    ):
        raise RuntimeError("Final LSTM ensemble ranking metrics do not reproduce")
    training_frames["lstm_calibrated_ensemble"] = _score_frame(
        eligible_metadata,
        detector_id="lstm_calibrated_ensemble",
        split="train",
        alert_score=training_ensemble_scores,
        raw_score=None,
    )
    validation_frames["lstm_calibrated_ensemble"] = _score_frame(
        validation_metadata,
        detector_id="lstm_calibrated_ensemble",
        split="validation",
        alert_score=validation_ensemble_scores,
        raw_score=None,
    )
    ensemble_bundle = model_directory / "lstm_calibrated_ensemble.json"
    _atomic_write_json(
        {
            "schema_version": "1.0.0",
            "study_id": protocol["study_id"],
            "detector_id": "lstm_calibrated_ensemble",
            "aggregation": "arithmetic_mean_of_window_id_aligned_calibrated_scores",
            "source_artifacts": protocol["inputs"]["final_lstm_models"],
            "raw_score_claim": False,
            "test_data_opened": False,
        },
        ensemble_bundle,
    )
    bundle_hashes["lstm_calibrated_ensemble"] = sha256_file(ensemble_bundle)
    reproduction_rows.append(
        {
            "detector_id": "lstm_calibrated_ensemble",
            "validation_rows": 9365,
            "maximum_raw_score_difference": max_lstm_raw,
            "maximum_calibrated_score_difference": max(
                max_lstm_calibrated, ensemble_difference
            ),
            "observed_selection_mean_pr_auc": observed_pr,
            "registered_selection_mean_pr_auc": source[
                "registered_selection_mean_pr_auc"
            ],
            "observed_selection_mean_roc_auc": observed_roc,
            "registered_selection_mean_roc_auc": source[
                "registered_selection_mean_roc_auc"
            ],
            "maximum_ranking_metric_difference": max(
                abs(observed_pr - float(source["registered_selection_mean_pr_auc"])),
                abs(observed_roc - float(source["registered_selection_mean_roc_auc"])),
            ),
            "reproduced": True,
        }
    )
    for detector_id in SCORE_SOURCE_ORDER:
        if len(training_frames[detector_id]) != 5037:
            raise RuntimeError(f"Training score-frame count differs for {detector_id}")
        if len(validation_frames[detector_id]) != 9365:
            raise RuntimeError(f"Validation score-frame count differs for {detector_id}")
    reproduction = pd.DataFrame(reproduction_rows).set_index("detector_id")
    for detector_id in SCORE_SOURCE_ORDER:
        reproduction.loc[detector_id, "training_score_frame_sha256"] = (
            score_frame_sha256(training_frames[detector_id])
        )
        reproduction.loc[detector_id, "validation_score_frame_sha256"] = (
            score_frame_sha256(validation_frames[detector_id])
        )
    return (
        training_frames,
        validation_frames,
        reproduction.reset_index(),
        bundle_hashes,
    )


def build_alert_study_tables(
    *,
    protocol: Mapping[str, Any],
    training_frames: Mapping[str, pd.DataFrame],
    validation_frames: Mapping[str, pd.DataFrame],
    validation_metadata: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Evaluate all 1,280 candidates under all five registered policies."""
    rules = {rule.rule_id: rule for rule in registered_threshold_rules()}
    grid_rules = tuple(item["rule_id"] for item in protocol["grid"]["threshold_rules"])
    if grid_rules != tuple(rules):
        raise RuntimeError("Implementation threshold-rule order differs from protocol")
    candidates = generate_alert_candidates(
        protocol["grid"]["score_source_order"],
        protocol["grid"]["threshold_context_order"],
        tuple(rules.values()),
        protocol["grid"]["ewma_states"],
        protocol["grid"]["persistence_values"],
    )
    if len(candidates) != 1280:
        raise RuntimeError("Phase 5 implementation did not generate 1,280 candidates")
    expected_modes = sorted(training_frames[SCORE_SOURCE_ORDER[0]]["op_mode"].unique())
    threshold_cache: dict[tuple[str, str, str], FittedThresholds] = {}
    threshold_rows: list[dict[str, Any]] = []
    training_summary_rows: list[dict[str, Any]] = []
    for detector_id in SCORE_SOURCE_ORDER:
        training = training_frames[detector_id]
        training_summary_rows.append(
            {
                "detector_id": detector_id,
                "operating_mode": "global",
                "score_count": len(training),
                "score_mean": float(training["alert_score"].mean()),
                "score_std_ddof0": float(np.std(training["alert_score"], ddof=0)),
                "score_minimum": float(training["alert_score"].min()),
                "score_maximum": float(training["alert_score"].max()),
                "score_frame_sha256": score_frame_sha256(training),
                "threshold_reference_split": "train",
            }
        )
        for mode, group in training.groupby("op_mode", sort=True):
            training_summary_rows.append(
                {
                    "detector_id": detector_id,
                    "operating_mode": int(mode),
                    "score_count": len(group),
                    "score_mean": float(group["alert_score"].mean()),
                    "score_std_ddof0": float(np.std(group["alert_score"], ddof=0)),
                    "score_minimum": float(group["alert_score"].min()),
                    "score_maximum": float(group["alert_score"].max()),
                    "score_frame_sha256": score_frame_sha256(training),
                    "threshold_reference_split": "train",
                }
            )
        for context in protocol["grid"]["threshold_context_order"]:
            for rule in rules.values():
                fitted = fit_thresholds(
                    training["alert_score"].to_numpy(dtype=float),
                    training["op_mode"].to_numpy(),
                    context=context,
                    rule=rule,
                    split_name="train",
                    expected_modes=expected_modes,
                    minimum_mode_count=int(
                        protocol["window_contract"][
                            "minimum_eligible_training_windows_per_mode"
                        ]
                    ),
                )
                threshold_cache[(detector_id, context, rule.rule_id)] = fitted
                for mode, value in fitted.values.items():
                    threshold_rows.append(
                        {
                            "detector_id": detector_id,
                            "threshold_context": context,
                            "threshold_rule_id": rule.rule_id,
                            "operating_mode": "global" if mode is None else int(mode),
                            "threshold": value,
                            "reference_count": fitted.reference_counts[mode],
                            "reference_split": "train",
                            "clipped": False,
                        }
                    )

    policy_frames = [
        policy.apply(validation_metadata) for policy in registered_validation_policies()
    ]
    metric_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        detector_id = candidate["detector_id"]
        alpha = candidate["ewma_alpha"]
        trace = apply_alert_policy(
            validation_frames[detector_id],
            threshold_cache[
                (
                    detector_id,
                    candidate["threshold_context"],
                    candidate["threshold_rule_id"],
                )
            ],
            ewma_alpha=alpha,
            persistence=int(candidate["persistence"]),
        )
        for policy_frame in policy_frames:
            metric, _, _ = evaluate_alert_policy(trace, policy_frame)
            metric_rows.append({**candidate, **metric})
    candidate_policy = pd.DataFrame(metric_rows)
    if len(candidate_policy) != 6400:
        raise RuntimeError("Phase 5 did not produce exactly 6,400 candidate-policy rows")
    aggregated = aggregate_candidate_metrics(
        candidate_policy,
        selection_policy_ids=protocol["selection_objective"]["selection_policy_ids"],
        feasibility_limit=float(
            protocol["selection_objective"]["feasibility"]["maximum"]
        ),
    )
    if len(aggregated) != 1280:
        raise RuntimeError("Phase 5 did not aggregate exactly 1,280 candidates")
    per_detector, overall = select_best_candidates(aggregated)
    if not per_detector.empty:
        per_detector["selection_status"] = "recommended_pending_owner_approval"
        per_detector["median_delay_aspiration_met"] = (
            per_detector["median_policy_median_detection_delay"]
            <= float(protocol["selection_objective"]["median_delay_aspiration_cycles"])
        )
    if not overall.empty:
        overall["selection_status"] = "recommended_pending_owner_approval"
        overall["median_delay_aspiration_met"] = (
            overall["median_policy_median_detection_delay"]
            <= float(protocol["selection_objective"]["median_delay_aspiration_cycles"])
        )

    selected_trace_frames: list[pd.DataFrame] = []
    selected_event_frames: list[pd.DataFrame] = []
    selected_engine_frames: list[pd.DataFrame] = []
    complement_inputs: dict[tuple[str, str], pd.DataFrame] = {}
    selected_rows = per_detector.to_dict(orient="records")
    overall_id = None if overall.empty else str(overall.iloc[0]["candidate_id"])
    for selected in selected_rows:
        detector_id = str(selected["detector_id"])
        candidate_id = str(selected["candidate_id"])
        alpha = selected["ewma_alpha"]
        alpha_value = None if pd.isna(alpha) else float(alpha)
        trace = apply_alert_policy(
            validation_frames[detector_id],
            threshold_cache[
                (
                    detector_id,
                    str(selected["threshold_context"]),
                    str(selected["threshold_rule_id"]),
                )
            ],
            ewma_alpha=alpha_value,
            persistence=int(selected["persistence"]),
        )
        trace.insert(0, "candidate_id", candidate_id)
        if candidate_id == overall_id:
            selected_trace_frames.append(trace)
        for policy_frame in policy_frames:
            metric, per_engine, events = evaluate_alert_policy(trace, policy_frame)
            per_engine.insert(0, "detector_id", detector_id)
            per_engine.insert(0, "candidate_id", candidate_id)
            if metric["selection_policy"]:
                complement_inputs[(detector_id, metric["policy_id"])] = per_engine.copy()
            if candidate_id == overall_id:
                selected_engine_frames.append(per_engine)
                if not events.empty:
                    events.insert(0, "detector_id", detector_id)
                    events.insert(0, "candidate_id", candidate_id)
                    selected_event_frames.append(events)

    complementarity_rows: list[dict[str, Any]] = []
    detector_winners = [str(value) for value in per_detector["detector_id"]] if not per_detector.empty else []
    for policy_id in protocol["selection_objective"]["selection_policy_ids"]:
        for detector_a, detector_b in combinations(detector_winners, 2):
            left = complement_inputs[(detector_a, policy_id)][
                ["engine", "detected", "healthy_false_alert"]
            ].rename(
                columns={
                    "detected": "detected_a",
                    "healthy_false_alert": "false_a",
                }
            )
            right = complement_inputs[(detector_b, policy_id)][
                ["engine", "detected", "healthy_false_alert"]
            ].rename(
                columns={
                    "detected": "detected_b",
                    "healthy_false_alert": "false_b",
                }
            )
            aligned = left.merge(right, on="engine", validate="one_to_one")
            complementarity_rows.append(
                {
                    "policy_id": policy_id,
                    "detector_a": detector_a,
                    "detector_b": detector_b,
                    "engine_count": len(aligned),
                    "both_detected": int((aligned["detected_a"] & aligned["detected_b"]).sum()),
                    "only_a_detected": int((aligned["detected_a"] & ~aligned["detected_b"]).sum()),
                    "only_b_detected": int((~aligned["detected_a"] & aligned["detected_b"]).sum()),
                    "neither_detected": int((~aligned["detected_a"] & ~aligned["detected_b"]).sum()),
                    "both_healthy_false_alert": int((aligned["false_a"] & aligned["false_b"]).sum()),
                    "only_a_healthy_false_alert": int((aligned["false_a"] & ~aligned["false_b"]).sum()),
                    "only_b_healthy_false_alert": int((~aligned["false_a"] & aligned["false_b"]).sum()),
                    "neither_healthy_false_alert": int((~aligned["false_a"] & ~aligned["false_b"]).sum()),
                    "fusion_evaluated": False,
                }
            )

    target_rows: list[dict[str, Any]] = []
    if overall.empty:
        target_rows.append(
            {
                "candidate_id": None,
                "policy_id": None,
                "false_positive_endpoint_target_met": False,
                "median_delay_aspiration_met": False,
                "target_attainment_status": "no_feasible_candidate",
                "gate_4_status": "recommended_pending_owner_approval",
            }
        )
    else:
        overall_metrics = candidate_policy[
            (candidate_policy["candidate_id"] == overall_id)
            & candidate_policy["policy_id"].isin(
                protocol["selection_objective"]["selection_policy_ids"]
            )
        ]
        for row in overall_metrics.to_dict(orient="records"):
            target_rows.append(
                {
                    "candidate_id": overall_id,
                    "policy_id": row["policy_id"],
                    "false_positive_alerted_endpoints_per_1000": row[
                        "false_positive_alerted_endpoints_per_1000_healthy_endpoints"
                    ],
                    "false_positive_endpoint_target_met": row[
                        "false_positive_alerted_endpoints_per_1000_healthy_endpoints"
                    ]
                    <= 60.0,
                    "median_first_alert_delay": row["median_first_alert_delay"],
                    "median_delay_aspiration_met": bool(
                        np.isfinite(row["median_first_alert_delay"])
                        and row["median_first_alert_delay"] <= 12.0
                    ),
                    "target_attainment_status": "feasible_validation_recommendation",
                    "gate_4_status": "recommended_pending_owner_approval",
                }
            )

    empty_trace = validation_frames[SCORE_SOURCE_ORDER[0]].iloc[:0].copy()
    return {
        "training_score_reference_summary": pd.DataFrame(training_summary_rows),
        "threshold_table": pd.DataFrame(threshold_rows),
        "candidates": pd.DataFrame(candidates),
        "candidate_policy_metrics": candidate_policy,
        "candidate_selection": aggregated,
        "best_policy_per_detector": per_detector,
        "overall_recommendation": overall,
        "selected_validation_alert_trace": (
            pd.concat(selected_trace_frames, ignore_index=True)
            if selected_trace_frames
            else empty_trace
        ),
        "selected_events": (
            pd.concat(selected_event_frames, ignore_index=True)
            if selected_event_frames
            else pd.DataFrame()
        ),
        "per_engine_metrics": (
            pd.concat(selected_engine_frames, ignore_index=True)
            if selected_engine_frames
            else pd.DataFrame()
        ),
        "detector_complementarity": pd.DataFrame(complementarity_rows),
        "target_attainment": pd.DataFrame(target_rows),
    }


def expected_alert_policy_ledger_run_ids(study_id: str) -> tuple[str, ...]:
    return tuple(f"{study_id}_{detector}" for detector in SCORE_SOURCE_ORDER) + (
        f"{study_id}_overall_recommendation",
    )


def _ledger_records(
    *,
    protocol: Mapping[str, Any],
    protocol_path: Path,
    protocol_sha256: str,
    repo_root: Path,
    execution_time: str,
    code_commit: str,
    per_detector: pd.DataFrame,
    overall: pd.DataFrame,
    report_hashes: Mapping[str, str],
    bundle_hashes: Mapping[str, str],
    model_directory: Path,
    report_directory: Path,
) -> list[dict[str, Any]]:
    split_reference = next(
        item for item in protocol["authorities"] if item["authority_id"] == "fd002_primary_split"
    )
    config = {
        "study_id": protocol["study_id"],
        "path": repo_relative_posix(protocol_path, repo_root),
        "sha256": protocol_sha256,
        "hash_form": "raw",
    }
    selected_by_detector = {
        str(row["detector_id"]): row for row in per_detector.to_dict(orient="records")
    }
    records: list[dict[str, Any]] = []
    common = {
        "schema_version": "2.0.0",
        "timestamp": execution_time,
        "owner": protocol["owner"],
        "evidence_class": "validation_proxy_only",
        "result_classification": "validation_proxy_alert_policy_diagnostics_not_test_performance",
        "split": {
            "manifest_id": "fd002-primary-v1",
            "path": split_reference["path"],
            "sha256": split_reference["sha256"],
            "hash_form": split_reference["hash_form"],
        },
        "config": config,
    }
    for detector_id in SCORE_SOURCE_ORDER:
        selected = selected_by_detector.get(detector_id)
        has_selection = selected is not None
        run_id = f"{protocol['study_id']}_{detector_id}"
        bundle_name = (
            "lstm_calibrated_ensemble.json"
            if detector_id == "lstm_calibrated_ensemble"
            else f"{detector_id}.joblib"
        )
        record = {
            **common,
            "run_id": run_id,
            "source_run_id": run_id,
            "experiment_name": "phase5_alert_policy_validation",
            "model": detector_id,
            "parameters": {
                "selected_candidate_id": None if selected is None else selected["candidate_id"],
                "gate_4_status": "recommended_pending_owner_approval",
                "threshold_final_test_validated": False,
            },
            "population": {
                "train_size": 5037,
                "validation_size": 9365,
                "engine_counts": {"train": 156, "validation": 52},
            },
            "metric": {
                "name": "minimum_primary_policy_engine_detection_coverage",
                "value": None if selected is None else selected["minimum_engine_detection_coverage"],
                "value_text": None
                if selected is None
                else format(float(selected["minimum_engine_detection_coverage"]), ".17g"),
            },
            "evidence_boundary": {
                "final_result": False,
                "threshold_selected": has_selection,
                "held_out_internal_test_accessed": False,
                "threshold_final_test_validated": False,
                "gate_4_status": "recommended_pending_owner_approval",
            },
            "artifact": {
                "artifact_id": f"{run_id}:best_policy_report",
                "path": repo_relative_posix(
                    report_directory / "best_policy_per_detector.csv", repo_root
                ),
                "sha256": report_hashes["best_policy_per_detector.csv"],
                "present": True,
                "hash_form": "raw",
            },
            "model_artifact": {
                "path": repo_relative_posix(model_directory / bundle_name, repo_root),
                "sha256": bundle_hashes[detector_id],
                "present": True,
                "tracked_by_git": False,
                "hash_form": "raw",
            },
            "notes": (
                "validation-only alert-policy diagnostics; selected policy remains pending "
                "Gate 4 owner approval; no final/test validation, online recalibration, fusion, "
                "or test-data access"
            ),
            "provenance": {
                "code_commit": code_commit,
                "protocol_sha256": protocol_sha256,
                "test_data_opened": False,
                "online_recalibration": False,
                "fusion_evaluated": False,
            },
        }
        validate_run_record(record)
        records.append(record)
    overall_row = None if overall.empty else overall.iloc[0].to_dict()
    overall_id = f"{protocol['study_id']}_overall_recommendation"
    record = {
        **common,
        "run_id": overall_id,
        "source_run_id": overall_id,
        "experiment_name": "phase5_overall_alert_policy_recommendation",
        "model": None if overall_row is None else overall_row["detector_id"],
        "parameters": {
            "selected_candidate_id": None if overall_row is None else overall_row["candidate_id"],
            "gate_4_status": "recommended_pending_owner_approval",
            "threshold_final_test_validated": False,
        },
        "population": {
            "train_size": 5037,
            "validation_size": 9365,
            "engine_counts": {"train": 156, "validation": 52},
        },
        "metric": {
            "name": "minimum_primary_policy_engine_detection_coverage",
            "value": None
            if overall_row is None
            else overall_row["minimum_engine_detection_coverage"],
            "value_text": None
            if overall_row is None
            else format(float(overall_row["minimum_engine_detection_coverage"]), ".17g"),
        },
        "evidence_boundary": {
            "final_result": False,
            "threshold_selected": overall_row is not None,
            "held_out_internal_test_accessed": False,
            "threshold_final_test_validated": False,
            "gate_4_status": "recommended_pending_owner_approval",
        },
        "artifact": {
            "artifact_id": f"{overall_id}:recommendation_report",
            "path": repo_relative_posix(
                report_directory / "overall_recommendation.csv", repo_root
            ),
            "sha256": report_hashes["overall_recommendation.csv"],
            "present": True,
            "hash_form": "raw",
        },
        "notes": (
            "overall validation recommendation under the frozen feasibility/selection order; "
            "Gate 4 remains pending owner approval; not final-test-validated"
        ),
        "provenance": {
            "code_commit": code_commit,
            "protocol_sha256": protocol_sha256,
            "test_data_opened": False,
            "online_recalibration": False,
            "fusion_evaluated": False,
        },
    }
    validate_run_record(record)
    records.append(record)
    return records


def _atomically_extend_ledger(path: Path, records: list[dict[str, Any]]) -> None:
    existing = load_run_ledger(path)
    existing_ids = {record["run_id"] for record in existing}
    new_ids = {record["run_id"] for record in records}
    if existing_ids & new_ids:
        raise ValueError("Phase 5 ledger run IDs already exist")
    temporary = path.with_name(f".{path.name}.phase5.tmp")
    if temporary.exists():
        raise FileExistsError(f"Refusing stale temporary ledger: {temporary}")
    shutil.copyfile(path, temporary)
    try:
        for record in records:
            append_run_record(temporary, record)
        if len(load_run_ledger(temporary)) != len(existing) + len(records):
            raise RuntimeError("Temporary Phase 5 ledger count mismatch")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol.resolve()
    repo_root = find_repository_root(protocol_path.parent)
    protocol = _load_json(protocol_path)
    validate_alert_policy_protocol(protocol)
    if not _RUN_ID_PATTERN.fullmatch(args.run_id) or args.run_id != protocol["study_id"]:
        raise ValueError("This v1 protocol requires its registered study ID as run-id")
    ledger_path = args.ledger.resolve()
    if ledger_path != resolve_repo_path(protocol["outputs"]["ledger"], repo_root):
        raise ValueError("Phase 5 v1 must use the registered ledger path")
    existing_ledger = load_run_ledger(ledger_path)
    reserved = set(expected_alert_policy_ledger_run_ids(protocol["study_id"]))
    if reserved & {record["run_id"] for record in existing_ledger}:
        raise ValueError("Phase 5 ledger run IDs already exist")
    original_ledger = ledger_path.read_bytes()

    code_commit = _git_value(repo_root, "rev-parse", "HEAD")
    code_branch = _git_value(repo_root, "branch", "--show-current")
    working_tree_clean = (
        _git_value(repo_root, "status", "--porcelain=v2", "--untracked-files=all") == ""
    )
    if not working_tree_clean:
        raise RuntimeError("Phase 5 execution requires a clean worktree and index")
    protocol_sha256 = sha256_file(protocol_path)
    train_sequences, validation_sequences, train_metadata, validation_metadata = (
        load_allowed_inputs(protocol, repo_root)
    )
    device = _device(args.device)
    outputs = protocol["outputs"]
    model_directory = resolve_repo_path(outputs["model_directory"], repo_root)
    report_directory = resolve_repo_path(outputs["report_directory"], repo_root)
    result_path = resolve_repo_path(outputs["result_config"], repo_root)
    for path in (model_directory, report_directory, result_path):
        if path.exists():
            raise FileExistsError(f"Refusing existing Phase 5 output: {path}")
    model_base = model_directory.parent
    report_base = report_directory.parent
    model_base_existed = model_base.exists()
    report_base_existed = report_base.exists()
    model_base.mkdir(parents=True, exist_ok=True)
    report_base.mkdir(parents=True, exist_ok=True)
    started_clock = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    execution_time = started_at

    temporary_model: Path | None = None
    temporary_report: Path | None = None
    model_promoted = False
    report_promoted = False
    ledger_updated = False
    result_created = False
    try:
        temporary_model = Path(tempfile.mkdtemp(prefix=".pending-", dir=model_base))
        temporary_report = Path(tempfile.mkdtemp(prefix=".pending-", dir=report_base))
        training_frames, validation_frames, reproduction, bundle_hashes = (
            reproduce_score_sources(
                protocol=protocol,
                repo_root=repo_root,
                train_sequences=train_sequences,
                validation_sequences=validation_sequences,
                train_metadata=train_metadata,
                validation_metadata=validation_metadata,
                model_directory=temporary_model,
                device=device,
            )
        )
        tables = build_alert_study_tables(
            protocol=protocol,
            training_frames=training_frames,
            validation_frames=validation_frames,
            validation_metadata=validation_metadata,
        )
        tables["validation_score_reproduction_summary"] = reproduction
        tables["verification_summary"] = pd.DataFrame(
            [
                {
                    "score_sources_reproduced": int(reproduction["reproduced"].sum()),
                    "training_rows_per_source": 5037,
                    "validation_rows_per_source": 9365,
                    "operating_modes": 6,
                    "threshold_rows": len(tables["threshold_table"]),
                    "candidate_rows": len(tables["candidates"]),
                    "candidate_policy_rows": len(tables["candidate_policy_metrics"]),
                    "gate_4_status": "recommended_pending_owner_approval",
                    "test_data_opened": False,
                    "online_recalibration": False,
                    "fusion_evaluated": False,
                }
            ]
        )
        for name, frame in tables.items():
            _write_csv(frame, temporary_report / f"{name}.csv")
        pre_runtime_hashes = {
            path.name: sha256_file(path)
            for path in sorted(temporary_report.iterdir())
            if path.is_file()
        }
        runtime = {
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "scikit_learn_version": sklearn.__version__,
            "joblib_version": joblib.__version__,
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "operating_system": platform.platform(),
            "device": device.type,
            "gpu_name_when_available": (
                torch.cuda.get_device_name(0) if device.type == "cuda" else None
            ),
            "start_timestamp": started_at,
            "end_timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "duration_seconds": time.perf_counter() - started_clock,
            "code_commit": code_commit,
            "code_branch": code_branch,
            "working_tree_clean": working_tree_clean,
            "protocol_sha256": protocol_sha256,
            "input_sha256": {
                "sequences": {
                    split: protocol["inputs"]["sequences"][split]["sha256"]
                    for split in ALLOWED_SPLITS
                },
                "metadata": {
                    split: protocol["inputs"]["metadata"][split]["sha256"]
                    for split in ALLOWED_SPLITS
                },
                "final_lstm_models": {
                    seed: reference["sha256"]
                    for seed, reference in protocol["inputs"]["final_lstm_models"].items()
                },
            },
            "output_sha256": {
                "model_bundles": bundle_hashes,
                "reports_excluding_runtime_and_artifact_manifest": pre_runtime_hashes,
            },
            "test_data_opened": False,
            "online_recalibration": False,
            "fusion_evaluated": False,
        }
        missing_runtime = set(protocol["runtime_provenance_required"]) - set(runtime)
        if missing_runtime:
            raise RuntimeError(f"Runtime provenance is incomplete: {sorted(missing_runtime)}")
        _atomic_write_json(runtime, temporary_report / "runtime_provenance.json")
        manifest_rows = [
            {
                "artifact_type": "model_bundle",
                "artifact_id": detector_id,
                "path": repo_relative_posix(
                    model_directory
                    / (
                        "lstm_calibrated_ensemble.json"
                        if detector_id == "lstm_calibrated_ensemble"
                        else f"{detector_id}.joblib"
                    ),
                    repo_root,
                ),
                "sha256": bundle_hashes[detector_id],
                "tracked_by_git": False,
            }
            for detector_id in SCORE_SOURCE_ORDER
        ]
        manifest_rows.extend(
            {
                "artifact_type": "report",
                "artifact_id": path.stem,
                "path": repo_relative_posix(report_directory / path.name, repo_root),
                "sha256": sha256_file(path),
                "tracked_by_git": True,
            }
            for path in sorted(temporary_report.iterdir())
            if path.is_file()
        )
        _write_csv(pd.DataFrame(manifest_rows), temporary_report / "artifact_manifest.csv")
        report_hashes = {
            path.name: sha256_file(path)
            for path in sorted(temporary_report.iterdir())
            if path.is_file()
        }

        os.replace(temporary_model, model_directory)
        model_promoted = True
        os.replace(temporary_report, report_directory)
        report_promoted = True
        per_detector = tables["best_policy_per_detector"]
        overall = tables["overall_recommendation"]
        records = _ledger_records(
            protocol=protocol,
            protocol_path=protocol_path,
            protocol_sha256=protocol_sha256,
            repo_root=repo_root,
            execution_time=execution_time,
            code_commit=code_commit,
            per_detector=per_detector,
            overall=overall,
            report_hashes=report_hashes,
            bundle_hashes=bundle_hashes,
            model_directory=model_directory,
            report_directory=report_directory,
        )
        _atomically_extend_ledger(ledger_path, records)
        ledger_updated = True
        result = {
            "schema_version": "1.0.0",
            "study_id": protocol["study_id"],
            "run_id": args.run_id,
            "status": "completed",
            "result_classification": "validation_proxy_alert_policy_diagnostics_not_test_performance",
            "protocol_path": repo_relative_posix(protocol_path, repo_root),
            "protocol_sha256": protocol_sha256,
            "code_commit": code_commit,
            "execution_time": execution_time,
            "execution_device": device.type,
            "counts": {
                "score_sources": 5,
                "eligible_training_rows_per_source": 5037,
                "validation_rows_per_source": 9365,
                "operating_modes": 6,
                "threshold_rows": len(tables["threshold_table"]),
                "candidates": len(tables["candidates"]),
                "proxy_policies": 5,
                "candidate_policy_rows": len(tables["candidate_policy_metrics"]),
                "ledger_records_appended": len(records),
            },
            "score_reproduction": reproduction.to_dict(orient="records"),
            "best_policy_per_detector": per_detector.to_dict(orient="records"),
            "overall_recommendation": (
                None if overall.empty else overall.iloc[0].to_dict()
            ),
            "selection_status": "recommended_pending_owner_approval",
            "gate_4_status": "recommended_pending_owner_approval",
            "outputs": {
                "model_directory": repo_relative_posix(model_directory, repo_root),
                "model_bundle_sha256": bundle_hashes,
                "report_directory": repo_relative_posix(report_directory, repo_root),
                "report_sha256": report_hashes,
                "ledger_records_appended": len(records),
            },
            "test_data_opened": False,
            "online_recalibration": False,
            "fusion_evaluated": False,
            "final_result": False,
        }
        _atomic_write_json(result, result_path)
        result_created = True
        print(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "candidates": len(tables["candidates"]),
                    "candidate_policy_rows": len(tables["candidate_policy_metrics"]),
                    "selected_candidate_id": (
                        None if overall.empty else overall.iloc[0]["candidate_id"]
                    ),
                    "gate_4_status": "recommended_pending_owner_approval",
                    "test_data_opened": False,
                },
                sort_keys=True,
            ),
            flush=True,
        )
    except BaseException:
        rollback_error: BaseException | None = None
        if result_created and result_path.exists():
            result_path.unlink()
        if ledger_updated:
            rollback_path: Path | None = None
            try:
                descriptor, rollback_name = tempfile.mkstemp(
                    prefix=f".{ledger_path.name}.rollback-", dir=ledger_path.parent
                )
                os.close(descriptor)
                rollback_path = Path(rollback_name)
                rollback_path.write_bytes(original_ledger)
                os.replace(rollback_path, ledger_path)
            except BaseException as error:
                rollback_error = error
            finally:
                if rollback_path is not None and rollback_path.exists():
                    rollback_path.unlink()
        if report_promoted and report_directory.exists():
            shutil.rmtree(report_directory)
        if model_promoted and model_directory.exists():
            shutil.rmtree(model_directory)
        if rollback_error is not None:
            raise RuntimeError("Phase 5 ledger rollback failed") from rollback_error
        raise
    finally:
        if temporary_model is not None and temporary_model.exists():
            shutil.rmtree(temporary_model)
        if temporary_report is not None and temporary_report.exists():
            shutil.rmtree(temporary_report)
        if not model_base_existed and model_base.exists():
            try:
                model_base.rmdir()
            except OSError:
                pass
        if not report_base_existed and report_base.exists():
            try:
                report_base.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    main()
