"""Run the registered FD002 LSTM screen without opening held-out test data."""

from __future__ import annotations

import argparse
import json
import os
import platform
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import pandas as pd
import torch
from turbofan_anomaly.alerting.calibration import EmpiricalCDFCalibrator
from turbofan_anomaly.evaluation.provenance import (
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
    LSTMArchitecture,
    TrainingSettings,
    engine_id_digest,
    fit_lstm_autoencoder,
    parameter_count,
    reconstruction_errors,
    save_lstm_artifact,
    split_eligible_training_windows,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("configs/lstm/fd002-lstm-screen-protocol-v1.json"),
    )
    parser.add_argument(
        "--models-dir", type=Path, default=Path("models/lstm_v2")
    )
    parser.add_argument(
        "--reports-dir", type=Path, default=Path("reports/lstm_v2")
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _require_hash(path: Path, expected: str) -> None:
    verification = verify_registered_hash(path, expected)
    print(
        f"HASH_OK path={path} match_form={verification.match_form}",
        flush=True,
    )


def _device(choice: str) -> torch.device:
    if choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable")
        return torch.device("cuda")
    if choice == "cpu":
        return torch.device("cpu")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _selection_metrics(
    calibrated_scores: np.ndarray,
    policy_frames: list[pd.DataFrame],
) -> tuple[list[dict[str, Any]], float, float]:
    return proxy_ranking_metrics(calibrated_scores, policy_frames)


def _run_id(
    stage: str, pipeline: str, architecture_id: str, seed: int
) -> str:
    return f"fd002_lstm_v1_{stage}_{pipeline}_{architecture_id}_seed{seed}"


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol.resolve()
    repo_root = find_repository_root(protocol_path.parent)
    protocol = _load_json(protocol_path)
    if protocol.get("status") != "registered_before_execution":
        raise RuntimeError("The LSTM protocol is not registered for execution")
    if protocol["evidence_boundary"]["test_data_may_be_opened"]:
        raise RuntimeError("This screen must not permit held-out test access")
    if int(protocol["screen"]["total_registered_runs"]) != 9:
        raise RuntimeError("Unexpected registered run count")

    inputs = protocol["inputs"]
    _require_hash(
        resolve_repo_path(inputs["split_manifest"], repo_root),
        inputs["split_manifest_sha256"],
    )
    _require_hash(
        resolve_repo_path(inputs["preprocessing_selection"], repo_root),
        inputs["preprocessing_selection_sha256"],
    )
    _require_hash(
        resolve_repo_path(inputs["baseline_config"], repo_root),
        inputs["baseline_config_sha256"],
    )
    metadata_dir = resolve_repo_path(inputs["window_metadata_dir"], repo_root)
    sequence_dir = resolve_repo_path(inputs["sequences_dir"], repo_root)
    for split_name in ("train", "validation"):
        _require_hash(
            metadata_dir / f"window_metadata_{split_name}.csv",
            inputs["window_metadata_sha256"][split_name],
        )
    for pipeline in protocol["pipelines"]:
        for split_name in ("train", "validation"):
            _require_hash(
                sequence_dir / pipeline / f"{split_name}.npy",
                inputs["sequence_sha256"][pipeline][split_name],
            )

    train_metadata = pd.read_csv(metadata_dir / "window_metadata_train.csv")
    validation_metadata = pd.read_csv(
        metadata_dir / "window_metadata_validation.csv"
    )
    split_manifest_id = str(inputs["split_manifest_id"])
    for metadata, expected_split in (
        (train_metadata, "train"),
        (validation_metadata, "validation"),
    ):
        if set(metadata["split"]) != {expected_split}:
            raise RuntimeError(f"Unexpected {expected_split} metadata split value")
        if set(metadata["split_manifest_id"]) != {split_manifest_id}:
            raise RuntimeError(f"{expected_split} metadata manifest mismatch")

    training = protocol["training"]
    eligible = training_eligible_windows(
        train_metadata, float(training["healthy_fraction"])
    ).to_numpy(dtype=bool)
    monitor_config = protocol["monitor_split"]
    development_mask, monitor_mask, monitor_assignment = (
        split_eligible_training_windows(
            train_metadata,
            eligible,
            monitor_fraction=float(monitor_config["fraction"]),
            random_state=int(monitor_config["random_state"]),
            n_strata=int(monitor_config["n_strata"]),
        )
    )
    development_engines = sorted(
        monitor_assignment.loc[
            monitor_assignment["role"] == "development", "engine"
        ]
        .astype(int)
        .tolist()
    )
    monitor_engines = sorted(
        monitor_assignment.loc[
            monitor_assignment["role"] == "monitor", "engine"
        ]
        .astype(int)
        .tolist()
    )
    validation_engines = sorted(
        validation_metadata["engine"].astype(int).unique().tolist()
    )
    if (set(development_engines) | set(monitor_engines)) & set(
        validation_engines
    ):
        raise RuntimeError("Training and validation engines overlap")

    expected_shape = tuple(map(int, protocol["window_shape"]))
    arrays: dict[str, dict[str, np.ndarray]] = {}
    for pipeline in protocol["pipelines"]:
        arrays[pipeline] = {
            split_name: np.load(
                sequence_dir / pipeline / f"{split_name}.npy",
                allow_pickle=False,
            )
            for split_name in ("train", "validation")
        }
        if arrays[pipeline]["train"].shape != (
            len(train_metadata),
            *expected_shape,
        ):
            raise RuntimeError(f"Unexpected {pipeline} training sequence shape")
        if arrays[pipeline]["validation"].shape != (
            len(validation_metadata),
            *expected_shape,
        ):
            raise RuntimeError(f"Unexpected {pipeline} validation sequence shape")

    architecture_by_id = {
        item["architecture_id"]: LSTMArchitecture(**item)
        for item in protocol["architectures"]
    }
    settings = TrainingSettings(
        batch_size=int(training["batch_size"]),
        max_epochs=int(training["max_epochs"]),
        minimum_epochs=int(training["minimum_epochs"]),
        patience=int(training["patience"]),
        min_delta=float(training["min_delta"]),
        learning_rate=float(training["learning_rate"]),
        weight_decay=float(training["weight_decay"]),
        gradient_clip_norm=float(training["gradient_clip_norm"]),
    )
    policy_frames = [
        policy.apply(validation_metadata)
        for policy in registered_validation_policies()
    ]
    device = _device(args.device)
    args.models_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    execution_time = datetime.now().astimezone().isoformat(timespec="seconds")

    run_summaries: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    history_rows: list[dict[str, Any]] = []
    validation_score_frames: list[pd.DataFrame] = []
    experiment_rows: list[dict[str, Any]] = []
    artifact_paths: dict[str, Path] = {}

    def execute_run(
        *, stage: str, pipeline: str, architecture: LSTMArchitecture, seed: int
    ) -> dict[str, Any]:
        run_id = _run_id(stage, pipeline, architecture.architecture_id, seed)
        print(
            f"START {run_id} device={device.type} "
            f"development={int(development_mask.sum())} "
            f"monitor={int(monitor_mask.sum())}",
            flush=True,
        )
        train_sequences = arrays[pipeline]["train"]
        validation_sequences = arrays[pipeline]["validation"]
        fit_result = fit_lstm_autoencoder(
            train_sequences[development_mask],
            train_sequences[monitor_mask],
            architecture=architecture,
            settings=settings,
            seed=seed,
            device=device,
        )
        development_scores = reconstruction_errors(
            fit_result.model,
            train_sequences[development_mask],
            batch_size=settings.batch_size,
            device=device,
        )
        validation_raw_scores = reconstruction_errors(
            fit_result.model,
            validation_sequences,
            batch_size=settings.batch_size,
            device=device,
        )
        calibrator = EmpiricalCDFCalibrator().fit(development_scores)
        validation_calibrated_scores = calibrator.transform(
            validation_raw_scores
        )
        run_metrics, mean_pr_auc, mean_roc_auc = _selection_metrics(
            validation_calibrated_scores, policy_frames
        )
        model_parameters = parameter_count(fit_result.model)
        artifact_path = args.models_dir / f"{run_id}.pt"
        artifact_metadata = {
            "study_id": protocol["study_id"],
            "run_id": run_id,
            "stage": stage,
            "split_manifest_id": split_manifest_id,
            "preprocessing_decision_id": inputs["preprocessing_decision_id"],
            "pipeline": pipeline,
            "seed": seed,
            "input_dim": expected_shape[1],
            "window_size": expected_shape[0],
            "architecture": asdict(architecture),
            "training_settings": asdict(settings),
            "development_window_count": int(development_mask.sum()),
            "monitor_window_count": int(monitor_mask.sum()),
            "development_engine_count": len(development_engines),
            "monitor_engine_count": len(monitor_engines),
            "development_engine_ids_sha256": engine_id_digest(
                development_engines
            ),
            "monitor_engine_ids_sha256": engine_id_digest(monitor_engines),
            "best_epoch": fit_result.best_epoch,
            "best_monitor_loss": fit_result.best_monitor_loss,
            "score_calibration": training["score_calibration"],
            "result_classification": protocol["evidence_boundary"][
                "result_classification"
            ],
        }
        save_lstm_artifact(
            fit_result.model,
            architecture,
            development_scores,
            artifact_metadata,
            artifact_path,
        )
        artifact_paths[run_id] = artifact_path
        summary = {
            "run_id": run_id,
            "stage": stage,
            "pipeline": pipeline,
            "architecture_id": architecture.architecture_id,
            "seed": seed,
            "parameter_count": model_parameters,
            "epochs_completed": len(fit_result.history),
            "best_epoch": fit_result.best_epoch,
            "best_monitor_loss": fit_result.best_monitor_loss,
            "selection_mean_pr_auc": mean_pr_auc,
            "selection_mean_roc_auc": mean_roc_auc,
            "artifact_path": str(artifact_path),
        }
        run_summaries.append(summary)
        for row in run_metrics:
            metric_rows.append({**summary, **row})
        for row in fit_result.history:
            history_rows.append(
                {
                    "run_id": run_id,
                    "stage": stage,
                    "pipeline": pipeline,
                    "architecture_id": architecture.architecture_id,
                    "seed": seed,
                    **row,
                }
            )
        score_frame = validation_metadata[
            ["window_id", "engine", "start_cycle", "end_cycle", "max_cycle"]
        ].copy()
        score_frame.insert(0, "run_id", run_id)
        score_frame.insert(1, "stage", stage)
        score_frame.insert(2, "pipeline", pipeline)
        score_frame.insert(3, "architecture_id", architecture.architecture_id)
        score_frame.insert(4, "seed", seed)
        score_frame["raw_reconstruction_error"] = validation_raw_scores
        score_frame["calibrated_score"] = validation_calibrated_scores
        validation_score_frames.append(score_frame)
        experiment_rows.append(
            {
                "run_id": run_id,
                "datetime": execution_time,
                "owner": protocol["owner"],
                "experiment_name": "lstm_validation_screen",
                "model": "lstm_autoencoder",
                "params": json.dumps(
                    {
                        "stage": stage,
                        "pipeline": pipeline,
                        "architecture": asdict(architecture),
                        "seed": seed,
                        "training": asdict(settings),
                    },
                    sort_keys=True,
                ),
                "train_size": int(development_mask.sum()),
                "valid_size": len(validation_metadata),
                "metric_name": "mean_validation_pr_auc_endpoint_policies",
                "metric_value": mean_pr_auc,
                "notes": (
                    "evidence=validation_proxy_only; "
                    f"monitor_windows={int(monitor_mask.sum())}; "
                    f"best_epoch={fit_result.best_epoch}; "
                    f"best_monitor_loss={fit_result.best_monitor_loss:.10f}; "
                    f"mean_roc_auc={mean_roc_auc:.10f}; "
                    "no threshold or test access"
                ),
                "artifact_path": str(artifact_path),
            }
        )
        print(
            f"DONE {run_id} epochs={len(fit_result.history)} "
            f"best_epoch={fit_result.best_epoch} "
            f"monitor={fit_result.best_monitor_loss:.6f} "
            f"mean_pr={mean_pr_auc:.6f} mean_roc={mean_roc_auc:.6f}",
            flush=True,
        )
        return summary

    stage_1 = protocol["screen"]["stage_1"]
    if stage_1["seeds"] != [42] or stage_1["pipeline"] != "p1_k6":
        raise RuntimeError("Unexpected stage 1 registration")
    stage_1_summaries = [
        execute_run(
            stage="stage1",
            pipeline=stage_1["pipeline"],
            architecture=architecture_by_id[architecture_id],
            seed=42,
        )
        for architecture_id in stage_1["architecture_ids"]
    ]
    selected_architecture_summary = sorted(
        stage_1_summaries,
        key=lambda row: (
            -row["selection_mean_pr_auc"],
            -row["selection_mean_roc_auc"],
            row["best_monitor_loss"],
            row["architecture_id"],
        ),
    )[0]
    selected_architecture_id = selected_architecture_summary["architecture_id"]
    selected_architecture = architecture_by_id[selected_architecture_id]
    print(f"STAGE1_SELECTED {selected_architecture_id}", flush=True)

    stage_2 = protocol["screen"]["stage_2"]
    for seed in stage_2["seeds"]:
        for pipeline in stage_2["pipelines"]:
            execute_run(
                stage="stage2",
                pipeline=pipeline,
                architecture=selected_architecture,
                seed=int(seed),
            )
    if len(run_summaries) != int(protocol["screen"]["total_registered_runs"]):
        raise RuntimeError("Executed run count differs from the registration")

    run_summary_frame = pd.DataFrame(run_summaries).sort_values(
        ["stage", "pipeline", "architecture_id", "seed"]
    )
    stage_2_frame = run_summary_frame[run_summary_frame["stage"] == "stage2"]
    robustness = (
        stage_2_frame.groupby("pipeline", as_index=False)
        .agg(
            run_count=("run_id", "count"),
            median_selection_mean_pr_auc=("selection_mean_pr_auc", "median"),
            mean_selection_mean_pr_auc=("selection_mean_pr_auc", "mean"),
            std_selection_mean_pr_auc=("selection_mean_pr_auc", "std"),
            min_selection_mean_pr_auc=("selection_mean_pr_auc", "min"),
            max_selection_mean_pr_auc=("selection_mean_pr_auc", "max"),
            median_selection_mean_roc_auc=("selection_mean_roc_auc", "median"),
            mean_best_monitor_loss=("best_monitor_loss", "mean"),
        )
        .sort_values("pipeline")
    )
    recommended_pipeline_row = robustness.sort_values(
        [
            "median_selection_mean_pr_auc",
            "median_selection_mean_roc_auc",
            "pipeline",
        ],
        ascending=[False, False, True],
    ).iloc[0]
    recommended_pipeline = str(recommended_pipeline_row["pipeline"])

    reports = {
        "monitor_engine_assignment": args.reports_dir
        / "monitor_engine_assignment.csv",
        "training_history": args.reports_dir / "training_history.csv",
        "model_selection": args.reports_dir / "model_selection.csv",
        "run_summary": args.reports_dir / "run_summary.csv",
        "architecture_screen": args.reports_dir / "architecture_screen.csv",
        "robustness_summary": args.reports_dir / "robustness_summary.csv",
        "validation_scores": args.reports_dir / "validation_scores.csv",
        "experiment_rows": args.reports_dir / "experiment_rows.csv",
    }
    monitor_assignment.to_csv(reports["monitor_engine_assignment"], index=False)
    pd.DataFrame(history_rows).to_csv(reports["training_history"], index=False)
    pd.DataFrame(metric_rows).sort_values(
        ["stage", "pipeline", "architecture_id", "seed", "policy_id"]
    ).to_csv(reports["model_selection"], index=False)
    run_summary_frame.to_csv(reports["run_summary"], index=False)
    run_summary_frame[run_summary_frame["stage"] == "stage1"].to_csv(
        reports["architecture_screen"], index=False
    )
    robustness.to_csv(reports["robustness_summary"], index=False)
    pd.concat(validation_score_frames, ignore_index=True).to_csv(
        reports["validation_scores"], index=False
    )
    pd.DataFrame(experiment_rows).to_csv(reports["experiment_rows"], index=False)

    results = {
        "study_id": protocol["study_id"],
        "protocol_path": repo_relative_posix(protocol_path, repo_root),
        "protocol_sha256": sha256_file(protocol_path),
        "execution_time": execution_time,
        "execution_device": str(device),
        "registered_runs": int(protocol["screen"]["total_registered_runs"]),
        "completed_runs": len(run_summaries),
        "split_manifest_id": split_manifest_id,
        "preprocessing_decision_id": inputs["preprocessing_decision_id"],
        "monitor_split": {
            "method": monitor_config["method"],
            "development_engine_count": len(development_engines),
            "monitor_engine_count": len(monitor_engines),
            "development_window_count": int(development_mask.sum()),
            "monitor_window_count": int(monitor_mask.sum()),
            "development_engine_ids_sha256": engine_id_digest(
                development_engines
            ),
            "monitor_engine_ids_sha256": engine_id_digest(monitor_engines),
        },
        "stage_1_recommendation": {
            "architecture_id": selected_architecture_id,
            "selection_mean_pr_auc": selected_architecture_summary[
                "selection_mean_pr_auc"
            ],
            "selection_mean_roc_auc": selected_architecture_summary[
                "selection_mean_roc_auc"
            ],
            "decision_status": "recommended_pending_human_approval",
        },
        "stage_2_recommendation": {
            "pipeline": recommended_pipeline,
            "median_selection_mean_pr_auc": float(
                recommended_pipeline_row["median_selection_mean_pr_auc"]
            ),
            "median_selection_mean_roc_auc": float(
                recommended_pipeline_row["median_selection_mean_roc_auc"]
            ),
            "decision_status": "recommended_pending_human_approval",
        },
        "outputs": {
            "reports": {
                name: repo_relative_posix(path, repo_root)
                for name, path in reports.items()
            },
            "report_sha256": {
                name: sha256_file(path) for name, path in reports.items()
            },
            "models_dir": repo_relative_posix(args.models_dir, repo_root),
            "model_sha256": {
                run_id: sha256_file(path)
                for run_id, path in sorted(artifact_paths.items())
            },
            "test_outputs_created": False,
        },
        "package_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "torch": torch.__version__,
        },
        "result_classification": protocol["evidence_boundary"][
            "result_classification"
        ],
        "test_data_opened_by_study": False,
    }
    result_path = resolve_repo_path(protocol["result_config_output"], repo_root)
    _write_json(results, result_path)
    print(
        json.dumps(
            {
                "study_id": protocol["study_id"],
                "completed_runs": len(run_summaries),
                "selected_architecture": selected_architecture_id,
                "recommended_pipeline": recommended_pipeline,
                "test_data_opened_by_study": False,
                "result_config": repo_relative_posix(result_path, repo_root),
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
