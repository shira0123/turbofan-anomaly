"""Baseline anomaly models and evaluation helpers for Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import LocalOutlierFactor


@dataclass
class BaselineResult:
    model_name: str
    roc_auc: float
    precision_at_k: float
    false_alarm_rate: float
    mean_detection_delay: float
    detection_coverage: float


def sequence_summary_features(sequences: np.ndarray) -> np.ndarray:
    """Build compact per-window features from [N, T, S] sequences."""
    if sequences.ndim != 3:
        raise ValueError("Expected sequences with shape [N, T, S]")

    mean_feat = sequences.mean(axis=1)
    std_feat = sequences.std(axis=1)
    slope_feat = sequences[:, -1, :] - sequences[:, 0, :]
    return np.concatenate([mean_feat, std_feat, slope_feat], axis=1)


def precision_at_k(y_true: np.ndarray, scores: np.ndarray, k: int) -> float:
    if k <= 0:
        return 0.0
    k = min(k, len(scores))
    top_idx = np.argsort(scores)[-k:]
    return float(y_true[top_idx].mean())


def threshold_for_top_k(scores: np.ndarray, k: int) -> float:
    if k <= 0:
        return float("inf")
    k = min(k, len(scores))
    return float(np.partition(scores, -k)[-k])


def false_alarm_rate(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    healthy = y_true == 0
    if healthy.sum() == 0:
        return 0.0
    false_alarms = np.logical_and(y_pred == 1, healthy)
    return float(false_alarms.sum() / healthy.sum())


def detection_delay(
    y_pred: np.ndarray,
    engine_ids: np.ndarray,
    local_window_index: np.ndarray,
    onset_index_by_engine: Dict[int, int],
) -> Tuple[float, float]:
    """
    Compute mean delay after anomaly onset and coverage across engines.

    Delay is measured in windows after the first anomalous window for each engine.
    """
    delays = []
    detected = 0

    unique_engines = np.unique(engine_ids)
    for engine in unique_engines:
        onset = onset_index_by_engine.get(int(engine))
        if onset is None:
            continue

        mask = engine_ids == engine
        pred_e = y_pred[mask]
        idx_e = local_window_index[mask]

        post_onset_hits = idx_e[np.logical_and(pred_e == 1, idx_e >= onset)]
        if len(post_onset_hits) == 0:
            continue

        detected += 1
        delays.append(float(post_onset_hits.min() - onset))

    if len(unique_engines) == 0:
        return 0.0, 0.0

    mean_delay = float(np.mean(delays)) if delays else float("nan")
    coverage = float(detected / len(unique_engines))
    return mean_delay, coverage


def evaluate_baseline(
    model_name: str,
    scores: np.ndarray,
    y_true: np.ndarray,
    engine_ids: np.ndarray,
    local_window_index: np.ndarray,
    onset_index_by_engine: Dict[int, int],
) -> BaselineResult:
    anomaly_count = int(y_true.sum())
    k = max(1, anomaly_count)

    auc = float(roc_auc_score(y_true, scores)) if len(np.unique(y_true)) > 1 else float("nan")
    p_at_k = precision_at_k(y_true, scores, k)
    threshold = threshold_for_top_k(scores, k)
    y_pred = (scores >= threshold).astype(int)
    far = false_alarm_rate(y_true, y_pred)
    mean_delay, coverage = detection_delay(
        y_pred,
        engine_ids=engine_ids,
        local_window_index=local_window_index,
        onset_index_by_engine=onset_index_by_engine,
    )

    return BaselineResult(
        model_name=model_name,
        roc_auc=auc,
        precision_at_k=p_at_k,
        false_alarm_rate=far,
        mean_detection_delay=mean_delay,
        detection_coverage=coverage,
    )


def run_isolation_forest(
    x_train_healthy: np.ndarray,
    x_eval: np.ndarray,
    contamination: float,
    random_state: int = 42,
) -> np.ndarray:
    model = IsolationForest(
        n_estimators=300,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(x_train_healthy)
    # Larger score means more anomalous.
    return -model.score_samples(x_eval)


def run_lof_novelty(
    x_train_healthy: np.ndarray,
    x_eval: np.ndarray,
    contamination: float,
) -> np.ndarray:
    model = LocalOutlierFactor(
        n_neighbors=35,
        contamination=contamination,
        novelty=True,
    )
    model.fit(x_train_healthy)
    # Larger score means more anomalous.
    return -model.score_samples(x_eval)