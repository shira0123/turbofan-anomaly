"""Build sequence arrays that remain aligned with persisted window metadata."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from turbofan_anomaly.data.preprocessing import SENSOR_COLUMNS


def build_window_array(
    frame: pd.DataFrame,
    metadata: pd.DataFrame,
    *,
    sensor_columns: Sequence[str] = SENSOR_COLUMNS,
    dtype: np.dtype = np.dtype("float32"),
) -> np.ndarray:
    """Return ``[windows, time, sensors]`` aligned to metadata row order."""
    required_frame = {"engine", "cycle", *sensor_columns}
    missing_frame = required_frame - set(frame.columns)
    if missing_frame:
        raise ValueError(f"Missing sequence source columns: {sorted(missing_frame)}")
    required_metadata = {
        "window_id",
        "engine",
        "start_cycle",
        "end_cycle",
        "window_size",
    }
    missing_metadata = required_metadata - set(metadata.columns)
    if missing_metadata:
        raise ValueError(f"Missing sequence metadata columns: {sorted(missing_metadata)}")
    if metadata.empty:
        raise ValueError("Cannot build an empty sequence array")
    if metadata["window_id"].duplicated().any():
        raise ValueError("window_id values must be unique")
    if metadata["window_size"].nunique() != 1:
        raise ValueError("All windows must use one window_size")

    window_size = int(metadata["window_size"].iloc[0])
    sequences = np.empty(
        (len(metadata), window_size, len(sensor_columns)), dtype=dtype
    )
    source_engines = set(frame["engine"].astype(int).unique())
    metadata_engines = set(metadata["engine"].astype(int).unique())
    if metadata_engines - source_engines:
        raise ValueError("Window metadata references an engine absent from the source")

    for engine, metadata_engine in metadata.groupby("engine", sort=False):
        source_engine = frame[frame["engine"] == engine].sort_values("cycle")
        cycles = source_engine["cycle"].to_numpy(dtype=int)
        if len(cycles) > 1 and not np.all(np.diff(cycles) == 1):
            raise ValueError(f"Engine {engine} has non-consecutive cycles")
        sensor_values = source_engine.loc[:, list(sensor_columns)].to_numpy(dtype=dtype)
        first_cycle = int(cycles[0])

        for row_index, row in metadata_engine.iterrows():
            start_offset = int(row["start_cycle"]) - first_cycle
            end_offset = start_offset + window_size
            if start_offset < 0 or end_offset > len(source_engine):
                raise ValueError(f"Window {row['window_id']} lies outside engine data")
            observed_start = int(cycles[start_offset])
            observed_end = int(cycles[end_offset - 1])
            if (
                observed_start != int(row["start_cycle"])
                or observed_end != int(row["end_cycle"])
            ):
                raise ValueError(f"Window {row['window_id']} cycle bounds do not align")
            sequences[metadata.index.get_loc(row_index)] = sensor_values[
                start_offset:end_offset
            ]

    if not np.isfinite(sequences).all():
        raise ValueError("Sequence array contains non-finite sensor values")
    return sequences


def summary_features(sequences: np.ndarray) -> np.ndarray:
    """Convert ``[N,T,S]`` windows to fixed ``[N,3S]`` classical features."""
    if sequences.ndim != 3:
        raise ValueError("Expected sequences with shape [windows, time, sensors]")
    mean_features = sequences.mean(axis=1)
    standard_deviation_features = sequences.std(axis=1)
    slope_features = sequences[:, -1, :] - sequences[:, 0, :]
    features = np.concatenate(
        [mean_features, standard_deviation_features, slope_features], axis=1
    )
    return features.astype(np.float32, copy=False)
