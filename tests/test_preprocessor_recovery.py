from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from turbofan_anomaly.data.io import FD002_COLUMNS
from turbofan_anomaly.data.preprocessing import (
    RegimeSensorPreprocessor,
    load_preprocessor,
    save_preprocessor,
)
from turbofan_anomaly.workflows.recover_p1_preprocessor import (
    DEFAULT_PROTOCOL,
    compare_arrays,
    compare_cycle_frames,
    derive_canonical_mode_mapping,
    reconstruct_training_partition,
    select_recovery_route,
    validate_recovery_protocol,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _synthetic_source() -> pd.DataFrame:
    rows = []
    settings = (
        (-10.0, -1.0, 1.0),
        (-6.0, -0.5, 2.0),
        (-2.0, 0.0, 3.0),
        (2.0, 0.5, 4.0),
        (6.0, 1.0, 5.0),
        (10.0, 1.5, 6.0),
    )
    for engine, operating in enumerate(settings, start=1):
        for cycle in range(1, 13):
            sensors = [engine * 100.0 + cycle + index / 100.0 for index in range(21)]
            rows.append([engine, cycle, *operating, *sensors])
    return pd.DataFrame(rows, columns=FD002_COLUMNS)


def _write_source(frame: pd.DataFrame, path: Path) -> tuple[int, str]:
    frame.to_csv(path, sep=" ", header=False, index=False, lineterminator="\n")
    raw = path.read_bytes()
    return len(raw), hashlib.sha256(raw).hexdigest()


def _synthetic_manifest(frame: pd.DataFrame) -> dict:
    records = []
    roles = {1: "train", 2: "train", 3: "validation", 4: "validation", 5: "test", 6: "test"}
    for engine, role in roles.items():
        count = int((frame["engine"] == engine).sum())
        records.append({"engine": engine, "split": role, "cycle_count": count, "max_cycle": count})
    return {
        "manifest_id": "synthetic",
        "dataset": {"rows": len(frame)},
        "engines": records,
    }


def _synthetic_protocol(path: Path, frame: pd.DataFrame) -> dict:
    size, digest = _write_source(frame, path)
    return {
        "source_lineage_correction": {
            "authorized_local_source": {"size_bytes": size, "sha256": digest}
        },
        "frozen_partition": {
            "training_engine_ids": [1, 2],
            "expected_source_engines": 6,
            "expected_training_rows": 24,
        },
        "access_boundary": {
            "raw_run_to_failure_source_opened_for_partition_reconstruction": True,
            "internal_held_out_split_artifact_opened": False,
            "official_nasa_test_artifact_opened": False,
            "held_out_rows_retained": False,
            "held_out_rows_summarized": False,
            "held_out_rows_exported": False,
            "held_out_rows_used_for_fit_selection_or_evaluation": False,
            "confirmatory_evaluation_executed": False,
        },
    }


def test_registered_recovery_protocol_is_frozen_before_execution() -> None:
    protocol = json.loads((REPO_ROOT / DEFAULT_PROTOCOL).read_text(encoding="utf-8"))
    validate_recovery_protocol(protocol)
    assert len(protocol["frozen_partition"]["training_engine_ids"]) == 156
    assert protocol["status"] == "registered_before_project_data_fitting"
    assert protocol["frozen_gate_4_candidate"].endswith("persistence_8")


def test_partition_reconstruction_filters_fail_closed_and_preserves_order(tmp_path: Path) -> None:
    source = _synthetic_source()
    path = tmp_path / "source.txt"
    protocol = _synthetic_protocol(path, source)
    retained, audit = reconstruct_training_partition(
        path, _synthetic_manifest(source), protocol, chunk_size=7
    )
    assert retained["engine"].unique().tolist() == [1, 2]
    assert len(retained) == 24
    assert retained[["engine", "cycle"]].values.tolist() == sorted(
        retained[["engine", "cycle"]].values.tolist()
    )
    assert audit["held_out_rows_retained"] is False
    assert audit["held_out_rows_used_for_fit_selection_or_evaluation"] is False


def test_partition_reconstruction_rejects_source_hash_failure(tmp_path: Path) -> None:
    source = _synthetic_source()
    path = tmp_path / "source.txt"
    protocol = _synthetic_protocol(path, source)
    protocol["source_lineage_correction"]["authorized_local_source"]["sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="SHA-256"):
        reconstruct_training_partition(path, _synthetic_manifest(source), protocol)


def test_partition_reconstruction_rejects_unknown_engine_and_count_drift(tmp_path: Path) -> None:
    source = _synthetic_source()
    source.loc[source.index[-1], "engine"] = 99
    path = tmp_path / "source.txt"
    protocol = _synthetic_protocol(path, source)
    with pytest.raises(RuntimeError, match="unknown engine"):
        reconstruct_training_partition(path, _synthetic_manifest(_synthetic_source()), protocol)

    source = _synthetic_source()
    path = tmp_path / "source2.txt"
    protocol = _synthetic_protocol(path, source)
    protocol["frozen_partition"]["expected_training_rows"] = 23
    with pytest.raises(RuntimeError, match="row count"):
        reconstruct_training_partition(path, _synthetic_manifest(source), protocol)


def test_partition_reconstruction_rejects_duplicate_or_unordered_keys(tmp_path: Path) -> None:
    source = _synthetic_source()
    source.loc[1, "cycle"] = 1
    path = tmp_path / "source.txt"
    protocol = _synthetic_protocol(path, source)
    with pytest.raises(RuntimeError, match="duplicate or unordered"):
        reconstruct_training_partition(path, _synthetic_manifest(source), protocol)


def test_recovery_routes_preserve_missing_legacy_hash() -> None:
    legacy = "a" * 64
    assert select_recovery_route(legacy, legacy) == "route_a_byte_exact"
    assert select_recovery_route("b" * 64, legacy) == "route_b_governed_semantic_reconstruction"


def test_cluster_label_permutation_is_training_only_and_exact() -> None:
    raw = np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
    registered = np.array([3, 3, 5, 5, 0, 0, 2, 2, 1, 1, 4, 4])
    mapping = derive_canonical_mode_mapping(raw, registered)
    assert mapping == {0: 3, 1: 5, 2: 0, 3: 2, 4: 1, 5: 4}
    broken = registered.copy()
    broken[1] = 2
    with pytest.raises(RuntimeError, match="not a label permutation"):
        derive_canonical_mode_mapping(raw, broken)


def test_six_mode_fit_mapping_and_reload_use_training_engines_only(tmp_path: Path) -> None:
    frame = _synthetic_source()
    train = frame[frame["engine"].isin([1, 2, 3, 4, 5, 6])].reset_index(drop=True)
    validation = copy.deepcopy(train)
    validation["engine"] += 100
    model = RegimeSensorPreprocessor(
        split_manifest_id="synthetic",
        n_clusters=6,
        healthy_fraction=0.5,
        random_state=42,
        n_init=20,
        min_mode_fit_rows=1,
    ).fit(train)
    assert set(model.predict_raw_modes(train)) == set(range(6))
    mapping = {mode: 5 - mode for mode in range(6)}
    model.set_canonical_mode_mapping(mapping)
    before_fit_ids = model.fit_engine_ids_
    transformed_validation = model.transform(validation)
    assert model.fit_engine_ids_ == before_fit_ids == (1, 2, 3, 4, 5, 6)
    assert set(transformed_validation["op_mode"]) == set(range(6))
    artifact = tmp_path / "p1.joblib"
    save_preprocessor(model, artifact)
    loaded, metadata = load_preprocessor(artifact, expected_split_manifest_id="synthetic")
    assert metadata["canonical_mode_mapping"] == mapping
    pd.testing.assert_frame_equal(loaded.transform(validation), transformed_validation)


def test_transformed_frame_and_sequence_tolerances_are_fail_closed() -> None:
    frame = _synthetic_source().iloc[:2].copy()
    frame["op_mode"] = [0, 1]
    report = compare_cycle_frames(frame, frame.copy(), rtol=1e-10, atol=1e-12)
    assert report["maximum_absolute_sensor_difference"] == 0.0
    changed = frame.copy()
    changed.loc[0, "sensor_1"] += 1e-3
    with pytest.raises(RuntimeError, match="exceed tolerance"):
        compare_cycle_frames(changed, frame, rtol=1e-10, atol=1e-12)

    array = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    assert compare_arrays(array, array.copy(), rtol=1e-7, atol=1e-7)["exact"] is True
    changed_array = array.copy()
    changed_array[0, 0, 0] += 1e-3
    with pytest.raises(RuntimeError, match="exceed tolerance"):
        compare_arrays(changed_array, array, rtol=1e-7, atol=1e-7)
