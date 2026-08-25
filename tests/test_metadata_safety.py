from __future__ import annotations

import sys

from turbofan_anomaly.workflows.create_window_metadata import (
    SAFE_METADATA_SPLITS,
    parse_args,
    selected_metadata_splits,
)


def test_metadata_default_is_training_and_validation_only(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["create_window_metadata"])
    args = parse_args()

    assert args.include_internal_test is False
    assert SAFE_METADATA_SPLITS == ("train", "validation")
    assert selected_metadata_splits(include_internal_test=False) == (
        "train",
        "validation",
    )
