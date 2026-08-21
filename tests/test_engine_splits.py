from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.split_manifest import (
    SPLIT_NAMES,
    build_split_manifest,
    manifest_json,
    write_split_csvs,
)


def _synthetic_engine_frame(engine_count: int = 50) -> pd.DataFrame:
    rows = []
    for engine in range(1, engine_count + 1):
        cycle_count = 39 + engine
        rows.extend(
            {"engine": engine, "cycle": cycle}
            for cycle in range(1, cycle_count + 1)
        )
    return pd.DataFrame(rows)


def _build(frame: pd.DataFrame, source_path: Path, seed: int = 42) -> dict:
    return build_split_manifest(
        frame=frame,
        source_path=source_path,
        manifest_id="synthetic-primary-v1",
        ratios={"train": 0.60, "validation": 0.20, "test": 0.20},
        seed=seed,
        n_strata=5,
    )


def test_engine_split_is_deterministic_complete_and_disjoint(tmp_path: Path) -> None:
    frame = _synthetic_engine_frame()
    source_path = tmp_path / "synthetic.txt"
    source_path.write_text("stable synthetic source\n", encoding="utf-8")

    first = _build(frame, source_path)
    second = _build(frame, source_path)

    assert manifest_json(first) == manifest_json(second)
    assert first["split"]["counts"] == {"train": 30, "validation": 10, "test": 10}

    assignments = pd.DataFrame(first["engines"])
    assert assignments["engine"].is_unique
    assert set(assignments["engine"]) == set(range(1, 51))
    assert assignments["stratum"].value_counts().sort_index().to_dict() == {
        0: 10,
        1: 10,
        2: 10,
        3: 10,
        4: 10,
    }

    engine_sets = {
        split: set(assignments.loc[assignments["split"] == split, "engine"])
        for split in SPLIT_NAMES
    }
    assert engine_sets["train"].isdisjoint(engine_sets["validation"])
    assert engine_sets["train"].isdisjoint(engine_sets["test"])
    assert engine_sets["validation"].isdisjoint(engine_sets["test"])


def test_different_seed_changes_assignment(tmp_path: Path) -> None:
    frame = _synthetic_engine_frame()
    source_path = tmp_path / "synthetic.txt"
    source_path.write_text("stable synthetic source\n", encoding="utf-8")

    first = pd.DataFrame(_build(frame, source_path, seed=42)["engines"])
    second = pd.DataFrame(_build(frame, source_path, seed=43)["engines"])
    comparison = first[["engine", "split"]].merge(
        second[["engine", "split"]], on="engine", suffixes=("_first", "_second")
    )

    assert (comparison["split_first"] != comparison["split_second"]).any()


def test_materialized_split_csvs_exactly_partition_rows(tmp_path: Path) -> None:
    frame = _synthetic_engine_frame()
    source_path = tmp_path / "synthetic.txt"
    source_path.write_text("stable synthetic source\n", encoding="utf-8")
    manifest = _build(frame, source_path)

    outputs = write_split_csvs(frame, manifest, tmp_path / "splits")
    materialized = {name: pd.read_csv(path) for name, path in outputs.items()}

    assert sum(len(split_frame) for split_frame in materialized.values()) == len(frame)
    observed_rows = set().union(
        *(
            set(map(tuple, split_frame[["engine", "cycle"]].to_numpy()))
            for split_frame in materialized.values()
        )
    )
    assert observed_rows == set(map(tuple, frame[["engine", "cycle"]].to_numpy()))
    assert all(
        set(materialized[left]["engine"]).isdisjoint(set(materialized[right]["engine"]))
        for index, left in enumerate(SPLIT_NAMES)
        for right in SPLIT_NAMES[index + 1 :]
    )
