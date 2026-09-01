"""Exact local PCA reconstruction-error decomposition in normalized feature space."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from turbofan_anomaly.data.preprocessing import SENSOR_COLUMNS
from turbofan_anomaly.models.classical import ClassicalAnomalyModel


EXPLANATION_METADATA = {
    "explanation_type": "pca_reconstruction_error_contribution",
    "scope": "local_model_fidelity_explanation",
    "feature_space": "normalized_feature_space",
    "causality": "non_causal",
    "shap": "not_shap",
}


@dataclass(frozen=True)
class PCAAttribution:
    """Additive per-sensor contributions for a batch of PCA score windows."""

    raw_scores: np.ndarray
    contributions: np.ndarray
    shares: np.ndarray
    ranks: np.ndarray
    top_sensor_indices: np.ndarray
    maximum_completeness_difference: float

    def top_sensors(self, row: int, *, sensor_columns: tuple[str, ...] = SENSOR_COLUMNS) -> list[dict[str, float | int | str]]:
        """Return deterministic top-three records for one window."""
        return [
            {
                "sensor": sensor_columns[int(index)],
                "contribution": float(self.contributions[row, index]),
                "share": float(self.shares[row, index]),
                "rank": int(self.ranks[row, index]),
            }
            for index in self.top_sensor_indices[row]
        ]


def _validate_pca_model(model: ClassicalAnomalyModel) -> None:
    model._require_fitted()
    if model.detector_name != "pca":
        raise ValueError("PCA reconstruction attribution requires a PCA detector")
    if model.feature_count_ != 3 * len(SENSOR_COLUMNS):
        raise ValueError("Frozen PCA feature dimension must equal 63 summary features")
    if not hasattr(model.detector_, "transform") or not hasattr(model.detector_, "inverse_transform"):
        raise ValueError("PCA detector lacks reconstruction methods")


def attribute_pca_reconstruction(
    model: ClassicalAnomalyModel,
    features: np.ndarray,
    *,
    completeness_abs_tolerance: float = 1e-12,
) -> PCAAttribution:
    """Decompose frozen PCA raw MSE into 21 exact sensor contributions.

    The frozen PCA is fitted on 63 standardized summary features (mean, standard
    deviation, and endpoint-minus-start slope for each registered sensor).  It
    does not reconstruct a 30x21 grid; each sensor contribution is the sum of
    its three squared residual terms divided by the raw-score denominator 63.
    """
    _validate_pca_model(model)
    values = np.asarray(features, dtype=float)
    if values.ndim != 2 or values.shape[1] != model.feature_count_:
        raise ValueError(f"Expected [windows, {model.feature_count_}] features")
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("Attribution features must be non-empty and finite")
    if completeness_abs_tolerance < 0.0:
        raise ValueError("completeness_abs_tolerance must be nonnegative")

    assert model.feature_scaler_ is not None
    assert model.detector_ is not None
    scaled = model.feature_scaler_.transform(values)
    reconstruction = np.asarray(
        model.detector_.inverse_transform(model.detector_.transform(scaled)), dtype=float
    )
    if reconstruction.shape != scaled.shape or not np.isfinite(reconstruction).all():
        raise ValueError("PCA reconstruction has invalid shape or non-finite values")
    squared = (scaled - reconstruction) ** 2
    raw_scores = np.mean(squared, axis=1)
    sensor_count = len(SENSOR_COLUMNS)
    contributions = (
        squared[:, :sensor_count]
        + squared[:, sensor_count : 2 * sensor_count]
        + squared[:, 2 * sensor_count : 3 * sensor_count]
    ) / float(model.feature_count_)
    reconstructed_score = contributions.sum(axis=1)
    differences = np.abs(raw_scores - reconstructed_score)
    maximum = float(differences.max(initial=0.0))
    if maximum > completeness_abs_tolerance:
        raise RuntimeError("PCA sensor contributions do not reproduce the raw score")
    shares = np.divide(
        contributions,
        raw_scores[:, None],
        out=np.zeros_like(contributions),
        where=raw_scores[:, None] > 0.0,
    )
    sensor_index = np.arange(sensor_count)
    ordering = np.asarray([np.lexsort((sensor_index, -row)) for row in contributions], dtype=int)
    ranks = np.empty_like(ordering)
    ranks[np.arange(len(ordering))[:, None], ordering] = np.arange(1, sensor_count + 1)
    return PCAAttribution(raw_scores, contributions, shares, ranks, ordering[:, :3], maximum)
