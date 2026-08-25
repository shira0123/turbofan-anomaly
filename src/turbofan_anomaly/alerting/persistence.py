"""Engine-local EWMA and persistence state for alert endpoints."""

from __future__ import annotations

import numpy as np
import pandas as pd

from turbofan_anomaly.alerting.thresholds import FittedThresholds, validate_calibrated_scores


def apply_alert_policy(
    score_frame: pd.DataFrame,
    thresholds: FittedThresholds,
    *,
    ewma_alpha: float | None,
    persistence: int,
) -> pd.DataFrame:
    """Apply chronological smoothing, strict thresholding, and persistence."""
    required = {"window_id", "engine", "end_cycle", "op_mode", "alert_score"}
    missing = required - set(score_frame.columns)
    if missing:
        raise ValueError(f"Missing alert-score columns: {sorted(missing)}")
    if score_frame["window_id"].isna().any() or score_frame["window_id"].duplicated().any():
        raise ValueError("Alert score window IDs must be non-null and unique")
    if score_frame[["engine", "end_cycle"]].duplicated().any():
        raise ValueError("Engine/end-cycle alert-score identities must be unique")
    if ewma_alpha is not None and not 0.0 < float(ewma_alpha) <= 1.0:
        raise ValueError("EWMA alpha must be in (0, 1]")
    if int(persistence) not in {1, 3, 5, 8}:
        raise ValueError("Persistence must be one of 1, 3, 5, or 8")

    output = score_frame.copy(deep=True)
    output["_stable_order"] = np.arange(len(output), dtype=int)
    output = output.sort_values(
        ["engine", "end_cycle", "_stable_order"], kind="mergesort"
    ).reset_index(drop=True)
    scores = validate_calibrated_scores(output["alert_score"].to_numpy(dtype=float))

    smoothed = np.empty(len(output), dtype=float)
    threshold_values = np.empty(len(output), dtype=float)
    violations = np.zeros(len(output), dtype=bool)
    counters = np.zeros(len(output), dtype=int)
    active = np.zeros(len(output), dtype=bool)
    segment_ids = np.zeros(len(output), dtype=int)
    previous_engine: int | None = None
    previous_cycle: int | None = None
    previous_smoothed = 0.0
    counter = 0
    segment = -1
    for index, row in output.iterrows():
        engine = int(row["engine"])
        cycle = int(row["end_cycle"])
        reset = previous_engine != engine or previous_cycle is None or cycle != previous_cycle + 1
        if reset:
            segment += 1
            counter = 0
            current_smoothed = scores[index]
        elif ewma_alpha is None:
            current_smoothed = scores[index]
        else:
            current_smoothed = float(ewma_alpha) * scores[index] + (
                1.0 - float(ewma_alpha)
            ) * previous_smoothed
        threshold = thresholds.threshold_for_mode(row["op_mode"])
        violation = bool(current_smoothed > threshold)
        counter = counter + 1 if violation else 0
        smoothed[index] = current_smoothed
        threshold_values[index] = threshold
        violations[index] = violation
        counters[index] = counter
        active[index] = violation and counter >= int(persistence)
        segment_ids[index] = segment
        previous_engine = engine
        previous_cycle = cycle
        previous_smoothed = current_smoothed

    output["smoothed_score"] = smoothed
    output["threshold"] = threshold_values
    output["threshold_violation"] = violations
    output["persistence_count"] = counters
    output["alert_active"] = active
    output["state_segment_id"] = segment_ids
    return output.drop(columns="_stable_order")
