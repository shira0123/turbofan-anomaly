from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.preprocessing import SENSOR_COLUMNS
from src.data.window_arrays import build_window_array, summary_features
from src.data.window_metadata import create_window_metadata


def _frame() -> pd.DataFrame:
    rows = []
    for engine, cycle_count in [(1, 31), (2, 30)]:
        for cycle in range(1, cycle_count + 1):
            row = {"engine": engine, "cycle": cycle}
            row.update(
                {
                    sensor: float(engine * 1000 + cycle + sensor_index)
                    for sensor_index, sensor in enumerate(SENSOR_COLUMNS)
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def test_window_array_aligns_exactly_with_metadata_order() -> None:
    frame = _frame()
    metadata = create_window_metadata(
        frame,
        split="train",
        manifest_id="split-v1",
        source_dataset_sha256="a" * 64,
        window_size=30,
    )
    sequences = build_window_array(frame, metadata)

    assert sequences.shape == (3, 30, 21)
    assert sequences.dtype == np.float32
    assert sequences[0, 0, 0] == 1001.0
    assert sequences[0, -1, 0] == 1030.0
    assert sequences[1, 0, 0] == 1002.0
    assert sequences[2, 0, 0] == 2001.0

    features = summary_features(sequences)
    assert features.shape == (3, 63)
    assert features[0, -21] == 29.0


def test_window_array_rejects_misaligned_cycle_bounds() -> None:
    frame = _frame()
    metadata = create_window_metadata(
        frame,
        split="train",
        manifest_id="split-v1",
        source_dataset_sha256="b" * 64,
        window_size=30,
    )
    metadata.loc[0, "end_cycle"] = 29

    try:
        build_window_array(frame, metadata)
    except ValueError as error:
        assert "cycle bounds do not align" in str(error)
    else:
        raise AssertionError("Expected misaligned metadata to be rejected")
