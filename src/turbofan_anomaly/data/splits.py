"""Deterministic, engine-disjoint split manifests for C-MAPSS FD002."""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split

from turbofan_anomaly.data.io import (
    FD002_COLUMNS,
    load_fd002,
    validate_fd002_frame,
)
from turbofan_anomaly.evaluation.provenance import sha256_file


SPLIT_NAMES = ("train", "validation", "test")


def summarize_engines(frame: pd.DataFrame) -> pd.DataFrame:
    """Build the engine-level characteristics allowed for split balancing."""
    validate_fd002_frame(frame)
    summary = (
        frame.groupby("engine", sort=True)["cycle"]
        .agg(cycle_count="size", max_cycle="max")
        .reset_index()
        .sort_values("engine")
        .reset_index(drop=True)
    )
    summary[["engine", "cycle_count", "max_cycle"]] = summary[
        ["engine", "cycle_count", "max_cycle"]
    ].astype(int)
    return summary


def _validate_ratios(ratios: Mapping[str, float]) -> dict[str, float]:
    if set(ratios) != set(SPLIT_NAMES):
        raise ValueError(f"Ratios must define exactly: {SPLIT_NAMES}")
    normalized = {name: float(ratios[name]) for name in SPLIT_NAMES}
    if any(value <= 0.0 for value in normalized.values()):
        raise ValueError("All split ratios must be positive")
    if not np.isclose(sum(normalized.values()), 1.0):
        raise ValueError("Split ratios must sum to 1.0")
    return normalized


def assign_engine_splits(
    engine_summary: pd.DataFrame,
    ratios: Mapping[str, float],
    seed: int,
    n_strata: int = 5,
) -> pd.DataFrame:
    """Assign whole engines using max-cycle rank strata and fixed seeds.

    The secondary seed is deterministically derived as ``seed + 1``. Explicit
    engine assignments are persisted in the manifest, so downstream work never
    needs to recreate a split from library behavior alone.
    """
    ratios = _validate_ratios(ratios)
    if n_strata < 2:
        raise ValueError("n_strata must be at least 2")
    if len(engine_summary) < n_strata * 4:
        raise ValueError(
            "Not enough engines for two-stage stratification; "
            f"need at least {n_strata * 4}, found {len(engine_summary)}"
        )

    assignments = engine_summary.sort_values("engine").reset_index(drop=True).copy()
    ranks = assignments["max_cycle"].rank(method="first")
    assignments["stratum"] = pd.qcut(ranks, q=n_strata, labels=False).astype(int)

    held_out_ratio = ratios["validation"] + ratios["test"]
    indices = assignments.index.to_numpy()
    train_idx, held_out_idx = train_test_split(
        indices,
        test_size=held_out_ratio,
        random_state=int(seed),
        shuffle=True,
        stratify=assignments["stratum"],
    )

    validation_share = ratios["validation"] / held_out_ratio
    validation_idx, test_idx = train_test_split(
        held_out_idx,
        train_size=validation_share,
        random_state=int(seed) + 1,
        shuffle=True,
        stratify=assignments.loc[held_out_idx, "stratum"],
    )

    assignments["split"] = ""
    assignments.loc[train_idx, "split"] = "train"
    assignments.loc[validation_idx, "split"] = "validation"
    assignments.loc[test_idx, "split"] = "test"
    assignments = assignments.sort_values("engine").reset_index(drop=True)

    validate_assignments(assignments, engine_summary["engine"].tolist())
    return assignments


def validate_assignments(assignments: pd.DataFrame, expected_engines: list[int]) -> None:
    """Fail if an engine is missing, duplicated, or assigned to an unknown split."""
    required = {"engine", "split", "cycle_count", "max_cycle", "stratum"}
    missing = required - set(assignments.columns)
    if missing:
        raise ValueError(f"Missing assignment columns: {sorted(missing)}")
    if assignments["engine"].duplicated().any():
        raise ValueError("An engine appears more than once in split assignments")
    if set(assignments["split"]) != set(SPLIT_NAMES):
        raise ValueError("Assignments must contain train, validation, and test splits")
    if set(assignments["engine"].astype(int)) != set(map(int, expected_engines)):
        raise ValueError("Split assignments do not exactly cover the source engines")

    engine_sets = {
        name: set(assignments.loc[assignments["split"] == name, "engine"].astype(int))
        for name in SPLIT_NAMES
    }
    for index, left in enumerate(SPLIT_NAMES):
        for right in SPLIT_NAMES[index + 1 :]:
            if engine_sets[left] & engine_sets[right]:
                raise ValueError(f"Engine overlap detected between {left} and {right}")


def build_split_manifest(
    frame: pd.DataFrame,
    source_path: Path,
    manifest_id: str,
    ratios: Mapping[str, float],
    seed: int,
    n_strata: int = 5,
) -> dict:
    """Create a fully explicit and deterministically serializable manifest."""
    ratios = _validate_ratios(ratios)
    summary = summarize_engines(frame)
    assignments = assign_engine_splits(summary, ratios, seed, n_strata=n_strata)

    engine_records = [
        {
            "engine": int(row.engine),
            "split": str(row.split),
            "cycle_count": int(row.cycle_count),
            "max_cycle": int(row.max_cycle),
            "stratum": int(row.stratum),
        }
        for row in assignments.itertuples(index=False)
    ]
    counts = {
        name: int((assignments["split"] == name).sum()) for name in SPLIT_NAMES
    }

    return {
        "manifest_version": 1,
        "manifest_id": manifest_id,
        "generator": {
            "module": "turbofan_anomaly.data.splits",
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "dataset": {
            "path": source_path.as_posix(),
            "sha256": sha256_file(source_path),
            "rows": int(len(frame)),
            "columns": int(len(frame.columns)),
            "engines": int(len(summary)),
        },
        "split": {
            "method": "seeded_stratified_engine_split",
            "ratios": ratios,
            "seed": int(seed),
            "secondary_seed": int(seed) + 1,
            "counts": counts,
            "stratification": {
                "field": "max_cycle",
                "bins": int(n_strata),
                "method": "rank_then_equal_frequency_bins",
                "tie_break": "engine_id_order",
                "use": "split_balancing_only_not_model_input",
            },
        },
        "evaluation_boundary": {
            "official_fd002_test": "external_generalization_only_after_pipeline_freeze",
            "source_used_for_internal_split": source_path.name,
        },
        "artifact_policy": {
            "required_split_manifest_id": manifest_id,
            "artifacts_without_matching_manifest_id": "legacy_incompatible_with_validation_or_test",
        },
        "engines": engine_records,
    }


def manifest_json(manifest: dict) -> str:
    """Serialize without timestamps so identical inputs produce identical bytes."""
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_manifest(manifest: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest_json(manifest), encoding="utf-8")


def write_split_csvs(frame: pd.DataFrame, manifest: dict, output_dir: Path) -> dict[str, Path]:
    """Materialize row-level split CSVs from explicit engine assignments."""
    assignments = pd.DataFrame(manifest["engines"])
    validate_assignments(assignments, sorted(frame["engine"].astype(int).unique().tolist()))
    split_by_engine = assignments.set_index("engine")["split"].to_dict()

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    combined_rows = 0
    for split_name in SPLIT_NAMES:
        engine_ids = {
            engine for engine, split in split_by_engine.items() if split == split_name
        }
        split_frame = frame[frame["engine"].isin(engine_ids)].reset_index(drop=True)
        path = output_dir / f"{split_name}.csv"
        split_frame.to_csv(path, index=False)
        outputs[split_name] = path
        combined_rows += len(split_frame)

    if combined_rows != len(frame):
        raise RuntimeError("Materialized split row counts do not partition the source data")
    return outputs
