from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.models.classical_baselines import (
    ClassicalAnomalyModel,
    EmpiricalCDFCalibrator,
    candidate_grid,
    load_baseline_artifact,
    save_baseline_artifact,
)


def test_empirical_cdf_is_training_fitted_and_monotonic() -> None:
    calibrator = EmpiricalCDFCalibrator().fit(np.array([3.0, 1.0, 2.0]))
    calibrated = calibrator.transform(np.array([0.0, 1.0, 1.5, 3.0, 4.0]))

    assert np.all(np.diff(calibrated) >= 0)
    assert calibrated.tolist() == [0.0, 1 / 3, 1 / 3, 1.0, 1.0]


@pytest.mark.parametrize(
    ("detector", "parameters"),
    [
        ("pca", {"n_components": 0.95}),
        ("one_class_svm", {"nu": 0.05, "gamma": "scale"}),
        ("isolation_forest", {"max_samples": 64, "n_estimators": 25}),
        ("lof", {"n_neighbors": 10}),
    ],
)
def test_classical_model_scores_unseen_rows(
    detector: str, parameters: dict
) -> None:
    rng = np.random.default_rng(42)
    healthy = rng.normal(0.0, 1.0, size=(100, 9))
    evaluation = np.vstack([healthy[:10], rng.normal(5.0, 1.0, size=(10, 9))])
    model = ClassicalAnomalyModel(
        detector, parameters, random_state=42
    ).fit(healthy)

    raw, calibrated = model.score(evaluation)
    assert raw.shape == calibrated.shape == (20,)
    assert np.isfinite(raw).all()
    assert ((calibrated >= 0.0) & (calibrated <= 1.0)).all()


def test_baseline_artifact_enforces_provenance(tmp_path: Path) -> None:
    rng = np.random.default_rng(7)
    healthy = rng.normal(size=(50, 6))
    model = ClassicalAnomalyModel(
        "pca", {"n_components": 0.95}, random_state=42
    ).fit(healthy)
    metadata = {
        "split_manifest_id": "split-v1",
        "preprocessing_decision_id": "preprocessing-v1",
    }
    path = tmp_path / "pca.joblib"
    save_baseline_artifact(model, metadata, path)

    _, loaded_metadata = load_baseline_artifact(
        path,
        expected_split_manifest_id="split-v1",
        expected_preprocessing_decision_id="preprocessing-v1",
    )
    assert loaded_metadata == metadata
    with pytest.raises(ValueError, match="split manifest mismatch"):
        load_baseline_artifact(path, expected_split_manifest_id="other")


def test_candidate_grid_is_small_and_registered() -> None:
    grid = candidate_grid()
    assert set(grid) == {"pca", "one_class_svm", "isolation_forest", "lof"}
    assert all(len(candidates) == 3 for candidates in grid.values())
