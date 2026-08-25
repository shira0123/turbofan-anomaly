from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from turbofan_anomaly.data.preprocessing import (
    OP_COLUMNS,
    SENSOR_COLUMNS,
    GlobalSensorPreprocessor,
    RegimeSensorPreprocessor,
    healthy_training_mask,
    load_preprocessor,
    save_preprocessor,
)


def _row(engine: int, cycle: int, op_value: float, sensor_value: float) -> dict:
    row = {
        "engine": engine,
        "cycle": cycle,
        "op1": op_value,
        "op2": op_value / 10,
        "op3": 60.0 if op_value < 5 else 100.0,
    }
    row.update({sensor: sensor_value + index for index, sensor in enumerate(SENSOR_COLUMNS)})
    return row


def _two_regime_train_frame() -> pd.DataFrame:
    rows = []
    for engine in range(1, 5):
        op_value = 0.0 if engine <= 2 else 10.0
        for cycle in range(1, 11):
            sensor_value = engine * 10 + cycle if cycle <= 3 else 10_000 + cycle
            rows.append(_row(engine, cycle, op_value, sensor_value))
    return pd.DataFrame(rows)


def test_global_scaler_fits_only_healthy_assumption_training_rows() -> None:
    train = _two_regime_train_frame()
    healthy_mask = healthy_training_mask(train, 0.30)
    expected_mean = train.loc[healthy_mask, list(SENSOR_COLUMNS)].mean().to_numpy()

    preprocessor = GlobalSensorPreprocessor(
        split_manifest_id="split-v1", healthy_fraction=0.30
    ).fit(train)

    assert preprocessor.healthy_fit_row_count_ == 12
    assert np.allclose(preprocessor.sensor_scaler_.mean_, expected_mean)
    assert not np.allclose(
        preprocessor.sensor_scaler_.mean_, train[list(SENSOR_COLUMNS)].mean().to_numpy()
    )

    validation = pd.DataFrame([_row(99, 1, 50.0, 1_000_000.0)])
    mean_before = preprocessor.sensor_scaler_.mean_.copy()
    transformed = preprocessor.transform(validation)
    assert np.array_equal(preprocessor.sensor_scaler_.mean_, mean_before)
    assert transformed["engine"].tolist() == [99]
    assert transformed["cycle"].tolist() == [1]
    assert transformed["op_mode"].tolist() == [-1]


def test_regime_preprocessor_uses_training_state_and_preserves_rows() -> None:
    train = _two_regime_train_frame()
    preprocessor = RegimeSensorPreprocessor(
        split_manifest_id="split-v1",
        n_clusters=2,
        healthy_fraction=0.30,
        random_state=42,
        n_init=5,
        min_mode_fit_rows=1,
    ).fit(train)

    expected_op_mean = train[list(OP_COLUMNS)].mean().to_numpy()
    assert np.allclose(preprocessor.op_scaler_.mean_, expected_op_mean)
    assert sum(preprocessor.sensor_fit_rows_per_mode_.values()) == 12
    assert preprocessor.fallback_modes_ == ()

    transformed = preprocessor.transform(train)
    assert len(transformed) == len(train)
    assert transformed[["engine", "cycle", *OP_COLUMNS]].equals(
        train[["engine", "cycle", *OP_COLUMNS]]
    )
    assert set(transformed["op_mode"]) == {0, 1}
    assert not transformed[list(SENSOR_COLUMNS)].isna().any().any()

    repeated = RegimeSensorPreprocessor(
        split_manifest_id="split-v1",
        n_clusters=2,
        healthy_fraction=0.30,
        random_state=42,
        n_init=5,
        min_mode_fit_rows=1,
    ).fit(train).transform(train)
    assert np.array_equal(transformed["op_mode"].to_numpy(), repeated["op_mode"].to_numpy())
    assert np.allclose(
        transformed[list(SENSOR_COLUMNS)], repeated[list(SENSOR_COLUMNS)]
    )


def test_rare_mode_uses_global_training_only_fallback() -> None:
    train = pd.DataFrame(
        [
            _row(
                1,
                cycle,
                0.0 if cycle <= 3 else 10.0,
                float(cycle),
            )
            for cycle in range(1, 11)
        ]
    )
    preprocessor = RegimeSensorPreprocessor(
        split_manifest_id="split-v1",
        n_clusters=2,
        healthy_fraction=0.30,
        random_state=42,
        n_init=5,
        min_mode_fit_rows=1,
    ).fit(train)

    assert len(preprocessor.fallback_modes_) == 1
    fallback_mode = preprocessor.fallback_modes_[0]
    assert preprocessor.sensor_fit_rows_per_mode_[fallback_mode] == 0
    assert (
        preprocessor.sensor_scalers_per_mode_[fallback_mode]
        is preprocessor.global_sensor_scaler_
    )
    transformed = preprocessor.transform(train)
    assert not transformed[list(SENSOR_COLUMNS)].isna().any().any()


def test_preprocessing_artifact_round_trip_retains_manifest_id(tmp_path: Path) -> None:
    train = _two_regime_train_frame()
    preprocessor = GlobalSensorPreprocessor(
        split_manifest_id="fd002-primary-v1", healthy_fraction=0.30
    ).fit(train)
    path = tmp_path / "p0.joblib"

    save_preprocessor(preprocessor, path)
    loaded, metadata = load_preprocessor(
        path, expected_split_manifest_id="fd002-primary-v1"
    )

    assert metadata["split_manifest_id"] == "fd002-primary-v1"
    assert metadata["sensor_scaler_fit_rows"] == 12
    assert np.allclose(
        preprocessor.transform(train)[list(SENSOR_COLUMNS)],
        loaded.transform(train)[list(SENSOR_COLUMNS)],
    )
    with pytest.raises(ValueError, match="split manifest mismatch"):
        load_preprocessor(path, expected_split_manifest_id="different-split")
