"""Traceable window metadata independent of learned preprocessing and labels."""

from __future__ import annotations

import numpy as np
import pandas as pd


WINDOW_METADATA_COLUMNS = [
    "window_id",
    "engine",
    "start_cycle",
    "end_cycle",
    "midpoint_cycle",
    "max_cycle",
    "life_fraction_end",
    "window_size",
    "split",
    "split_manifest_id",
    "source_dataset_sha256",
    "op_mode",
    "label_policy_id",
    "label_state",
]


def _validate_window_source(frame: pd.DataFrame) -> None:
    missing = {"engine", "cycle"} - set(frame.columns)
    if missing:
        raise ValueError(f"Missing window source columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Cannot create window metadata from an empty split")
    if frame.duplicated(["engine", "cycle"]).any():
        raise ValueError("Duplicate (engine, cycle) rows found")


def create_window_metadata(
    frame: pd.DataFrame,
    *,
    split: str,
    manifest_id: str,
    source_dataset_sha256: str,
    window_size: int = 30,
) -> pd.DataFrame:
    """Create one auditable metadata record per engine-local sliding window.

    ``op_mode`` is deliberately null until Phase 2 supplies a mode learned from
    training engines. Likewise, no anomaly proxy is applied here: policy fields
    remain explicitly unassigned/unlabeled.
    """
    _validate_window_source(frame)
    if window_size < 1:
        raise ValueError("window_size must be positive")
    if not manifest_id:
        raise ValueError("manifest_id may not be empty")
    if len(source_dataset_sha256) != 64:
        raise ValueError("source_dataset_sha256 must be a 64-character SHA-256 digest")

    rows: list[dict] = []
    for engine, engine_frame in frame.groupby("engine", sort=True):
        ordered = engine_frame.sort_values("cycle")
        cycles = ordered["cycle"].to_numpy(dtype=int)
        if len(cycles) > 1 and not np.all(np.diff(cycles) == 1):
            raise ValueError(f"Engine {engine} has non-consecutive cycles")

        max_cycle = int(cycles[-1])
        number_of_windows = max(0, len(cycles) - window_size + 1)
        for local_start in range(number_of_windows):
            start_cycle = int(cycles[local_start])
            end_cycle = int(cycles[local_start + window_size - 1])
            midpoint_cycle = int(cycles[local_start + window_size // 2])
            window_id = (
                f"{manifest_id}:{split}:e{int(engine):03d}:"
                f"c{start_cycle:04d}-{end_cycle:04d}"
            )
            rows.append(
                {
                    "window_id": window_id,
                    "engine": int(engine),
                    "start_cycle": start_cycle,
                    "end_cycle": end_cycle,
                    "midpoint_cycle": midpoint_cycle,
                    "max_cycle": max_cycle,
                    "life_fraction_end": end_cycle / max_cycle,
                    "window_size": int(window_size),
                    "split": split,
                    "split_manifest_id": manifest_id,
                    "source_dataset_sha256": source_dataset_sha256,
                    "op_mode": pd.NA,
                    "label_policy_id": "unassigned",
                    "label_state": "unlabeled",
                }
            )

    metadata = pd.DataFrame(rows, columns=WINDOW_METADATA_COLUMNS)
    metadata["op_mode"] = pd.array(metadata["op_mode"], dtype="Int64")
    validate_window_metadata(metadata, frame, split=split, window_size=window_size)
    return metadata


def validate_window_metadata(
    metadata: pd.DataFrame,
    source_frame: pd.DataFrame,
    *,
    split: str,
    window_size: int,
) -> None:
    """Validate alignment, chronology, split identity, and unlabeled state."""
    missing = set(WINDOW_METADATA_COLUMNS) - set(metadata.columns)
    if missing:
        raise ValueError(f"Missing window metadata columns: {sorted(missing)}")

    expected_count = int(
        source_frame.groupby("engine", sort=True)
        .size()
        .map(lambda count: max(0, int(count) - window_size + 1))
        .sum()
    )
    if len(metadata) != expected_count:
        raise ValueError(
            f"Window count mismatch: expected {expected_count}, found {len(metadata)}"
        )
    if metadata["window_id"].duplicated().any():
        raise ValueError("window_id values must be unique")
    if not metadata.empty and set(metadata["split"]) != {split}:
        raise ValueError("Window metadata contains an unexpected split value")
    if not metadata.empty and not (metadata["window_size"] == window_size).all():
        raise ValueError("Window metadata contains an unexpected window size")
    if not metadata.empty and not (
        metadata["end_cycle"] - metadata["start_cycle"] + 1 == window_size
    ).all():
        raise ValueError("A window does not span the required consecutive cycles")
    if set(metadata["engine"].astype(int)) - set(source_frame["engine"].astype(int)):
        raise ValueError("Window metadata contains an engine absent from its source split")
    if not metadata["op_mode"].isna().all():
        raise ValueError("Phase 1 window metadata must not pre-assign op_mode")
    if not metadata.empty:
        if set(metadata["label_policy_id"]) != {"unassigned"}:
            raise ValueError("Phase 1 must not assign a label policy")
        if set(metadata["label_state"]) != {"unlabeled"}:
            raise ValueError("Phase 1 must not assign anomaly labels")

    max_cycles = source_frame.groupby("engine")["cycle"].max().astype(int).to_dict()
    if not metadata.empty:
        expected_max = metadata["engine"].map(max_cycles).astype(int)
        if not np.array_equal(metadata["max_cycle"].to_numpy(), expected_max.to_numpy()):
            raise ValueError("Window max_cycle does not match the source engine")
