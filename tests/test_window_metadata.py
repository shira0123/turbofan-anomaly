from __future__ import annotations

import pandas as pd
import pytest

from turbofan_anomaly.data.metadata import create_window_metadata


def _source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"engine": engine, "cycle": cycle}
            for engine, cycle_count in [(11, 31), (22, 30)]
            for cycle in range(1, cycle_count + 1)
        ]
    )


def test_window_metadata_preserves_engine_identity_and_chronology() -> None:
    source = _source_frame()
    metadata = create_window_metadata(
        source,
        split="validation",
        manifest_id="fd002-primary-v1",
        source_dataset_sha256="a" * 64,
        window_size=30,
    )

    assert len(metadata) == (31 - 30 + 1) + (30 - 30 + 1)
    assert metadata["window_id"].is_unique
    assert metadata[["engine", "start_cycle", "end_cycle"]].to_dict("records") == [
        {"engine": 11, "start_cycle": 1, "end_cycle": 30},
        {"engine": 11, "start_cycle": 2, "end_cycle": 31},
        {"engine": 22, "start_cycle": 1, "end_cycle": 30},
    ]
    assert metadata["midpoint_cycle"].tolist() == [16, 17, 16]
    assert metadata["max_cycle"].tolist() == [31, 31, 30]
    assert metadata["split"].tolist() == ["validation"] * 3
    assert metadata["op_mode"].isna().all()
    assert metadata["label_policy_id"].tolist() == ["unassigned"] * 3
    assert metadata["label_state"].tolist() == ["unlabeled"] * 3

    for row in metadata.itertuples(index=False):
        window_rows = source[
            (source["engine"] == row.engine)
            & source["cycle"].between(row.start_cycle, row.end_cycle)
        ]
        assert len(window_rows) == 30
        assert window_rows["engine"].nunique() == 1


def test_life_fraction_is_based_on_engine_max_cycle() -> None:
    metadata = create_window_metadata(
        _source_frame(),
        split="train",
        manifest_id="fd002-primary-v1",
        source_dataset_sha256="b" * 64,
        window_size=30,
    )

    assert metadata.loc[0, "life_fraction_end"] == pytest.approx(30 / 31)
    assert metadata.loc[1, "life_fraction_end"] == pytest.approx(1.0)
    assert metadata.loc[2, "life_fraction_end"] == pytest.approx(1.0)


def test_nonconsecutive_cycles_are_rejected() -> None:
    source = pd.DataFrame(
        {"engine": [1, 1, 1], "cycle": [1, 2, 4]}
    )

    with pytest.raises(ValueError, match="non-consecutive cycles"):
        create_window_metadata(
            source,
            split="test",
            manifest_id="fd002-primary-v1",
            source_dataset_sha256="c" * 64,
            window_size=2,
        )
