"""Training-reference calibration shared by classical and LSTM scores."""

from __future__ import annotations

import numpy as np


class EmpiricalCDFCalibrator:
    """Map anomaly scores to training-reference percentiles without labels."""

    def __init__(self) -> None:
        self.sorted_training_scores_: np.ndarray | None = None

    def fit(self, scores: np.ndarray) -> "EmpiricalCDFCalibrator":
        values = np.asarray(scores, dtype=float).reshape(-1)
        if len(values) == 0 or not np.isfinite(values).all():
            raise ValueError("Calibration scores must be finite and non-empty")
        self.sorted_training_scores_ = np.sort(values)
        return self

    def transform(self, scores: np.ndarray) -> np.ndarray:
        if self.sorted_training_scores_ is None:
            raise RuntimeError("Call fit() before transform()")
        values = np.asarray(scores, dtype=float).reshape(-1)
        if not np.isfinite(values).all():
            raise ValueError("Scores to calibrate must be finite")
        ranks = np.searchsorted(self.sorted_training_scores_, values, side="right")
        return ranks.astype(float) / len(self.sorted_training_scores_)
