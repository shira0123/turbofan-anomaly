from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from turbofan_anomaly.data.metadata import (
    assign_endpoint_operating_modes,
    materialize_endpoint_window_context,
    validate_p1_k6_mode_coverage,
)


def _windows(*, end_cycles: list[int], engine: int = 1) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "window_id": [f"w{index}" for index in range(len(end_cycles))],
            "engine": [engine] * len(end_cycles),
            "end_cycle": end_cycles,
            "op_mode": pd.array([pd.NA] * len(end_cycles), dtype="Int64"),
            "payload": list(range(len(end_cycles))),
        }
    )


def _cycles(modes: list[object], *, engine: int = 1) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "engine": [engine] * len(modes),
            "cycle": np.arange(1, len(modes) + 1),
            "op_mode": modes,
        }
    )


def test_endpoint_assignment_uses_final_cycle_for_mixed_mode_windows() -> None:
    windows = _windows(end_cycles=[3, 2])
    derived = assign_endpoint_operating_modes(windows, _cycles([0, 1, 2]))

    assert derived["window_id"].tolist() == ["w0", "w1"]
    assert derived["payload"].tolist() == [0, 1]
    assert derived["op_mode"].astype(int).tolist() == [2, 1]
    assert windows["op_mode"].isna().all()


def test_endpoint_assignment_rejects_missing_endpoint() -> None:
    with pytest.raises(ValueError, match="missing 1 endpoint"):
        assign_endpoint_operating_modes(
            _windows(end_cycles=[3]),
            _cycles([0, 1]),
        )


def test_endpoint_assignment_rejects_duplicate_endpoint_keys() -> None:
    cycles = pd.concat([_cycles([0, 1]), _cycles([1]).assign(cycle=2)])
    with pytest.raises(ValueError, match="duplicate endpoint keys"):
        assign_endpoint_operating_modes(_windows(end_cycles=[2]), cycles)


@pytest.mark.parametrize("invalid_mode", [np.nan, 1.5, -1, 6, "not-a-mode"])
def test_endpoint_assignment_rejects_invalid_p1_k6_modes(
    invalid_mode: object,
) -> None:
    with pytest.raises(ValueError, match="operating modes|invalid P1/K=6 modes"):
        assign_endpoint_operating_modes(
            _windows(end_cycles=[1]),
            _cycles([invalid_mode]),
        )


def test_six_mode_coverage_requires_minimum_eligible_training_occupancy() -> None:
    training = pd.DataFrame({"op_mode": np.repeat(np.arange(6), 100)})
    validation = pd.DataFrame({"op_mode": np.arange(6)})
    counts = validate_p1_k6_mode_coverage(
        training,
        validation,
        np.ones(len(training), dtype=bool),
        minimum_eligible_training_windows_per_mode=100,
        expected_eligible_training_windows=600,
    )
    assert counts == {mode: 100 for mode in range(6)}

    sparse = np.ones(len(training), dtype=bool)
    sparse[599] = False
    with pytest.raises(ValueError, match="insufficient window coverage"):
        validate_p1_k6_mode_coverage(
            training,
            validation,
            sparse,
            minimum_eligible_training_windows_per_mode=100,
        )


def test_six_mode_coverage_rejects_missing_mode_in_either_split() -> None:
    training = pd.DataFrame({"op_mode": np.repeat(np.arange(6), 2)})
    validation = pd.DataFrame({"op_mode": np.arange(5)})
    with pytest.raises(ValueError, match="validation must contain exactly"):
        validate_p1_k6_mode_coverage(
            training,
            validation,
            np.ones(len(training), dtype=bool),
            minimum_eligible_training_windows_per_mode=1,
        )


def test_materialization_preserves_original_bytes_and_hash(tmp_path: Path) -> None:
    original = tmp_path / "window_metadata_train.csv"
    cycle_frame = tmp_path / "train.csv"
    destination = tmp_path / "window_context" / "train.csv"
    _windows(end_cycles=[2]).to_csv(original, index=False, lineterminator="\n")
    _cycles([0, 3]).to_csv(cycle_frame, index=False, lineterminator="\n")
    original_bytes = original.read_bytes()
    original_hash = hashlib.sha256(original_bytes).hexdigest()
    cycle_hash = hashlib.sha256(cycle_frame.read_bytes()).hexdigest()

    derived_hash = materialize_endpoint_window_context(
        original_metadata_path=original,
        cycle_frame_path=cycle_frame,
        destination_path=destination,
        expected_original_sha256=original_hash,
        expected_cycle_frame_sha256=cycle_hash,
    )

    assert original.read_bytes() == original_bytes
    assert hashlib.sha256(original.read_bytes()).hexdigest() == original_hash
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == derived_hash
    assert pd.read_csv(destination)["op_mode"].tolist() == [3]


def test_materialization_rejects_original_hash_drift_without_output(
    tmp_path: Path,
) -> None:
    original = tmp_path / "window_metadata_train.csv"
    cycle_frame = tmp_path / "train.csv"
    destination = tmp_path / "derived.csv"
    _windows(end_cycles=[1]).to_csv(original, index=False, lineterminator="\n")
    _cycles([0]).to_csv(cycle_frame, index=False, lineterminator="\n")
    cycle_hash = hashlib.sha256(cycle_frame.read_bytes()).hexdigest()

    with pytest.raises(ValueError, match="hash differs"):
        materialize_endpoint_window_context(
            original_metadata_path=original,
            cycle_frame_path=cycle_frame,
            destination_path=destination,
            expected_original_sha256="0" * 64,
            expected_cycle_frame_sha256=cycle_hash,
        )
    assert not destination.exists()
