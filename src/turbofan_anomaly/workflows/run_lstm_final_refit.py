"""Run the registered FD002 final LSTM refit on training/validation only."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import pandas as pd
import sklearn
import torch

from turbofan_anomaly.alerting.calibration import EmpiricalCDFCalibrator
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
from turbofan_anomaly.models.lstm_training import (
    FixedEpochSettings,
    LSTMArchitecture,
    TrainingSettings,
    aligned_calibrated_score_ensemble,
    engine_id_digest,
    ensure_output_paths_available,
    final_refit_artifact_name,
    fit_lstm_autoencoder,
    fit_lstm_autoencoder_fixed_epochs,
    load_lstm_artifact,
    median_locked_epoch,
    parameter_count,
    reconstruction_errors,
    save_lstm_artifact,
    split_eligible_training_windows,
    validate_sequence_collection,
)


ALLOWED_SPLITS = ("train", "validation")
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
        default=Path("configs/lstm/fd002-lstm-final-refit-protocol-v1.json"),
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Explicit versioned run ID; v1 requires fd002-lstm-final-refit-v1",
    )
    parser.add_argument(
        "--device", choices=["auto", "cpu", "cuda"], default="auto"
    )
    parser.add_argument(
        "--ledger", type=Path, default=Path("experiments/runs_v2.jsonl")
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def _atomic_write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing JSON output: {path}")
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise FileExistsError(f"Refusing stale temporary result: {temporary}")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def validate_allowed_split_name(split_name: str) -> str:
    """Enforce the registered final-refit split allow-list."""
    value = str(split_name)
    if value not in ALLOWED_SPLITS:
        raise ValueError(f"Split is not allowed by final-refit protocol: {value}")
    return value


def validate_allowed_input_path(path_value: str | Path, split_name: str) -> str:
    """Reject test-like inputs even when a caller supplies a valid split label."""
    split = validate_allowed_split_name(split_name)
    canonical = canonical_repo_relative(path_value)
    lowered = canonical.lower()
    if any(marker in lowered for marker in _FORBIDDEN_PATH_MARKERS):
        raise ValueError(f"Prohibited final-refit input path: {canonical}")
    filename = Path(canonical).name.lower()
    if split not in filename:
        raise ValueError(f"Input filename does not identify {split}: {canonical}")
    return canonical


def validate_final_refit_protocol(protocol: dict[str, Any]) -> None:
    """Validate the frozen decisions that may not drift at execution time."""
    if protocol.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported final-refit protocol schema")
    if protocol.get("study_id") != "fd002-lstm-final-refit-v1":
        raise ValueError("Unexpected final-refit study ID")
    if protocol.get("status") != "registered_before_execution":
        raise RuntimeError("Final-refit protocol is not registered for execution")
    boundary = protocol["evidence_boundary"]
    if boundary["allowed_splits"] != ["train", "validation"]:
        raise RuntimeError("Final-refit split allow-list changed")
    if not {"held_out_internal_test", "official_nasa_test"}.issubset(
        boundary["prohibited_inputs"]
    ):
        raise RuntimeError("Final-refit prohibited input policy is incomplete")
    forbidden_flags = (
        "test_data_may_be_opened",
        "validation_controls_gradient_updates",
        "validation_controls_early_stopping",
        "validation_controls_seed_choice",
        "validation_controls_epoch_choice",
        "threshold_selection_authorized",
        "phase_5_authorized",
    )
    if any(bool(boundary[field]) for field in forbidden_flags):
        raise RuntimeError("Final-refit evidence boundary was weakened")

    architecture = protocol["architecture"]
    expected_architecture = {
        "architecture_id": "balanced_64x16_l1",
        "hidden_dim": 64,
        "latent_dim": 16,
        "num_layers": 1,
        "dropout": 0.0,
        "parameter_count": 59045,
    }
    if architecture != expected_architecture:
        raise RuntimeError("Final-refit architecture differs from Gate 3 approval")
    if protocol["inputs"]["pipeline"] != "p1_k6":
        raise RuntimeError("Final refit may use only P1/K=6 sequences")
    if protocol["window_contract"] != {
        "shape": [30, 21],
        "eligible_training_windows": 5037,
        "validation_windows": 9365,
        "training_engines": 156,
        "validation_engines": 52,
        "train_validation_engine_overlap": 0,
    }:
        raise RuntimeError("Final-refit window contract differs from registration")
    if tuple(protocol["convergence_selection"]["seeds"]) != REGISTERED_SEEDS:
        raise RuntimeError("Convergence seeds differ from registration")
    if tuple(protocol["locked_refit"]["seeds"]) != REGISTERED_SEEDS:
        raise RuntimeError("Locked-refit seeds differ from registration")
    optimization = protocol["optimization"]
    expected_controls = {
        "batch_size": 128,
        "maximum_epochs": 150,
        "minimum_epochs": 20,
        "early_stopping_patience": 15,
        "minimum_improvement": 0.00001,
        "learning_rate": 0.001,
        "weight_decay": 0.00001,
        "gradient_clipping_norm": 1.0,
    }
    if any(optimization[key] != value for key, value in expected_controls.items()):
        raise RuntimeError("Optimization controls differ from registration")
    expected_template = final_refit_artifact_name(43).replace("seed43", "seed{seed}")
    if protocol["outputs"]["artifact_name_template"] != expected_template:
        raise RuntimeError("Final-refit artifact name template differs from registration")
    for split in ALLOWED_SPLITS:
        validate_allowed_input_path(
            protocol["inputs"]["sequences"][split]["path"], split
        )
        validate_allowed_input_path(
            protocol["inputs"]["metadata"][split]["path"], split
        )


def _device(choice: str) -> torch.device:
    if choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable")
        return torch.device("cuda")
    if choice == "cpu":
        return torch.device("cpu")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _verify_reference(reference: dict[str, Any], repo_root: Path) -> Path:
    path = resolve_repo_path(reference["path"], repo_root)
    verification = verify_registered_hash(path, reference["sha256"])
    if verification.match_form != reference["hash_form"]:
        raise RuntimeError(
            f"Registered hash form mismatch for {reference['path']}: "
            f"expected {reference['hash_form']}, observed {verification.match_form}"
        )
    return path


def _load_allowed_inputs(
    protocol: dict[str, Any], repo_root: Path
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame, pd.DataFrame]:
    inputs = protocol["inputs"]
    for authority in (
        "split_manifest",
        "preprocessing_selection",
        "screen_protocol",
        "screen_results",
    ):
        _verify_reference(inputs[authority], repo_root)
    _verify_reference(protocol["registered_classical_comparison"]["source_report"], repo_root)

    paths: dict[tuple[str, str], Path] = {}
    for kind in ("sequences", "metadata"):
        for split in ALLOWED_SPLITS:
            reference = inputs[kind][split]
            validate_allowed_input_path(reference["path"], split)
            paths[(kind, split)] = _verify_reference(reference, repo_root)

    train_metadata = pd.read_csv(paths[("metadata", "train")])
    validation_metadata = pd.read_csv(paths[("metadata", "validation")])
    train_sequences = np.load(
        paths[("sequences", "train")], allow_pickle=False, mmap_mode="r"
    )
    validation_sequences = np.load(
        paths[("sequences", "validation")], allow_pickle=False, mmap_mode="r"
    )

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
    if len(validation_metadata) != len(validation_sequences):
        raise RuntimeError("Validation sequence/metadata lengths differ")

    required_metadata = {
        "window_id",
        "engine",
        "start_cycle",
        "end_cycle",
        "max_cycle",
        "split",
        "split_manifest_id",
    }
    for frame, split in (
        (train_metadata, "train"),
        (validation_metadata, "validation"),
    ):
        missing = required_metadata - set(frame.columns)
        if missing:
            raise ValueError(f"Missing {split} metadata columns: {sorted(missing)}")
        if set(frame["split"].astype(str)) != {split}:
            raise RuntimeError(f"Unexpected {split} metadata split value")
        if set(frame["split_manifest_id"].astype(str)) != {"fd002-primary-v1"}:
            raise RuntimeError(f"Unexpected {split} metadata manifest identity")
        if frame["window_id"].isna().any() or frame["window_id"].duplicated().any():
            raise RuntimeError(f"{split} metadata window IDs are not unique")

    train_engines = set(train_metadata["engine"].astype(int))
    validation_engines = set(validation_metadata["engine"].astype(int))
    if train_engines & validation_engines:
        raise RuntimeError("Training and validation engines overlap")
    if len(train_engines) != 156 or len(validation_engines) != 52:
        raise RuntimeError("Unexpected train/validation engine count")
    return train_sequences, validation_sequences, train_metadata, validation_metadata


def _git_value(repo_root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args], cwd=repo_root, check=True, capture_output=True
    )
    return process.stdout.decode("utf-8").strip()


def _runtime_provenance(
    *,
    repo_root: Path,
    device: torch.device,
    started_at: str,
    started_clock: float,
    code_commit: str,
    code_branch: str,
    working_tree_clean: bool,
) -> dict[str, Any]:
    ended_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status = _git_value(repo_root, "status", "--porcelain=v2", "--untracked-files=all")
    return {
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scikit_learn_version": sklearn.__version__,
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "operating_system": platform.platform(),
        "device": device.type,
        "gpu_name_when_available": (
            torch.cuda.get_device_name(0) if device.type == "cuda" else None
        ),
        "start_timestamp": started_at,
        "end_timestamp": ended_at,
        "duration_seconds": time.perf_counter() - started_clock,
        "code_commit": code_commit,
        "code_branch": code_branch,
        "working_tree_clean": working_tree_clean,
        "working_tree_clean_at_report_write": status == "",
        "deterministic_flags": {
            "torch_deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "cudnn_deterministic": torch.backends.cudnn.deterministic,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
            "dataloader_num_workers": 0,
            "drop_last": False,
        },
        "test_data_opened": False,
    }


def expected_final_refit_ledger_run_ids(study_id: str) -> tuple[str, ...]:
    """Return the seven deterministic run IDs reserved by this protocol."""
    return (
        *(f"{study_id}_convergence_seed{seed}" for seed in REGISTERED_SEEDS),
        *(f"{study_id}_locked_seed{seed}" for seed in REGISTERED_SEEDS),
        f"{study_id}_calibrated_ensemble",
    )


def _ledger_records(
    *,
    protocol: dict[str, Any],
    protocol_path: Path,
    protocol_sha256: str,
    repo_root: Path,
    execution_time: str,
    convergence_rows: list[dict[str, Any]],
    locked_rows: list[dict[str, Any]],
    ensemble_row: dict[str, Any],
    model_hashes: dict[int, str],
    report_hashes: dict[str, str],
    final_model_dir: Path,
    final_report_dir: Path,
    code_commit: str,
) -> list[dict[str, Any]]:
    split = protocol["inputs"]["split_manifest"]
    config = {
        "study_id": protocol["study_id"],
        "path": repo_relative_posix(protocol_path, repo_root),
        "sha256": protocol_sha256,
        "hash_form": "raw",
    }
    boundary = {
        "final_result": False,
        "threshold_selected": False,
        "held_out_internal_test_accessed": False,
    }
    run_provenance = {
        "code_commit": code_commit,
        "protocol_sha256": protocol_sha256,
        "input_sha256": {
            split_name: {
                "sequences": protocol["inputs"]["sequences"][split_name]["sha256"],
                "metadata": protocol["inputs"]["metadata"][split_name]["sha256"],
            }
            for split_name in ALLOWED_SPLITS
        },
        "test_data_opened": False,
    }
    common = {
        "schema_version": "2.0.0",
        "timestamp": execution_time,
        "owner": protocol["owner"],
        "model": "lstm_autoencoder",
        "evidence_class": "validation_proxy_only",
        "evidence_boundary": boundary,
        "split": {
            "manifest_id": split["manifest_id"],
            "path": split["path"],
            "sha256": split["sha256"],
            "hash_form": split["hash_form"],
        },
        "config": config,
    }
    records: list[dict[str, Any]] = []
    convergence_report = final_report_dir / "convergence_summary.csv"
    for row in convergence_rows:
        run_id = f"{protocol['study_id']}_convergence_seed{row['seed']}"
        record = {
            **common,
            "run_id": run_id,
            "source_run_id": run_id,
            "experiment_name": "lstm_final_refit_convergence_selection",
            "parameters": {
                "seed": row["seed"],
                "architecture": protocol["architecture"]["architecture_id"],
                "pipeline": "p1_k6",
                "maximum_epochs": protocol["optimization"]["maximum_epochs"],
            },
            "population": {
                "train_size": 3988,
                "monitor_size": 1049,
                "validation_size": 0,
                "engine_counts": {"development": 124, "monitor": 32},
            },
            "metric": {
                "name": "best_monitor_reconstruction_loss",
                "value": row["best_monitor_loss"],
                "value_text": format(row["best_monitor_loss"], ".17g"),
            },
            "result_classification": "training_only_convergence_selection",
            "artifact": {
                "artifact_id": f"{run_id}:convergence_summary",
                "path": repo_relative_posix(convergence_report, repo_root),
                "sha256": report_hashes["convergence_summary.csv"],
                "present": True,
                "hash_form": "raw",
            },
            "notes": (
                "training-only engine-disjoint convergence selection; "
                "validation not scored; no threshold or test access"
            ),
            "provenance": dict(run_provenance),
        }
        validate_run_record(record)
        records.append(record)

    for row in locked_rows:
        seed = int(row["seed"])
        run_id = f"{protocol['study_id']}_locked_seed{seed}"
        artifact_path = final_model_dir / final_refit_artifact_name(seed)
        record = {
            **common,
            "run_id": run_id,
            "source_run_id": run_id,
            "experiment_name": "lstm_final_refit_locked_training",
            "parameters": {
                "seed": seed,
                "architecture": protocol["architecture"]["architecture_id"],
                "pipeline": "p1_k6",
                "locked_epoch_count": row["locked_epoch_count"],
            },
            "population": {
                "train_size": 5037,
                "validation_size": 9365,
                "engine_counts": {"train": 156, "validation": 52},
            },
            "metric": {
                "name": "mean_validation_pr_auc_endpoint_policies",
                "value": row["selection_mean_pr_auc"],
                "value_text": format(row["selection_mean_pr_auc"], ".17g"),
            },
            "result_classification": "validation_proxy_diagnostic_not_test_performance",
            "artifact": {
                "artifact_id": run_id,
                "path": repo_relative_posix(artifact_path, repo_root),
                "sha256": model_hashes[seed],
                "present": True,
                "hash_form": "raw",
            },
            "supporting_report": {
                "path": repo_relative_posix(
                    final_report_dir / "ranking_metrics.csv", repo_root
                ),
                "sha256": report_hashes["ranking_metrics.csv"],
                "present": True,
                "hash_form": "raw",
            },
            "notes": (
                "locked refit on all eligible training windows; training-fitted CDF; "
                "validation proxy diagnostic; no threshold or test access"
            ),
            "provenance": dict(run_provenance),
        }
        validate_run_record(record)
        records.append(record)

    ensemble_id = f"{protocol['study_id']}_calibrated_ensemble"
    ensemble_report = final_report_dir / "ensemble_validation_scores.csv"
    record = {
        **common,
        "run_id": ensemble_id,
        "source_run_id": ensemble_id,
        "experiment_name": "lstm_final_refit_calibrated_ensemble",
        "parameters": {
            "seeds": list(REGISTERED_SEEDS),
            "aggregation": "arithmetic_mean_per_seed_calibrated_scores",
            "alignment_key": "window_id",
        },
        "population": {
            "train_size": 5037,
            "validation_size": 9365,
            "engine_counts": {"train": 156, "validation": 52},
        },
        "metric": {
            "name": "mean_validation_pr_auc_endpoint_policies",
            "value": ensemble_row["selection_mean_pr_auc"],
            "value_text": format(ensemble_row["selection_mean_pr_auc"], ".17g"),
        },
        "result_classification": "validation_proxy_diagnostic_not_test_performance",
        "artifact": {
            "artifact_id": ensemble_id,
            "path": repo_relative_posix(ensemble_report, repo_root),
            "sha256": report_hashes["ensemble_validation_scores.csv"],
            "present": True,
            "hash_form": "raw",
        },
        "notes": (
            "predeclared window-ID-aligned mean of three calibrated seed scores; "
            "no best-seed choice; no threshold or test access"
        ),
        "provenance": dict(run_provenance),
    }
    validate_run_record(record)
    records.append(record)
    return records


def _atomically_extend_ledger(
    ledger_path: Path, records: list[dict[str, Any]]
) -> None:
    existing = load_run_ledger(ledger_path)
    existing_ids = {record["run_id"] for record in existing}
    if existing_ids & {record["run_id"] for record in records}:
        raise ValueError("Final-refit ledger run IDs already exist")
    temporary = ledger_path.with_name(f".{ledger_path.name}.final-refit.tmp")
    if temporary.exists():
        raise FileExistsError(f"Refusing stale temporary ledger: {temporary}")
    shutil.copyfile(ledger_path, temporary)
    try:
        for record in records:
            append_run_record(temporary, record)
        if len(load_run_ledger(temporary)) != len(existing) + len(records):
            raise RuntimeError("Temporary final-refit ledger count mismatch")
        os.replace(temporary, ledger_path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol.resolve()
    repo_root = find_repository_root(protocol_path.parent)
    protocol = _load_json(protocol_path)
    validate_final_refit_protocol(protocol)
    if not _RUN_ID_PATTERN.fullmatch(args.run_id):
        raise ValueError("run-id must be a lowercase versioned identifier")
    if args.run_id != protocol["study_id"]:
        raise ValueError("This v1 protocol requires its registered study ID as run-id")

    code_commit = _git_value(repo_root, "rev-parse", "HEAD")
    code_branch = _git_value(repo_root, "branch", "--show-current")
    working_tree_clean = (
        _git_value(repo_root, "status", "--porcelain=v2", "--untracked-files=all")
        == ""
    )
    ledger_path = args.ledger.resolve()
    if ledger_path != (repo_root / "experiments/runs_v2.jsonl").resolve():
        raise ValueError("Final-refit v1 must use the registered ledger path")
    existing_ledger = load_run_ledger(ledger_path)
    reserved_run_ids = set(expected_final_refit_ledger_run_ids(protocol["study_id"]))
    if reserved_run_ids & {record["run_id"] for record in existing_ledger}:
        raise ValueError("Final-refit ledger run IDs already exist")
    original_ledger_bytes = ledger_path.read_bytes()

    protocol_sha256 = sha256_file(protocol_path)
    train_sequences, validation_sequences, train_metadata, validation_metadata = (
        _load_allowed_inputs(protocol, repo_root)
    )
    healthy_fraction = float(protocol["healthy_training_assumption"]["fraction"])
    eligible = training_eligible_windows(train_metadata, healthy_fraction).to_numpy(
        dtype=bool
    )
    if int(eligible.sum()) != 5037:
        raise RuntimeError("Expected exactly 5,037 eligible training windows")

    convergence = protocol["convergence_selection"]
    development_mask, monitor_mask, assignment = split_eligible_training_windows(
        train_metadata,
        eligible,
        monitor_fraction=float(convergence["monitor_fraction"]),
        random_state=int(convergence["assignment_random_state"]),
        n_strata=int(convergence["n_strata"]),
    )
    development_engines = sorted(
        assignment.loc[assignment["role"] == "development", "engine"]
        .astype(int)
        .tolist()
    )
    monitor_engines = sorted(
        assignment.loc[assignment["role"] == "monitor", "engine"]
        .astype(int)
        .tolist()
    )
    if set(development_engines) & set(monitor_engines):
        raise RuntimeError("Development and monitor engines overlap")
    expected_development = convergence["expected_development"]
    expected_monitor = convergence["expected_monitor"]
    if (
        int(development_mask.sum()) != expected_development["window_count"]
        or len(development_engines) != expected_development["engine_count"]
        or engine_id_digest(development_engines)
        != expected_development["engine_ids_sha256"]
    ):
        raise RuntimeError("Registered development assignment does not reproduce")
    if (
        int(monitor_mask.sum()) != expected_monitor["window_count"]
        or len(monitor_engines) != expected_monitor["engine_count"]
        or engine_id_digest(monitor_engines) != expected_monitor["engine_ids_sha256"]
    ):
        raise RuntimeError("Registered monitor assignment does not reproduce")

    outputs = protocol["outputs"]
    model_base = resolve_repo_path(outputs["model_directory"], repo_root)
    report_base = resolve_repo_path(outputs["report_directory"], repo_root)
    final_model_dir = model_base / args.run_id
    final_report_dir = report_base / args.run_id
    result_path = resolve_repo_path(outputs["result_config"], repo_root)
    ensure_output_paths_available([final_model_dir, final_report_dir, result_path])
    model_base_existed = model_base.exists()
    report_base_existed = report_base.exists()
    model_base.mkdir(parents=True, exist_ok=True)
    report_base.mkdir(parents=True, exist_ok=True)

    started_clock = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    execution_time = started_at
    device = _device(args.device)
    artifact_runtime_identity = {
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scikit_learn_version": sklearn.__version__,
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "operating_system": platform.platform(),
        "device": device.type,
        "gpu_name_when_available": (
            torch.cuda.get_device_name(0) if device.type == "cuda" else None
        ),
        "start_timestamp": started_at,
        "code_commit": code_commit,
        "code_branch": code_branch,
        "working_tree_clean": working_tree_clean,
    }
    architecture_values = protocol["architecture"]
    architecture = LSTMArchitecture(
        architecture_id=architecture_values["architecture_id"],
        hidden_dim=int(architecture_values["hidden_dim"]),
        latent_dim=int(architecture_values["latent_dim"]),
        num_layers=int(architecture_values["num_layers"]),
        dropout=float(architecture_values["dropout"]),
    )
    if parameter_count(architecture.build(21)) != 59045:
        raise RuntimeError("Approved architecture parameter count changed")
    optimization = protocol["optimization"]
    convergence_settings = TrainingSettings(
        batch_size=int(optimization["batch_size"]),
        max_epochs=int(optimization["maximum_epochs"]),
        minimum_epochs=int(optimization["minimum_epochs"]),
        patience=int(optimization["early_stopping_patience"]),
        min_delta=float(optimization["minimum_improvement"]),
        learning_rate=float(optimization["learning_rate"]),
        weight_decay=float(optimization["weight_decay"]),
        gradient_clip_norm=float(optimization["gradient_clipping_norm"]),
    )

    convergence_rows: list[dict[str, Any]] = []
    convergence_history: list[dict[str, Any]] = []
    locked_rows: list[dict[str, Any]] = []
    locked_history: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    seed_score_frames: dict[int, pd.DataFrame] = {}
    verification_rows: list[dict[str, Any]] = []
    model_hashes: dict[int, str] = {}
    temporary_model_dir: Path | None = None
    temporary_report_dir: Path | None = None
    model_promoted = False
    report_promoted = False
    ledger_updated = False
    result_created = False
    try:
        temporary_model_dir = Path(
            tempfile.mkdtemp(prefix=".pending-", dir=model_base)
        )
        temporary_report_dir = Path(
            tempfile.mkdtemp(prefix=".pending-", dir=report_base)
        )
        for seed in REGISTERED_SEEDS:
            fit = fit_lstm_autoencoder(
                train_sequences[development_mask],
                train_sequences[monitor_mask],
                architecture=architecture,
                settings=convergence_settings,
                seed=seed,
                device=device,
            )
            convergence_rows.append(
                {
                    "seed": seed,
                    "epochs_completed": len(fit.history),
                    "best_epoch": fit.best_epoch,
                    "best_monitor_loss": fit.best_monitor_loss,
                }
            )
            convergence_history.extend(
                {"seed": seed, **row} for row in fit.history
            )

        locked_epoch_count = median_locked_epoch(
            [row["best_epoch"] for row in convergence_rows]
        )
        fixed_settings = FixedEpochSettings(
            batch_size=int(optimization["batch_size"]),
            epoch_count=locked_epoch_count,
            learning_rate=float(optimization["learning_rate"]),
            weight_decay=float(optimization["weight_decay"]),
            gradient_clip_norm=float(optimization["gradient_clipping_norm"]),
        )
        policy_frames = [
            policy.apply(validation_metadata)
            for policy in registered_validation_policies()
        ]
        eligible_sequences = train_sequences[eligible]
        for seed in REGISTERED_SEEDS:
            fixed = fit_lstm_autoencoder_fixed_epochs(
                eligible_sequences,
                architecture=architecture,
                settings=fixed_settings,
                seed=seed,
                device=device,
            )
            locked_history.extend({"seed": seed, **row} for row in fixed.history)
            training_raw = reconstruction_errors(
                fixed.model,
                eligible_sequences,
                batch_size=fixed_settings.batch_size,
                device=device,
            )
            calibrator = EmpiricalCDFCalibrator().fit(training_raw)
            validation_raw = reconstruction_errors(
                fixed.model,
                validation_sequences,
                batch_size=fixed_settings.batch_size,
                device=device,
            )
            validation_calibrated = calibrator.transform(validation_raw)
            metrics, mean_pr, mean_roc = proxy_ranking_metrics(
                validation_calibrated, policy_frames
            )
            locked_rows.append(
                {
                    "seed": seed,
                    "locked_epoch_count": locked_epoch_count,
                    "final_training_loss": fixed.history[-1]["training_loss"],
                    "selection_mean_pr_auc": mean_pr,
                    "selection_mean_roc_auc": mean_roc,
                }
            )
            ranking_rows.extend(
                {"score_source": f"lstm_seed_{seed}", "seed": seed, **row}
                for row in metrics
            )
            score_frame = validation_metadata[
                ["window_id", "engine", "start_cycle", "end_cycle", "max_cycle"]
            ].copy()
            if "op_mode" in validation_metadata:
                score_frame["op_mode"] = validation_metadata["op_mode"].to_numpy()
            score_frame.insert(0, "seed", seed)
            score_frame["raw_reconstruction_error"] = validation_raw
            score_frame["calibrated_score"] = validation_calibrated
            seed_score_frames[seed] = score_frame

            artifact_path = temporary_model_dir / final_refit_artifact_name(seed)
            metadata = {
                "study_id": protocol["study_id"],
                "run_id": args.run_id,
                "seed": seed,
                "pipeline": "p1_k6",
                "split_manifest_id": "fd002-primary-v1",
                "preprocessing_decision_id": "fd002-preprocessing-selection-v1",
                "input_dim": 21,
                "window_size": 30,
                "architecture": asdict(architecture),
                "fixed_epoch_settings": asdict(fixed_settings),
                "eligible_training_window_count": 5037,
                "training_engine_count": 156,
                "validation_engine_count": 52,
                "score_calibration": "empirical_cdf_fitted_on_all_eligible_training_scores",
                "protocol_sha256": protocol_sha256,
                "runtime_identity": {
                    **artifact_runtime_identity,
                    "deterministic_flags": {
                        "torch_deterministic_algorithms": (
                            torch.are_deterministic_algorithms_enabled()
                        ),
                        "cudnn_deterministic": torch.backends.cudnn.deterministic,
                        "cudnn_benchmark": torch.backends.cudnn.benchmark,
                        "cublas_workspace_config": os.environ.get(
                            "CUBLAS_WORKSPACE_CONFIG"
                        ),
                        "dataloader_num_workers": 0,
                        "drop_last": False,
                    },
                },
                "input_sha256": {
                    split: {
                        "sequences": protocol["inputs"]["sequences"][split][
                            "sha256"
                        ],
                        "metadata": protocol["inputs"]["metadata"][split]["sha256"],
                    }
                    for split in ALLOWED_SPLITS
                },
                "result_classification": "validation_proxy_diagnostic_not_test_performance",
                "test_data_opened": False,
            }
            save_lstm_artifact(
                fixed.model, architecture, training_raw, metadata, artifact_path
            )

            reloaded, reference, reloaded_metadata = load_lstm_artifact(
                artifact_path,
                expected_split_manifest_id="fd002-primary-v1",
                expected_preprocessing_decision_id=(
                    "fd002-preprocessing-selection-v1"
                ),
            )
            reloaded = reloaded.to(device)
            reproduced_raw = reconstruction_errors(
                reloaded,
                validation_sequences,
                batch_size=fixed_settings.batch_size,
                device=device,
            )
            reproduced_calibrated = np.searchsorted(
                reference, reproduced_raw, side="right"
            ).astype(float) / len(reference)
            raw_difference = float(np.max(np.abs(reproduced_raw - validation_raw)))
            calibrated_difference = float(
                np.max(np.abs(reproduced_calibrated - validation_calibrated))
            )
            tolerances = protocol["reload_verification"]
            if not np.allclose(
                reproduced_raw,
                validation_raw,
                rtol=tolerances["raw_scores"]["relative_tolerance"],
                atol=tolerances["raw_scores"]["absolute_tolerance"],
            ):
                raise RuntimeError(f"Raw reload scores do not reproduce for seed {seed}")
            if not np.allclose(
                reproduced_calibrated,
                validation_calibrated,
                rtol=tolerances["calibrated_scores"]["relative_tolerance"],
                atol=tolerances["calibrated_scores"]["absolute_tolerance"],
            ):
                raise RuntimeError(
                    f"Calibrated reload scores do not reproduce for seed {seed}"
                )
            if reloaded_metadata != metadata:
                raise RuntimeError(f"Artifact metadata changed for seed {seed}")
            verification_rows.append(
                {
                    "seed": seed,
                    "raw_maximum_absolute_difference": raw_difference,
                    "calibrated_maximum_absolute_difference": calibrated_difference,
                    "validation_score_rows": len(validation_raw),
                    "verified": True,
                }
            )
            model_hashes[seed] = sha256_file(artifact_path)

        ensemble = aligned_calibrated_score_ensemble(seed_score_frames)
        validation_ids = validation_metadata["window_id"].tolist()
        ensemble_indexed = ensemble.set_index("window_id")
        ensemble_scores = ensemble_indexed.loc[
            validation_ids, "ensemble_calibrated_score"
        ].to_numpy(dtype=float)
        ensemble_metrics, ensemble_pr, ensemble_roc = proxy_ranking_metrics(
            ensemble_scores, policy_frames
        )
        ensemble_row = {
            "score_source": "lstm_calibrated_ensemble",
            "seed": None,
            "selection_mean_pr_auc": ensemble_pr,
            "selection_mean_roc_auc": ensemble_roc,
        }
        ranking_rows.extend(
            {"score_source": "lstm_calibrated_ensemble", "seed": None, **row}
            for row in ensemble_metrics
        )
        ensemble_output = validation_metadata[
            ["window_id", "engine", "start_cycle", "end_cycle", "max_cycle"]
        ].merge(ensemble, on="window_id", how="left", validate="one_to_one")
        if len(ensemble_output) != 9365 or ensemble_output.isna().any().any():
            raise RuntimeError("Ensemble output is incomplete after window-ID alignment")

        classical_path = _verify_reference(
            protocol["registered_classical_comparison"]["source_report"], repo_root
        )
        classical = pd.read_csv(classical_path)
        classical = classical[classical["pipeline"] == "p1_k6"]
        required_detectors = {
            "lof",
            "one_class_svm",
            "isolation_forest",
            "pca",
        }
        if set(classical["detector"]) != required_detectors:
            raise RuntimeError("Registered P1 classical control set changed")
        comparison = classical[
            ["detector", "selection_mean_pr_auc", "selection_mean_roc_auc"]
        ].copy()
        comparison.insert(0, "score_source", "registered_p1_classical")
        comparison["seed"] = pd.NA
        comparison["result_classification"] = "validation_proxy_diagnostic"
        lstm_comparison = pd.DataFrame(
            [
                {
                    "score_source": "final_lstm_seed",
                    "detector": "lstm_autoencoder",
                    "seed": row["seed"],
                    "selection_mean_pr_auc": row["selection_mean_pr_auc"],
                    "selection_mean_roc_auc": row["selection_mean_roc_auc"],
                    "result_classification": "validation_proxy_diagnostic",
                }
                for row in locked_rows
            ]
            + [
                {
                    "score_source": "final_lstm_calibrated_ensemble",
                    "detector": "lstm_autoencoder",
                    "seed": pd.NA,
                    "selection_mean_pr_auc": ensemble_pr,
                    "selection_mean_roc_auc": ensemble_roc,
                    "result_classification": "validation_proxy_diagnostic",
                }
            ]
        )
        comparison = pd.concat([comparison, lstm_comparison], ignore_index=True)

        assignment.to_csv(
            temporary_report_dir / "convergence_engine_assignment.csv", index=False
        )
        pd.DataFrame(convergence_history).to_csv(
            temporary_report_dir / "convergence_history.csv", index=False
        )
        pd.DataFrame(convergence_rows).to_csv(
            temporary_report_dir / "convergence_summary.csv", index=False
        )
        pd.DataFrame(
            [
                {
                    "seed_43_best_epoch": convergence_rows[0]["best_epoch"],
                    "seed_44_best_epoch": convergence_rows[1]["best_epoch"],
                    "seed_45_best_epoch": convergence_rows[2]["best_epoch"],
                    "rule": "median_of_three_convergence_best_epochs",
                    "locked_epoch_count": locked_epoch_count,
                }
            ]
        ).to_csv(temporary_report_dir / "epoch_lock.csv", index=False)
        pd.DataFrame(locked_history).to_csv(
            temporary_report_dir / "locked_refit_training_history.csv", index=False
        )
        pd.DataFrame(locked_rows).to_csv(
            temporary_report_dir / "run_summary.csv", index=False
        )
        pd.concat(seed_score_frames.values(), ignore_index=True).to_csv(
            temporary_report_dir / "validation_scores.csv", index=False
        )
        ensemble_output.to_csv(
            temporary_report_dir / "ensemble_validation_scores.csv", index=False
        )
        pd.DataFrame(ranking_rows).to_csv(
            temporary_report_dir / "ranking_metrics.csv", index=False
        )
        comparison.to_csv(
            temporary_report_dir / "classical_comparison.csv", index=False
        )
        pd.DataFrame(verification_rows).to_csv(
            temporary_report_dir / "reload_verification.csv", index=False
        )
        pd.DataFrame(
            [
                {
                    "seed": seed,
                    "artifact_path": repo_relative_posix(
                        final_model_dir / final_refit_artifact_name(seed), repo_root
                    ),
                    "sha256": model_hashes[seed],
                }
                for seed in REGISTERED_SEEDS
            ]
        ).to_csv(temporary_report_dir / "artifact_manifest.csv", index=False)

        runtime = _runtime_provenance(
            repo_root=repo_root,
            device=device,
            started_at=started_at,
            started_clock=started_clock,
            code_commit=code_commit,
            code_branch=code_branch,
            working_tree_clean=working_tree_clean,
        )
        runtime["protocol_sha256"] = protocol_sha256
        runtime["input_sha256"] = {
            split: {
                "sequences": protocol["inputs"]["sequences"][split]["sha256"],
                "metadata": protocol["inputs"]["metadata"][split]["sha256"],
            }
            for split in ALLOWED_SPLITS
        }
        pre_runtime_report_hashes = {
            path.name: sha256_file(path)
            for path in sorted(temporary_report_dir.iterdir())
            if path.is_file()
        }
        runtime["output_sha256"] = {
            "model_artifacts": {
                str(seed): model_hashes[seed] for seed in REGISTERED_SEEDS
            },
            "reports_excluding_runtime_provenance": pre_runtime_report_hashes,
        }
        missing_runtime_fields = set(protocol["runtime_provenance_required"]) - set(
            runtime
        )
        if missing_runtime_fields:
            raise RuntimeError(
                "Runtime provenance is missing required fields: "
                f"{sorted(missing_runtime_fields)}"
            )
        _atomic_write_json(
            runtime, temporary_report_dir / "runtime_provenance.json"
        )
        report_hashes = {
            path.name: sha256_file(path)
            for path in sorted(temporary_report_dir.iterdir())
            if path.is_file()
        }

        os.replace(temporary_model_dir, final_model_dir)
        model_promoted = True
        os.replace(temporary_report_dir, final_report_dir)
        report_promoted = True
        records = _ledger_records(
            protocol=protocol,
            protocol_path=protocol_path,
            protocol_sha256=protocol_sha256,
            repo_root=repo_root,
            execution_time=execution_time,
            convergence_rows=convergence_rows,
            locked_rows=locked_rows,
            ensemble_row=ensemble_row,
            model_hashes=model_hashes,
            report_hashes=report_hashes,
            final_model_dir=final_model_dir,
            final_report_dir=final_report_dir,
            code_commit=code_commit,
        )
        _atomically_extend_ledger(ledger_path, records)
        ledger_updated = True

        result = {
            "schema_version": "1.0.0",
            "study_id": protocol["study_id"],
            "run_id": args.run_id,
            "status": "completed",
            "protocol_path": repo_relative_posix(protocol_path, repo_root),
            "protocol_sha256": protocol_sha256,
            "code_commit": code_commit,
            "execution_time": execution_time,
            "execution_device": device.type,
            "architecture": asdict(architecture),
            "convergence_best_epochs": {
                str(row["seed"]): row["best_epoch"] for row in convergence_rows
            },
            "locked_epoch_count": locked_epoch_count,
            "completed_locked_refits": 3,
            "ensemble": ensemble_row,
            "outputs": {
                "model_directory": repo_relative_posix(final_model_dir, repo_root),
                "model_sha256": {
                    str(seed): model_hashes[seed] for seed in REGISTERED_SEEDS
                },
                "report_directory": repo_relative_posix(final_report_dir, repo_root),
                "report_sha256": report_hashes,
                "ledger_records_appended": len(records),
            },
            "reload_verification": {
                "verified_artifacts": 3,
                "maximum_raw_absolute_difference": max(
                    row["raw_maximum_absolute_difference"]
                    for row in verification_rows
                ),
                "maximum_calibrated_absolute_difference": max(
                    row["calibrated_maximum_absolute_difference"]
                    for row in verification_rows
                ),
            },
            "result_classification": "validation_proxy_diagnostic_not_test_performance",
            "threshold_selected": False,
            "test_data_opened": False,
        }
        _atomic_write_json(result, result_path)
        result_created = True
        print(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "locked_epoch_count": locked_epoch_count,
                    "completed_locked_refits": 3,
                    "ledger_records_appended": len(records),
                    "result_config": repo_relative_posix(result_path, repo_root),
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
                    prefix=f".{ledger_path.name}.rollback-",
                    dir=ledger_path.parent,
                )
                os.close(descriptor)
                rollback_path = Path(rollback_name)
                rollback_path.write_bytes(original_ledger_bytes)
                os.replace(rollback_path, ledger_path)
            except BaseException as error:
                rollback_error = error
            finally:
                if rollback_path is not None and rollback_path.exists():
                    rollback_path.unlink()
        if report_promoted and final_report_dir.exists():
            shutil.rmtree(final_report_dir)
        if model_promoted and final_model_dir.exists():
            shutil.rmtree(final_model_dir)
        if rollback_error is not None:
            raise RuntimeError("Final-refit ledger rollback failed") from rollback_error
        raise
    finally:
        if temporary_model_dir is not None and temporary_model_dir.exists():
            shutil.rmtree(temporary_model_dir)
        if temporary_report_dir is not None and temporary_report_dir.exists():
            shutil.rmtree(temporary_report_dir)
        if not report_base_existed and report_base.exists():
            try:
                report_base.rmdir()
            except OSError:
                pass
        if not model_base_existed and model_base.exists():
            try:
                model_base.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    main()
