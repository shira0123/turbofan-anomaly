"""Traceable window metadata independent of learned preprocessing and labels."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

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

P1_K6_ENDPOINT_CONTEXT_SEMANTICS = "p1_k6_endpoint_cycle_mode_v1"
P1_K6_OPERATING_MODES = frozenset(range(6))


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


def assign_endpoint_operating_modes(
    window_metadata: pd.DataFrame,
    cycle_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Derive P1/K=6 window context from the mode at each window endpoint.

    The source metadata is copied and never mutated.  No sensor values participate in
    the assignment: ``(engine, end_cycle)`` is joined directly to the registered
    cycle-level ``(engine, cycle, op_mode)`` key.
    """
    required_windows = {"window_id", "engine", "end_cycle", "op_mode"}
    missing_windows = required_windows - set(window_metadata.columns)
    if missing_windows:
        raise ValueError(
            f"Missing window-context columns: {sorted(missing_windows)}"
        )
    required_cycles = {"engine", "cycle", "op_mode"}
    missing_cycles = required_cycles - set(cycle_frame.columns)
    if missing_cycles:
        raise ValueError(f"Missing cycle-context columns: {sorted(missing_cycles)}")
    if window_metadata.empty:
        raise ValueError("Cannot derive endpoint context for empty window metadata")
    if window_metadata["window_id"].isna().any() or window_metadata[
        "window_id"
    ].duplicated().any():
        raise ValueError("Window IDs must be non-null and unique")
    if not window_metadata["op_mode"].isna().all():
        raise ValueError("Original window metadata must have an unassigned op_mode")
    if cycle_frame.duplicated(["engine", "cycle"]).any():
        raise ValueError("Cycle context contains duplicate endpoint keys")

    numeric_modes = pd.to_numeric(cycle_frame["op_mode"], errors="coerce").to_numpy(
        dtype=float
    )
    if not np.isfinite(numeric_modes).all() or not np.equal(
        numeric_modes, np.floor(numeric_modes)
    ).all():
        raise ValueError("Cycle context operating modes must be finite integers")
    integer_modes = numeric_modes.astype(int)
    invalid_modes = set(integer_modes) - P1_K6_OPERATING_MODES
    if invalid_modes:
        raise ValueError(
            f"Cycle context contains invalid P1/K=6 modes: {sorted(invalid_modes)}"
        )

    source_columns = list(window_metadata.columns)
    windows = window_metadata.copy(deep=True)
    windows["_window_context_order"] = np.arange(len(windows), dtype=np.int64)
    endpoints = cycle_frame[["engine", "cycle"]].copy()
    endpoints["_endpoint_op_mode"] = integer_modes
    endpoints = endpoints.rename(columns={"cycle": "end_cycle"})
    merged = windows.merge(
        endpoints,
        on=["engine", "end_cycle"],
        how="left",
        sort=False,
        validate="many_to_one",
        indicator=True,
    )
    if (merged["_merge"] != "both").any():
        missing = int((merged["_merge"] != "both").sum())
        raise ValueError(f"Window context is missing {missing} endpoint assignments")
    merged = merged.sort_values("_window_context_order", kind="stable")
    merged["op_mode"] = pd.array(merged["_endpoint_op_mode"], dtype="Int64")
    result = merged[source_columns].reset_index(drop=True)
    if result["window_id"].tolist() != window_metadata["window_id"].tolist():
        raise RuntimeError("Endpoint assignment changed window ordering")
    return result


def validate_p1_k6_mode_coverage(
    training_metadata: pd.DataFrame,
    validation_metadata: pd.DataFrame,
    eligible_training: np.ndarray | pd.Series,
    *,
    minimum_eligible_training_windows_per_mode: int = 100,
    expected_eligible_training_windows: int | None = None,
) -> dict[int, int]:
    """Validate exact six-mode coverage and eligible-training occupancy."""
    eligible = np.asarray(eligible_training, dtype=bool)
    if eligible.shape != (len(training_metadata),):
        raise ValueError("Eligible-training mask is not metadata-aligned")
    if expected_eligible_training_windows is not None and int(eligible.sum()) != int(
        expected_eligible_training_windows
    ):
        raise ValueError("Eligible-training window count differs from registration")
    for metadata, split in (
        (training_metadata, "train"),
        (validation_metadata, "validation"),
    ):
        numeric = pd.to_numeric(metadata["op_mode"], errors="coerce").to_numpy(
            dtype=float
        )
        if not np.isfinite(numeric).all() or not np.equal(
            numeric, np.floor(numeric)
        ).all():
            raise ValueError(f"{split} operating modes must be finite integers")
        modes = set(numeric.astype(int))
        if modes != P1_K6_OPERATING_MODES:
            raise ValueError(f"{split} must contain exactly the six P1/K=6 modes")
    counts = (
        training_metadata.loc[eligible, "op_mode"].astype(int).value_counts().to_dict()
    )
    if set(counts) != P1_K6_OPERATING_MODES:
        raise ValueError("Eligible training must contain exactly the six P1/K=6 modes")
    if min(counts.values()) < int(minimum_eligible_training_windows_per_mode):
        raise ValueError("An eligible-training mode has insufficient window coverage")
    return {int(mode): int(counts[mode]) for mode in sorted(counts)}


def materialize_endpoint_window_context(
    *,
    original_metadata_path: Path,
    cycle_frame_path: Path,
    destination_path: Path,
    expected_original_sha256: str,
    expected_cycle_frame_sha256: str,
) -> str:
    """Write derived endpoint context atomically while preserving source bytes."""

    def raw_sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    original_path = Path(original_metadata_path)
    cycle_path = Path(cycle_frame_path)
    destination = Path(destination_path)
    original_before = raw_sha256(original_path)
    if original_before != expected_original_sha256:
        raise ValueError("Original window-metadata hash differs from registration")
    if raw_sha256(cycle_path) != expected_cycle_frame_sha256:
        raise ValueError("P1/K=6 cycle-frame hash differs from registration")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite derived metadata: {destination}")

    derived = assign_endpoint_operating_modes(
        pd.read_csv(original_path), pd.read_csv(cycle_path)
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    if temporary.exists():
        raise FileExistsError(f"Refusing stale derived-metadata temporary: {temporary}")
    try:
        derived.to_csv(temporary, index=False, lineterminator="\n")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    if raw_sha256(original_path) != original_before:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Original window metadata changed during derivation")
    return raw_sha256(destination)
