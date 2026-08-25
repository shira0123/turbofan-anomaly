"""Classical anomaly detectors with training-fitted feature and score state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from turbofan_anomaly.alerting.calibration import EmpiricalCDFCalibrator


class ClassicalAnomalyModel:
    """A fitted feature scaler, detector, and empirical score calibrator."""

    def __init__(
        self,
        detector_name: str,
        parameters: dict[str, Any],
        *,
        random_state: int = 42,
    ) -> None:
        if detector_name not in {"pca", "one_class_svm", "isolation_forest", "lof"}:
            raise ValueError(f"Unsupported detector: {detector_name}")
        self.detector_name = detector_name
        self.parameters = dict(parameters)
        self.random_state = int(random_state)
        self.feature_scaler_: StandardScaler | None = None
        self.detector_: Any = None
        self.score_calibrator_: EmpiricalCDFCalibrator | None = None
        self.fit_window_count_: int = 0
        self.feature_count_: int = 0

    def _build_detector(self, fit_window_count: int) -> Any:
        if self.detector_name == "pca":
            return PCA(
                n_components=float(self.parameters["n_components"]),
                svd_solver="full",
            )
        if self.detector_name == "one_class_svm":
            return OneClassSVM(
                kernel="rbf",
                nu=float(self.parameters["nu"]),
                gamma=self.parameters.get("gamma", "scale"),
            )
        if self.detector_name == "isolation_forest":
            max_samples = min(int(self.parameters["max_samples"]), fit_window_count)
            return IsolationForest(
                n_estimators=int(self.parameters.get("n_estimators", 300)),
                max_samples=max_samples,
                contamination="auto",
                random_state=self.random_state,
                n_jobs=-1,
            )
        n_neighbors = min(int(self.parameters["n_neighbors"]), fit_window_count - 1)
        if n_neighbors < 2:
            raise ValueError("LOF requires at least three fit windows")
        return LocalOutlierFactor(
            n_neighbors=n_neighbors,
            novelty=True,
            contamination="auto",
            n_jobs=-1,
        )

    def fit(self, healthy_training_features: np.ndarray) -> "ClassicalAnomalyModel":
        features = np.asarray(healthy_training_features, dtype=float)
        if features.ndim != 2 or len(features) < 3:
            raise ValueError("Expected at least three [windows, features] fit rows")
        if not np.isfinite(features).all():
            raise ValueError("Training features must be finite")

        self.feature_scaler_ = StandardScaler().fit(features)
        scaled = self.feature_scaler_.transform(features)
        self.detector_ = self._build_detector(len(features))
        self.detector_.fit(scaled)
        training_scores = self._raw_scores_scaled(scaled)
        self.score_calibrator_ = EmpiricalCDFCalibrator().fit(training_scores)
        self.fit_window_count_ = int(len(features))
        self.feature_count_ = int(features.shape[1])
        return self

    def _require_fitted(self) -> None:
        if (
            self.feature_scaler_ is None
            or self.detector_ is None
            or self.score_calibrator_ is None
        ):
            raise RuntimeError("Call fit() before scoring")

    def _raw_scores_scaled(self, scaled_features: np.ndarray) -> np.ndarray:
        if self.detector_name == "pca":
            reconstruction = self.detector_.inverse_transform(
                self.detector_.transform(scaled_features)
            )
            return np.mean((scaled_features - reconstruction) ** 2, axis=1)
        if self.detector_name == "one_class_svm":
            return -self.detector_.decision_function(scaled_features).reshape(-1)
        return -self.detector_.score_samples(scaled_features).reshape(-1)

    def score(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        self._require_fitted()
        values = np.asarray(features, dtype=float)
        if values.ndim != 2 or values.shape[1] != self.feature_count_:
            raise ValueError(
                f"Expected [windows, {self.feature_count_}] feature matrix"
            )
        if not np.isfinite(values).all():
            raise ValueError("Scoring features must be finite")
        assert self.feature_scaler_ is not None
        assert self.score_calibrator_ is not None
        scaled = self.feature_scaler_.transform(values)
        raw_scores = self._raw_scores_scaled(scaled)
        calibrated_scores = self.score_calibrator_.transform(raw_scores)
        return raw_scores, calibrated_scores


def candidate_grid() -> dict[str, list[dict[str, Any]]]:
    """Small registered grids chosen before validation scoring."""
    return {
        "pca": [
            {"n_components": 0.90},
            {"n_components": 0.95},
            {"n_components": 0.99},
        ],
        "one_class_svm": [
            {"nu": 0.01, "gamma": "scale"},
            {"nu": 0.05, "gamma": "scale"},
            {"nu": 0.10, "gamma": "scale"},
        ],
        "isolation_forest": [
            {"max_samples": 256, "n_estimators": 300},
            {"max_samples": 1024, "n_estimators": 300},
            {"max_samples": 5000, "n_estimators": 300},
        ],
        "lof": [
            {"n_neighbors": 20},
            {"n_neighbors": 35},
            {"n_neighbors": 50},
        ],
    }


def save_baseline_artifact(
    model: ClassicalAnomalyModel, metadata: dict[str, Any], path: Path
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "metadata": metadata}, path)


def load_baseline_artifact(
    path: Path,
    *,
    expected_split_manifest_id: str | None = None,
    expected_preprocessing_decision_id: str | None = None,
) -> tuple[ClassicalAnomalyModel, dict[str, Any]]:
    # Registered hashes document historical joblib outputs, but the artifacts
    # are absent here; deliberately avoid a legacy ``src.*`` pickle shim.
    payload = joblib.load(path)
    if "model" not in payload or "metadata" not in payload:
        raise ValueError(f"Invalid baseline artifact: {path}")
    metadata = payload["metadata"]
    if (
        expected_split_manifest_id is not None
        and metadata.get("split_manifest_id") != expected_split_manifest_id
    ):
        raise ValueError("Baseline artifact split manifest mismatch")
    if (
        expected_preprocessing_decision_id is not None
        and metadata.get("preprocessing_decision_id")
        != expected_preprocessing_decision_id
    ):
        raise ValueError("Baseline artifact preprocessing decision mismatch")
    return payload["model"], metadata
