from pathlib import Path

import numpy as np
import pandas as pd
import torch

from src.models.lstm_validation import (
    LSTMArchitecture,
    TrainingSettings,
    fit_lstm_autoencoder,
    load_lstm_artifact,
    reconstruction_errors,
    save_lstm_artifact,
    split_eligible_training_windows,
)


def _metadata() -> pd.DataFrame:
    rows = []
    for engine in range(1, 26):
        for end_cycle in (10, 20):
            rows.append(
                {
                    "engine": engine,
                    "end_cycle": end_cycle,
                    "max_cycle": 90 + engine,
                    "split": "train",
                }
            )
    return pd.DataFrame(rows)


def test_monitor_split_is_deterministic_engine_disjoint_and_complete() -> None:
    metadata = _metadata()
    eligible = np.ones(len(metadata), dtype=bool)
    first = split_eligible_training_windows(
        metadata, eligible, monitor_fraction=0.2, random_state=142
    )
    second = split_eligible_training_windows(
        metadata, eligible, monitor_fraction=0.2, random_state=142
    )
    development, monitor, summary = first
    assert np.array_equal(development, second[0])
    assert np.array_equal(monitor, second[1])
    assert np.array_equal(development | monitor, eligible)
    assert not np.any(development & monitor)
    development_engines = set(metadata.loc[development, "engine"])
    monitor_engines = set(metadata.loc[monitor, "engine"])
    assert development_engines.isdisjoint(monitor_engines)
    assert set(summary["role"]) == {"development", "monitor"}


def test_training_scoring_and_artifact_provenance(tmp_path: Path) -> None:
    rng = np.random.default_rng(7)
    development = rng.normal(size=(12, 5, 3)).astype(np.float32)
    monitor = rng.normal(size=(4, 5, 3)).astype(np.float32)
    architecture = LSTMArchitecture("tiny", 4, 2, 1, 0.0)
    settings = TrainingSettings(
        batch_size=4,
        max_epochs=2,
        minimum_epochs=1,
        patience=1,
        min_delta=0.0,
        learning_rate=0.001,
        weight_decay=0.0,
        gradient_clip_norm=1.0,
    )
    result = fit_lstm_autoencoder(
        development,
        monitor,
        architecture=architecture,
        settings=settings,
        seed=42,
        device=torch.device("cpu"),
    )
    scores = reconstruction_errors(
        result.model, development, batch_size=4, device=torch.device("cpu")
    )
    assert scores.shape == (12,)
    assert np.isfinite(scores).all()
    artifact = tmp_path / "tiny.pt"
    metadata = {
        "split_manifest_id": "split-v1",
        "preprocessing_decision_id": "pre-v1",
        "input_dim": 3,
    }
    save_lstm_artifact(result.model, architecture, scores, metadata, artifact)
    loaded, reference, loaded_metadata = load_lstm_artifact(
        artifact,
        expected_split_manifest_id="split-v1",
        expected_preprocessing_decision_id="pre-v1",
    )
    loaded_scores = reconstruction_errors(
        loaded, development, batch_size=4, device=torch.device("cpu")
    )
    assert np.allclose(scores, loaded_scores)
    assert np.array_equal(reference, np.sort(scores))
    assert loaded_metadata == metadata


def test_lstm_rejects_wrong_sensor_dimension() -> None:
    model = LSTMArchitecture("tiny", 4, 2, 1, 0.0).build(input_dim=3)
    try:
        model(torch.zeros(2, 5, 4))
    except ValueError as error:
        assert "Expected 3 sensors" in str(error)
    else:
        raise AssertionError("Expected wrong sensor dimension to be rejected")
