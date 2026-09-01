import joblib
import numpy as np
import pytest

from turbofan_anomaly.explainability.pca_attribution import attribute_pca_reconstruction
from turbofan_anomaly.models.classical import ClassicalAnomalyModel


@pytest.fixture()
def pca_model() -> ClassicalAnomalyModel:
    rng = np.random.default_rng(7)
    return ClassicalAnomalyModel("pca", {"n_components": 0.9}).fit(rng.normal(size=(96, 63)))


def test_contributions_are_complete_nonnegative_and_deterministic(pca_model):
    features = np.arange(126, dtype=float).reshape(2, 63) / 10.0
    result = attribute_pca_reconstruction(pca_model, features)
    assert np.all(result.contributions >= 0.0)
    assert np.allclose(result.contributions.sum(axis=1), result.raw_scores, atol=1e-12, rtol=0)
    assert np.allclose(result.shares.sum(axis=1), 1.0, atol=1e-12, rtol=0)
    assert result.top_sensor_indices.shape == (2, 3)
    assert result.maximum_completeness_difference <= 1e-12


def test_zero_score_uses_registered_sensor_order():
    rng = np.random.default_rng(12)
    model = ClassicalAnomalyModel("pca", {"n_components": 0.999}).fit(rng.normal(size=(96, 63)))
    features = rng.normal(size=(1, 63))
    expected_scaled = model.feature_scaler_.transform(features)
    model.detector_.inverse_transform = lambda values: expected_scaled
    result = attribute_pca_reconstruction(model, features)
    assert result.raw_scores[0] == 0.0
    assert np.array_equal(result.top_sensor_indices[0], np.array([0, 1, 2]))
    assert not result.shares.any()


def test_batch_single_and_serialized_reload_parity(pca_model, tmp_path):
    features = np.linspace(-1, 1, 189).reshape(3, 63)
    batch = attribute_pca_reconstruction(pca_model, features)
    singles = [attribute_pca_reconstruction(pca_model, row[None, :]) for row in features]
    assert np.allclose(batch.contributions, np.vstack([item.contributions for item in singles]))
    path = tmp_path / "pca.joblib"
    joblib.dump(pca_model, path)
    restored = attribute_pca_reconstruction(joblib.load(path), features)
    assert np.array_equal(batch.top_sensor_indices, restored.top_sensor_indices)
    assert np.allclose(batch.raw_scores, restored.raw_scores)


def test_invalid_values_and_malformed_reconstruction_are_rejected(pca_model):
    with pytest.raises(ValueError):
        attribute_pca_reconstruction(pca_model, np.full((1, 63), np.nan))
    pca_model.detector_.inverse_transform = lambda values: values[:, :-1]
    with pytest.raises(ValueError, match="invalid shape"):
        attribute_pca_reconstruction(pca_model, np.zeros((1, 63)))
