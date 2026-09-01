"""Batch-only, transform-only inference for the frozen FD002 primary policy."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd

from turbofan_anomaly.alerting.persistence import apply_alert_policy
from turbofan_anomaly.data.io import FD002_COLUMNS, validate_fd002_frame
from turbofan_anomaly.data.preprocessing import SENSOR_COLUMNS
from turbofan_anomaly.data.windows import build_window_array, summary_features
from turbofan_anomaly.evaluation.alerts import extract_alert_events
from turbofan_anomaly.explainability.pca_attribution import EXPLANATION_METADATA, attribute_pca_reconstruction
from turbofan_anomaly.inference.loader import FrozenArtifactLoader, FrozenArtifacts


@dataclass(frozen=True)
class InferenceResult:
    timeline: pd.DataFrame
    events: pd.DataFrame
    provenance: dict[str, str]

    def json_payload(self) -> dict[str, object]:
        return {
            "provenance": self.provenance,
            "timeline": _records(self.timeline),
            "events": _records(self.events),
        }


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return json.loads(frame.to_json(orient="records", date_format="iso", double_precision=15))


def validate_cycle_input(frame: pd.DataFrame) -> None:
    """Reject ambiguous or unordered raw cycle inputs before preprocessing."""
    if frame.columns.tolist() != FD002_COLUMNS:
        missing = [column for column in FD002_COLUMNS if column not in frame.columns]
        extra = [column for column in frame.columns if column not in FD002_COLUMNS]
        raise ValueError(f"Input columns must be exactly FD002_COLUMNS; missing={missing}, extra={extra}")
    if frame.empty:
        raise ValueError("Inference input may not be empty")
    for column in FD002_COLUMNS:
        if not pd.api.types.is_numeric_dtype(frame[column]) or pd.api.types.is_bool_dtype(frame[column]):
            raise ValueError(f"Input column {column} must be a non-boolean numeric type")
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Inference input contains non-finite values")
    for identity in ("engine", "cycle"):
        numeric = frame[identity].to_numpy(dtype=float)
        if not np.equal(numeric, np.floor(numeric)).all():
            raise ValueError(f"{identity} values must be integers")
    expected = frame.sort_values(["engine", "cycle"], kind="mergesort").index.to_numpy()
    if not np.array_equal(expected, frame.index.to_numpy()):
        raise ValueError("Input must already be sorted by engine and increasing cycle")
    validate_fd002_frame(frame)
    counts = frame.groupby("engine", sort=True).size()
    if (counts < 30).any():
        raise ValueError("Each engine requires at least 30 consecutive cycles")


class FrozenFD002InferencePipeline:
    """Reusable batch service. Streaming is intentionally pending, never approximated."""

    supports_streaming = False

    def __init__(self, artifacts: FrozenArtifacts) -> None:
        self.artifacts = artifacts

    @classmethod
    def from_repository(cls, repository_root: Path) -> "FrozenFD002InferencePipeline":
        return cls(FrozenArtifactLoader(repository_root).load())

    def infer(self, cycles: pd.DataFrame) -> InferenceResult:
        validate_cycle_input(cycles)
        transformed = self.artifacts.preprocessor.transform(cycles.copy(deep=True)).reset_index(drop=True)
        metadata_rows: list[dict[str, int | str]] = []
        for engine, frame in transformed.groupby("engine", sort=True):
            ordered = frame.reset_index(drop=True)
            engine_id = int(engine)
            for start in range(len(ordered) - 29):
                metadata_rows.append({
                    "window_id": f"frozen-inference-v1:e{engine_id:03d}:c{int(ordered.loc[start, 'cycle']):04d}-{int(ordered.loc[start + 29, 'cycle']):04d}",
                    "engine": engine_id,
                    "start_cycle": int(ordered.loc[start, "cycle"]),
                    "end_cycle": int(ordered.loc[start + 29, "cycle"]),
                    "window_size": 30,
                    "op_mode": int(ordered.loc[start + 29, "op_mode"]),
                })
        metadata = pd.DataFrame(metadata_rows)
        sequences = build_window_array(transformed, metadata, sensor_columns=SENSOR_COLUMNS)
        features = summary_features(sequences)
        raw_scores, calibrated = self.artifacts.pca_model.score(features)
        attribution = attribute_pca_reconstruction(
            self.artifacts.pca_model,
            features,
            completeness_abs_tolerance=float(self.artifacts.protocol["pca_score_and_attribution"]["completeness_abs_tolerance"]),
        )
        if not np.array_equal(raw_scores, attribution.raw_scores):
            if not np.allclose(raw_scores, attribution.raw_scores, rtol=0.0, atol=1e-12):
                raise RuntimeError("Attribution altered or failed to reproduce PCA scores")
        score_frame = metadata[["window_id", "engine", "start_cycle", "end_cycle", "op_mode"]].copy()
        score_frame["raw_score"] = raw_scores
        score_frame["calibrated_score"] = calibrated
        score_frame["alert_score"] = calibrated
        trace = apply_alert_policy(score_frame, self.artifacts.thresholds, ewma_alpha=0.2, persistence=8)
        events = extract_alert_events(trace)
        event_start = {(int(row.engine), int(row.event_start_cycle)): str(row.event_id) for row in events.itertuples(index=False)}
        trace["alert"] = trace["alert_active"].astype(bool)
        trace["event_start"] = [((int(row.engine), int(row.end_cycle)) in event_start) for row in trace.itertuples(index=False)]
        trace["event_status"] = [event_start.get((int(row.engine), int(row.end_cycle)), "active" if bool(row.alert_active) else "none") for row in trace.itertuples(index=False)]
        trace["top_three_sensor_contributions"] = [attribution.top_sensors(index) for index in range(len(trace))]
        for key, value in EXPLANATION_METADATA.items():
            trace[key] = value
        trace["attribution_completeness_abs_difference"] = np.abs(raw_scores - attribution.contributions.sum(axis=1))
        ordered_columns = [
            "window_id", "engine", "start_cycle", "end_cycle", "op_mode", "raw_score", "calibrated_score", "threshold", "smoothed_score", "threshold_violation", "persistence_count", "alert", "event_start", "event_status", "top_three_sensor_contributions", "explanation_type", "scope", "feature_space", "causality", "shap", "attribution_completeness_abs_difference",
        ]
        return InferenceResult(trace[ordered_columns].reset_index(drop=True), events, dict(self.artifacts.provenance))
