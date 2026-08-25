"""Run the leakage-controlled FD002 P0/P1 preprocessing candidate study.

This command fits on approved training engines, uses validation only for model-
selection diagnostics, and deliberately does not open or transform test.csv.
"""

from __future__ import annotations

import argparse
from itertools import combinations
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from turbofan_anomaly.data.preprocessing import (
    OP_COLUMNS,
    SENSOR_COLUMNS,
    GlobalSensorPreprocessor,
    RegimeSensorPreprocessor,
    save_preprocessor,
)
from turbofan_anomaly.evaluation.provenance import (
    find_repository_root,
    repo_relative_posix,
    sha256_file,
)


STUDY_ID = "fd002-preprocessing-study-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("configs/splits/fd002-primary-v1.json"),
    )
    parser.add_argument("--splits-dir", type=Path, default=Path("data/splits"))
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed/preprocessing"),
    )
    parser.add_argument(
        "--models-dir", type=Path, default=Path("models/preprocessing")
    )
    parser.add_argument(
        "--reports-dir", type=Path, default=Path("reports/preprocessing")
    )
    parser.add_argument(
        "--config-output",
        type=Path,
        default=Path("configs/preprocessing/fd002-preprocessing-study-v1.json"),
    )
    parser.add_argument("--healthy-fraction", type=float, default=0.30)
    parser.add_argument("--clusters", type=int, nargs="+", default=[4, 6, 8])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-init", type=int, default=20)
    parser.add_argument("--min-mode-fit-rows", type=int, default=30)
    parser.add_argument("--silhouette-sample-size", type=int, default=5000)
    parser.add_argument(
        "--stability-seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46]
    )
    parser.add_argument("--stability-engine-fraction", type=float, default=0.80)
    parser.add_argument("--stability-n-init", type=int, default=10)
    return parser.parse_args()


def _load_approved_inputs(
    manifest_path: Path, splits_dir: Path
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Split manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Intentionally do not read data/splits/test.csv in this study.
    train = pd.read_csv(splits_dir / "train.csv")
    validation = pd.read_csv(splits_dir / "validation.csv")
    expected = {
        split: {
            int(record["engine"])
            for record in manifest["engines"]
            if record["split"] == split
        }
        for split in ("train", "validation")
    }
    observed = {
        "train": set(train["engine"].astype(int).unique()),
        "validation": set(validation["engine"].astype(int).unique()),
    }
    if observed != expected:
        raise RuntimeError("Train/validation CSV engine IDs do not match the manifest")
    if observed["train"] & observed["validation"]:
        raise RuntimeError("Train and validation engines overlap")
    return manifest, train, validation


def _silhouette(
    frame: pd.DataFrame,
    preprocessor: RegimeSensorPreprocessor,
    *,
    sample_size: int,
    seed: int,
) -> float:
    assert preprocessor.op_scaler_ is not None
    scaled = preprocessor.op_scaler_.transform(
        frame.loc[:, list(OP_COLUMNS)].to_numpy(dtype=float)
    )
    labels = preprocessor.predict_modes(frame)
    if len(np.unique(labels)) < 2:
        return float("nan")
    effective_sample_size = min(int(sample_size), len(frame))
    return float(
        silhouette_score(
            scaled,
            labels,
            sample_size=effective_sample_size,
            random_state=seed,
        )
    )


def _engine_subsample_stability(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    n_clusters: int,
    seeds: list[int],
    engine_fraction: float,
    n_init: int,
) -> dict[str, float | int]:
    if len(seeds) < 2:
        raise ValueError("At least two stability seeds are required")
    if not 0.0 < engine_fraction <= 1.0:
        raise ValueError("stability engine fraction must be in (0, 1]")

    engine_ids = np.array(sorted(train["engine"].astype(int).unique()))
    sample_count = max(1, int(np.floor(len(engine_ids) * engine_fraction)))
    validation_settings = validation.loc[:, list(OP_COLUMNS)].to_numpy(dtype=float)
    predictions: list[np.ndarray] = []

    for seed in seeds:
        rng = np.random.default_rng(seed)
        sampled_engines = np.sort(
            rng.choice(engine_ids, size=sample_count, replace=False)
        )
        sample = train[train["engine"].isin(sampled_engines)]
        op_scaler = StandardScaler().fit(
            sample.loc[:, list(OP_COLUMNS)].to_numpy(dtype=float)
        )
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=seed,
            n_init=n_init,
        ).fit(
            op_scaler.transform(
                sample.loc[:, list(OP_COLUMNS)].to_numpy(dtype=float)
            )
        )
        predictions.append(
            kmeans.predict(op_scaler.transform(validation_settings)).astype(int)
        )

    pair_scores = [
        float(adjusted_rand_score(left, right))
        for left, right in combinations(predictions, 2)
    ]
    return {
        "stability_ari_mean": float(np.mean(pair_scores)),
        "stability_ari_min": float(np.min(pair_scores)),
        "stability_ari_max": float(np.max(pair_scores)),
        "stability_pair_count": len(pair_scores),
        "stability_sampled_engines": sample_count,
    }


def _occupancy_rows(
    transformed: pd.DataFrame,
    *,
    split: str,
    n_clusters: int,
    fit_rows_per_mode: dict[int, int],
) -> list[dict]:
    rows = []
    total_rows = len(transformed)
    total_engines = transformed["engine"].nunique()
    for mode in range(n_clusters):
        mode_frame = transformed[transformed["op_mode"] == mode]
        rows.append(
            {
                "k": n_clusters,
                "split": split,
                "op_mode": mode,
                "row_count": int(len(mode_frame)),
                "row_fraction": float(len(mode_frame) / total_rows),
                "engine_count": int(mode_frame["engine"].nunique()),
                "engine_fraction": float(
                    mode_frame["engine"].nunique() / total_engines
                ),
                "sensor_scaler_fit_rows": (
                    int(fit_rows_per_mode[mode]) if split == "train" else pd.NA
                ),
            }
        )
    return rows


def _centroid_rows(
    train: pd.DataFrame,
    preprocessor: RegimeSensorPreprocessor,
) -> list[dict]:
    centroids = preprocessor.centroids_original_units()
    modes = preprocessor.predict_modes(train)
    settings = train.loc[:, list(OP_COLUMNS)].copy()
    settings["op_mode"] = modes
    spread = settings.groupby("op_mode")[list(OP_COLUMNS)].std(ddof=0)

    rows = []
    for centroid in centroids.itertuples(index=False):
        mode = int(centroid.op_mode)
        rows.append(
            {
                "k": preprocessor.n_clusters,
                "op_mode": mode,
                "centroid_op1": float(centroid.centroid_op1),
                "centroid_op2": float(centroid.centroid_op2),
                "centroid_op3": float(centroid.centroid_op3),
                "within_std_op1": float(spread.loc[mode, "op1"]),
                "within_std_op2": float(spread.loc[mode, "op2"]),
                "within_std_op3": float(spread.loc[mode, "op3"]),
            }
        )
    return rows


def _write_processed(
    frame: pd.DataFrame, output_path: Path, expected_metadata: pd.DataFrame
) -> None:
    if len(frame) != len(expected_metadata):
        raise RuntimeError("Preprocessing changed the row count")
    metadata_columns = ["engine", "cycle", *OP_COLUMNS]
    if not frame[metadata_columns].equals(expected_metadata[metadata_columns]):
        raise RuntimeError("Preprocessing changed engine, cycle, or operating settings")
    if frame[list(SENSOR_COLUMNS)].isna().any().any():
        raise RuntimeError("Preprocessing produced null sensor values")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)


def _write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    repo_root = find_repository_root(args.manifest.resolve().parent)
    manifest, train, validation = _load_approved_inputs(
        args.manifest, args.splits_dir
    )
    manifest_id = str(manifest["manifest_id"])
    candidate_k = sorted(set(map(int, args.clusters)))
    if candidate_k != [4, 6, 8]:
        raise ValueError("The registered primary study requires K candidates [4, 6, 8]")

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    fit_summary_rows: list[dict] = []
    selection_rows: list[dict] = []
    occupancy_rows: list[dict] = []
    centroid_rows: list[dict] = []

    global_preprocessor = GlobalSensorPreprocessor(
        split_manifest_id=manifest_id,
        healthy_fraction=args.healthy_fraction,
    ).fit(train)
    p0_train = global_preprocessor.transform(train)
    p0_validation = global_preprocessor.transform(validation)
    _write_processed(
        p0_train, args.processed_dir / "p0_global" / "train.csv", train
    )
    _write_processed(
        p0_validation,
        args.processed_dir / "p0_global" / "validation.csv",
        validation,
    )
    save_preprocessor(
        global_preprocessor, args.models_dir / "p0_global.joblib"
    )
    fit_summary_rows.append(global_preprocessor.fit_metadata())

    for n_clusters in candidate_k:
        preprocessor = RegimeSensorPreprocessor(
            split_manifest_id=manifest_id,
            n_clusters=n_clusters,
            healthy_fraction=args.healthy_fraction,
            random_state=args.seed,
            n_init=args.n_init,
            min_mode_fit_rows=args.min_mode_fit_rows,
        ).fit(train)
        transformed_train = preprocessor.transform(train)
        transformed_validation = preprocessor.transform(validation)
        candidate_name = f"p1_k{n_clusters}"
        _write_processed(
            transformed_train,
            args.processed_dir / candidate_name / "train.csv",
            train,
        )
        _write_processed(
            transformed_validation,
            args.processed_dir / candidate_name / "validation.csv",
            validation,
        )
        save_preprocessor(
            preprocessor, args.models_dir / f"{candidate_name}.joblib"
        )

        fit_summary_rows.append(preprocessor.fit_metadata())
        occupancy_rows.extend(
            _occupancy_rows(
                transformed_train,
                split="train",
                n_clusters=n_clusters,
                fit_rows_per_mode=preprocessor.sensor_fit_rows_per_mode_,
            )
        )
        occupancy_rows.extend(
            _occupancy_rows(
                transformed_validation,
                split="validation",
                n_clusters=n_clusters,
                fit_rows_per_mode=preprocessor.sensor_fit_rows_per_mode_,
            )
        )
        centroid_rows.extend(_centroid_rows(train, preprocessor))

        stability = _engine_subsample_stability(
            train,
            validation,
            n_clusters=n_clusters,
            seeds=list(args.stability_seeds),
            engine_fraction=args.stability_engine_fraction,
            n_init=args.stability_n_init,
        )
        train_counts = transformed_train["op_mode"].value_counts()
        validation_counts = transformed_validation["op_mode"].value_counts()
        assert preprocessor.kmeans_ is not None
        centroid_distances = []
        for left, right in combinations(preprocessor.kmeans_.cluster_centers_, 2):
            centroid_distances.append(float(np.linalg.norm(left - right)))
        selection_rows.append(
            {
                "k": n_clusters,
                "train_silhouette": _silhouette(
                    train,
                    preprocessor,
                    sample_size=args.silhouette_sample_size,
                    seed=args.seed,
                ),
                "validation_silhouette": _silhouette(
                    validation,
                    preprocessor,
                    sample_size=args.silhouette_sample_size,
                    seed=args.seed,
                ),
                **stability,
                "train_min_mode_rows": int(train_counts.min()),
                "train_min_mode_fraction": float(train_counts.min() / len(train)),
                "validation_min_mode_rows": int(validation_counts.min()),
                "validation_min_mode_fraction": float(
                    validation_counts.min() / len(validation)
                ),
                "sensor_scaler_min_fit_rows": int(
                    min(preprocessor.sensor_fit_rows_per_mode_.values())
                ),
                "fallback_mode_count": len(preprocessor.fallback_modes_),
                "kmeans_inertia_per_train_row": float(
                    preprocessor.kmeans_.inertia_ / len(train)
                ),
                "min_centroid_distance_scaled": float(min(centroid_distances)),
            }
        )

    reports = {
        "model_selection": args.reports_dir / "model_selection.csv",
        "occupancy": args.reports_dir / "occupancy.csv",
        "centroids": args.reports_dir / "centroids.csv",
        "fit_summary": args.reports_dir / "fit_summary.csv",
    }
    pd.DataFrame(selection_rows).sort_values("k").to_csv(
        reports["model_selection"], index=False
    )
    pd.DataFrame(occupancy_rows).sort_values(["k", "split", "op_mode"]).to_csv(
        reports["occupancy"], index=False
    )
    pd.DataFrame(centroid_rows).sort_values(["k", "op_mode"]).to_csv(
        reports["centroids"], index=False
    )
    pd.DataFrame(fit_summary_rows).to_csv(reports["fit_summary"], index=False)

    config = {
        "study_id": STUDY_ID,
        "split_manifest_id": manifest_id,
        "source_dataset_sha256": manifest["dataset"]["sha256"],
        "input_hashes": {
            "train_csv": sha256_file(args.splits_dir / "train.csv"),
            "validation_csv": sha256_file(args.splits_dir / "validation.csv"),
        },
        "inputs": {
            "train_rows": len(train),
            "train_engines": train["engine"].nunique(),
            "validation_rows": len(validation),
            "validation_engines": validation["engine"].nunique(),
            "test_csv_opened_by_study": False,
        },
        "fit_policy": {
            "global_sensor_scaler": "first_fraction_rows_of_training_engines_only",
            "operating_setting_scaler": "all_rows_of_training_engines_only",
            "kmeans": "all_rows_of_training_engines_only",
            "per_mode_sensor_scalers": "first_fraction_rows_of_training_engines_only",
            "false_healthy_mask_interpretation": "unlabeled_not_known_anomaly",
            "rare_mode_fallback": "global_healthy_training_sensor_scaler",
        },
        "parameters": {
            "healthy_fraction": args.healthy_fraction,
            "candidate_k": candidate_k,
            "seed": args.seed,
            "n_init": args.n_init,
            "min_mode_fit_rows": args.min_mode_fit_rows,
            "silhouette_sample_size": args.silhouette_sample_size,
            "stability_seeds": list(args.stability_seeds),
            "stability_engine_fraction": args.stability_engine_fraction,
            "stability_n_init": args.stability_n_init,
        },
        "test_access_log": [
            {
                "stage": "preimplementation_schema_check",
                "access": "aggregate row/engine counts and op1-op3 ranges only",
                "used_for_candidate_fit_or_selection": False,
            }
        ],
        "outputs": {
            "reports": {
                name: repo_relative_posix(path, repo_root)
                for name, path in reports.items()
            },
            "candidate_models_dir": repo_relative_posix(args.models_dir, repo_root),
            "candidate_processed_dir": repo_relative_posix(
                args.processed_dir, repo_root
            ),
            "test_outputs_created": False,
        },
        "package_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "selection_status": "pending_human_decision_gate_2",
    }
    _write_json(config, args.config_output)

    print(
        {
            "study_id": STUDY_ID,
            "manifest_id": manifest_id,
            "candidates": ["p0_global", *[f"p1_k{k}" for k in candidate_k]],
            "model_selection_report": repo_relative_posix(
                reports["model_selection"], repo_root
            ),
            "test_csv_opened_by_study": False,
            "selection_status": config["selection_status"],
        }
    )


if __name__ == "__main__":
    main()
