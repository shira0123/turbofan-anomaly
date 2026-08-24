"""Fit and select classical FD002 anomaly baselines on validation engines only.

The command deliberately does not open, transform, score, or summarize test.csv.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from turbofan_anomaly.data.preprocessing import SENSOR_COLUMNS
from turbofan_anomaly.data.windows import build_window_array, summary_features
from turbofan_anomaly.evaluation.provenance import (
    find_repository_root,
    repo_relative_posix,
    sha256_file,
)
from turbofan_anomaly.evaluation.proxies import (
    registered_validation_policies,
    training_eligible_windows,
)
from turbofan_anomaly.evaluation.ranking import proxy_ranking_metrics
from turbofan_anomaly.models.classical import (
    ClassicalAnomalyModel,
    candidate_grid,
    save_baseline_artifact,
)


STUDY_ID = "fd002-classical-baselines-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("configs/splits/fd002-primary-v1.json"),
    )
    parser.add_argument(
        "--preprocessing-selection",
        type=Path,
        default=Path(
            "configs/preprocessing/fd002-preprocessing-selection-v1.json"
        ),
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed/preprocessing"),
    )
    parser.add_argument(
        "--window-metadata-dir", type=Path, default=Path("data/processed")
    )
    parser.add_argument(
        "--sequences-dir",
        type=Path,
        default=Path("data/processed/sequences_v2"),
    )
    parser.add_argument(
        "--models-dir", type=Path, default=Path("models/baselines_v2")
    )
    parser.add_argument(
        "--reports-dir", type=Path, default=Path("reports/baselines_v2")
    )
    parser.add_argument(
        "--config-output",
        type=Path,
        default=Path("configs/baselines/fd002-classical-baselines-v1.json"),
    )
    parser.add_argument("--healthy-fraction", type=float, default=0.30)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _engine_digest(engine_ids: list[int]) -> str:
    payload = ",".join(map(str, sorted(engine_ids))).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _candidate_id(detector_name: str, index: int) -> str:
    return f"{detector_name}_candidate_{index + 1}"


def _metric_rows(
    *,
    pipeline: str,
    detector_name: str,
    candidate_id: str,
    parameters: dict[str, Any],
    calibrated_scores: np.ndarray,
    policy_frames: list[pd.DataFrame],
) -> tuple[list[dict], float, float]:
    base_rows, mean_pr_auc, mean_roc_auc = proxy_ranking_metrics(
        calibrated_scores, policy_frames
    )
    rows = [
        {
            "pipeline": pipeline,
            "detector": detector_name,
            "candidate_id": candidate_id,
            "parameters": json.dumps(parameters, sort_keys=True),
            **row,
        }
        for row in base_rows
    ]
    return rows, mean_pr_auc, mean_roc_auc


def _write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    repo_root = find_repository_root(args.split_manifest.resolve().parent)
    split_manifest = _load_json(args.split_manifest)
    preprocessing_selection = _load_json(args.preprocessing_selection)
    split_manifest_id = str(split_manifest["manifest_id"])
    decision_id = str(preprocessing_selection["decision_id"])
    if preprocessing_selection["decision_status"] != "approved":
        raise RuntimeError("Preprocessing selection is not approved")
    if preprocessing_selection["split_manifest_id"] != split_manifest_id:
        raise RuntimeError("Preprocessing selection and split manifest disagree")

    approved = preprocessing_selection["approved_choice"]
    pipelines = [
        str(approved["global_comparator"]),
        str(approved["primary_regime_pipeline"]),
    ]
    if pipelines != ["p0_global", "p1_k6"]:
        raise RuntimeError("Registered baseline study requires P0 and approved P1/K=6")

    train_metadata = pd.read_csv(
        args.window_metadata_dir / "window_metadata_train.csv"
    )
    validation_metadata = pd.read_csv(
        args.window_metadata_dir / "window_metadata_validation.csv"
    )
    for metadata, split_name in [
        (train_metadata, "train"),
        (validation_metadata, "validation"),
    ]:
        if set(metadata["split"]) != {split_name}:
            raise RuntimeError(f"Unexpected split value in {split_name} metadata")
        if set(metadata["split_manifest_id"]) != {split_manifest_id}:
            raise RuntimeError(f"{split_name} metadata uses a different manifest")

    fit_mask = training_eligible_windows(
        train_metadata, args.healthy_fraction
    ).to_numpy(dtype=bool)
    if not fit_mask.any():
        raise RuntimeError("No healthy-assumption training windows")
    fit_engine_ids = sorted(
        train_metadata.loc[fit_mask, "engine"].astype(int).unique().tolist()
    )
    policy_frames = [
        policy.apply(validation_metadata)
        for policy in registered_validation_policies()
    ]

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    args.sequences_dir.mkdir(parents=True, exist_ok=True)
    grid = candidate_grid()
    model_selection_rows: list[dict] = []
    selected_rows: list[dict] = []
    validation_score_frames: list[pd.DataFrame] = []
    array_shapes: dict[str, dict[str, list[int]]] = {}
    preprocessed_input_hashes: dict[str, dict[str, str]] = {}
    sequence_paths: dict[str, dict[str, Path]] = {}
    selected_artifact_paths: dict[str, dict[str, Path]] = {
        pipeline: {} for pipeline in pipelines
    }

    for pipeline in pipelines:
        train_path = args.processed_dir / pipeline / "train.csv"
        validation_path = args.processed_dir / pipeline / "validation.csv"
        preprocessed_input_hashes[pipeline] = {
            "train": sha256_file(train_path),
            "validation": sha256_file(validation_path),
        }
        train_frame = pd.read_csv(train_path)
        validation_frame = pd.read_csv(validation_path)
        train_sequences = build_window_array(train_frame, train_metadata)
        validation_sequences = build_window_array(
            validation_frame, validation_metadata
        )
        pipeline_sequence_dir = args.sequences_dir / pipeline
        pipeline_sequence_dir.mkdir(parents=True, exist_ok=True)
        sequence_paths[pipeline] = {
            "train": pipeline_sequence_dir / "train.npy",
            "validation": pipeline_sequence_dir / "validation.npy",
        }
        np.save(sequence_paths[pipeline]["train"], train_sequences)
        np.save(sequence_paths[pipeline]["validation"], validation_sequences)
        array_shapes[pipeline] = {
            "train": list(train_sequences.shape),
            "validation": list(validation_sequences.shape),
        }

        train_features = summary_features(train_sequences)
        validation_features = summary_features(validation_sequences)
        healthy_training_features = train_features[fit_mask]

        for detector_name, parameter_candidates in grid.items():
            evaluated_candidates: list[dict[str, Any]] = []
            for candidate_index, parameters in enumerate(parameter_candidates):
                candidate_id = _candidate_id(detector_name, candidate_index)
                model = ClassicalAnomalyModel(
                    detector_name,
                    parameters,
                    random_state=args.seed,
                ).fit(healthy_training_features)
                raw_scores, calibrated_scores = model.score(validation_features)
                metric_rows, mean_pr_auc, mean_roc_auc = _metric_rows(
                    pipeline=pipeline,
                    detector_name=detector_name,
                    candidate_id=candidate_id,
                    parameters=parameters,
                    calibrated_scores=calibrated_scores,
                    policy_frames=policy_frames,
                )
                for row in metric_rows:
                    row["selection_mean_pr_auc"] = mean_pr_auc
                    row["selection_mean_roc_auc"] = mean_roc_auc
                model_selection_rows.extend(metric_rows)
                evaluated_candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "parameters": parameters,
                        "model": model,
                        "raw_scores": raw_scores,
                        "calibrated_scores": calibrated_scores,
                        "selection_mean_pr_auc": mean_pr_auc,
                        "selection_mean_roc_auc": mean_roc_auc,
                    }
                )

            selected = sorted(
                evaluated_candidates,
                key=lambda item: (
                    -item["selection_mean_pr_auc"],
                    -item["selection_mean_roc_auc"],
                    item["candidate_id"],
                ),
            )[0]
            artifact_path = args.models_dir / pipeline / f"{detector_name}.joblib"
            artifact_metadata = {
                "study_id": STUDY_ID,
                "split_manifest_id": split_manifest_id,
                "preprocessing_decision_id": decision_id,
                "pipeline": pipeline,
                "detector": detector_name,
                "candidate_id": selected["candidate_id"],
                "parameters": selected["parameters"],
                "random_state": args.seed,
                "healthy_training_fraction": args.healthy_fraction,
                "fit_window_count": int(fit_mask.sum()),
                "fit_engine_count": len(fit_engine_ids),
                "fit_engine_ids_sha256": _engine_digest(fit_engine_ids),
                "feature_definition": "mean_std_end_minus_start_per_sensor",
                "feature_count": int(healthy_training_features.shape[1]),
                "score_calibration": "empirical_cdf_fitted_on_healthy_training_scores",
                "result_classification": "validation_selected_not_test_performance",
            }
            save_baseline_artifact(
                selected["model"], artifact_metadata, artifact_path
            )
            selected_artifact_paths[pipeline][detector_name] = artifact_path
            selected_rows.append(
                {
                    **artifact_metadata,
                    "parameters": json.dumps(
                        selected["parameters"], sort_keys=True
                    ),
                    "selection_mean_pr_auc": selected["selection_mean_pr_auc"],
                    "selection_mean_roc_auc": selected["selection_mean_roc_auc"],
                    "artifact_path": repo_relative_posix(artifact_path, repo_root),
                }
            )
            score_frame = validation_metadata[
                [
                    "window_id",
                    "engine",
                    "start_cycle",
                    "end_cycle",
                    "max_cycle",
                    "split",
                ]
            ].copy()
            score_frame.insert(0, "pipeline", pipeline)
            score_frame.insert(1, "detector", detector_name)
            score_frame.insert(2, "candidate_id", selected["candidate_id"])
            score_frame["raw_score"] = selected["raw_scores"]
            score_frame["calibrated_score"] = selected["calibrated_scores"]
            validation_score_frames.append(score_frame)

    reports = {
        "model_selection": args.reports_dir / "model_selection.csv",
        "selected_models": args.reports_dir / "selected_models.csv",
        "validation_scores": args.reports_dir / "validation_scores.csv",
        "policy_counts": args.reports_dir / "policy_counts.csv",
    }
    pd.DataFrame(model_selection_rows).sort_values(
        ["pipeline", "detector", "candidate_id", "policy_id"]
    ).to_csv(reports["model_selection"], index=False)
    pd.DataFrame(selected_rows).sort_values(["pipeline", "detector"]).to_csv(
        reports["selected_models"], index=False
    )
    pd.concat(validation_score_frames, ignore_index=True).to_csv(
        reports["validation_scores"], index=False
    )
    policy_count_rows = []
    for policy_frame in policy_frames:
        counts = policy_frame["label_state"].value_counts()
        policy_count_rows.append(
            {
                "policy_id": policy_frame["policy_id"].iloc[0],
                "policy_semantics": policy_frame["policy_semantics"].iloc[0],
                "selection_policy": bool(
                    policy_frame["selection_policy"].iloc[0]
                ),
                "healthy_windows": int(counts.get("healthy", 0)),
                "ambiguous_windows": int(counts.get("ambiguous", 0)),
                "anomalous_windows": int(counts.get("anomalous", 0)),
            }
        )
    pd.DataFrame(policy_count_rows).to_csv(reports["policy_counts"], index=False)

    config = {
        "study_id": STUDY_ID,
        "split_manifest_id": split_manifest_id,
        "preprocessing_decision_id": decision_id,
        "inputs": {
            "split_manifest_sha256": sha256_file(args.split_manifest),
            "preprocessing_selection_sha256": sha256_file(
                args.preprocessing_selection
            ),
            "window_metadata_train_sha256": sha256_file(
                args.window_metadata_dir / "window_metadata_train.csv"
            ),
            "window_metadata_validation_sha256": sha256_file(
                args.window_metadata_dir / "window_metadata_validation.csv"
            ),
            "preprocessed_csv_sha256": preprocessed_input_hashes,
            "test_data_opened_by_study": False,
        },
        "pipelines": pipelines,
        "sequence_shapes": array_shapes,
        "training_policy": {
            "healthy_fraction": args.healthy_fraction,
            "fit_windows": int(fit_mask.sum()),
            "non_fit_training_windows_interpretation": "unlabeled_not_known_anomaly",
        },
        "feature_definition": {
            "name": "mean_std_end_minus_start_per_sensor",
            "input_shape": [30, len(SENSOR_COLUMNS)],
            "output_features": 3 * len(SENSOR_COLUMNS),
        },
        "candidate_grid": grid,
        "selection_rule": {
            "primary": "maximum_mean_validation_pr_auc_across_three_endpoint_policies",
            "tie_break_1": "maximum_mean_validation_roc_auc",
            "tie_break_2": "candidate_id_lexicographic",
            "threshold_selected": False,
        },
        "policies": [
            {
                "policy_id": frame["policy_id"].iloc[0],
                "semantics": frame["policy_semantics"].iloc[0],
                "selection_policy": bool(frame["selection_policy"].iloc[0]),
                "onset_fraction": float(frame["onset_fraction"].iloc[0]),
            }
            for frame in policy_frames
        ],
        "outputs": {
            "reports": {
                name: repo_relative_posix(path, repo_root)
                for name, path in reports.items()
            },
            "report_sha256": {
                name: sha256_file(path) for name, path in reports.items()
            },
            "models_dir": repo_relative_posix(args.models_dir, repo_root),
            "selected_model_sha256": {
                pipeline: {
                    detector: sha256_file(path)
                    for detector, path in detector_paths.items()
                }
                for pipeline, detector_paths in selected_artifact_paths.items()
            },
            "sequences_dir": repo_relative_posix(args.sequences_dir, repo_root),
            "sequence_sha256": {
                pipeline: {
                    split_name: sha256_file(path)
                    for split_name, path in split_paths.items()
                }
                for pipeline, split_paths in sequence_paths.items()
            },
            "test_outputs_created": False,
        },
        "package_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "random_state": args.seed,
        "result_classification": "validation_model_selection_not_test_performance",
    }
    _write_json(config, args.config_output)
    print(
        {
            "study_id": STUDY_ID,
            "pipelines": pipelines,
            "fit_windows": int(fit_mask.sum()),
            "selected_models": len(selected_rows),
            "test_data_opened_by_study": False,
            "result_classification": config["result_classification"],
        }
    )


if __name__ == "__main__":
    main()
