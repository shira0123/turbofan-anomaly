"""Window-, event-, engine-, and selection-level alert-policy evaluation."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd


def _ratio(numerator: float, denominator: int, *, scale: float = 1.0) -> float:
    return float(numerator * scale / denominator) if denominator else float("nan")


def _quartiles(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return float("nan"), float("nan"), float("nan")
    array = np.asarray(values, dtype=float)
    return (
        float(np.median(array)),
        float(np.quantile(array, 0.25)),
        float(np.quantile(array, 0.75)),
    )


def align_policy_frame(trace: pd.DataFrame, policy_frame: pd.DataFrame) -> pd.DataFrame:
    """Align one policy exactly by unique ``window_id`` without mutating inputs."""
    for frame, name in ((trace, "trace"), (policy_frame, "policy")):
        if "window_id" not in frame or frame["window_id"].isna().any():
            raise ValueError(f"{name} window IDs must be present and non-null")
        if frame["window_id"].duplicated().any():
            raise ValueError(f"{name} window IDs must be unique")
    if set(trace["window_id"]) != set(policy_frame["window_id"]):
        raise ValueError("Alert trace and proxy policy window IDs differ")
    policy_columns = [
        "window_id",
        "engine",
        "policy_id",
        "selection_policy",
        "onset_cycle",
        "label_state",
        "proxy_label",
    ]
    missing = set(policy_columns) - set(policy_frame.columns)
    if missing:
        raise ValueError(f"Missing proxy-policy columns: {sorted(missing)}")
    renamed = policy_frame[policy_columns].rename(columns={"engine": "policy_engine"})
    merged = trace.merge(renamed, on="window_id", how="left", validate="one_to_one")
    if not np.array_equal(
        merged["engine"].astype(int).to_numpy(),
        merged["policy_engine"].astype(int).to_numpy(),
    ):
        raise ValueError("Alert trace and proxy-policy engines differ")
    return merged.drop(columns="policy_engine")


def extract_alert_events(trace: pd.DataFrame) -> pd.DataFrame:
    """Extract contiguous active endpoint events with engine/gap boundaries."""
    required = {"engine", "end_cycle", "alert_active"}
    missing = required - set(trace.columns)
    if missing:
        raise ValueError(f"Missing event columns: {sorted(missing)}")
    ordered = trace.sort_values(["engine", "end_cycle"], kind="mergesort")
    active = ordered[ordered["alert_active"].astype(bool)]
    rows: list[dict[str, Any]] = []
    per_engine_count: dict[int, int] = {}
    current: dict[str, Any] | None = None
    for row in active.itertuples(index=False):
        engine = int(row.engine)
        cycle = int(row.end_cycle)
        if current is None or current["engine"] != engine or cycle != current["event_end_cycle"] + 1:
            if current is not None:
                rows.append(current)
            event_number = per_engine_count.get(engine, 0) + 1
            per_engine_count[engine] = event_number
            current = {
                "event_id": f"engine_{engine}_event_{event_number:03d}",
                "engine": engine,
                "event_start_cycle": cycle,
                "event_end_cycle": cycle,
                "event_duration_endpoints": 1,
            }
        else:
            current["event_end_cycle"] = cycle
            current["event_duration_endpoints"] += 1
    if current is not None:
        rows.append(current)
    return pd.DataFrame(
        rows,
        columns=[
            "event_id",
            "engine",
            "event_start_cycle",
            "event_end_cycle",
            "event_duration_endpoints",
        ],
    )


def evaluate_alert_policy(
    trace: pd.DataFrame, policy_frame: pd.DataFrame
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Evaluate one alert trace under one declared onset proxy policy."""
    aligned = align_policy_frame(trace, policy_frame)
    included = aligned["proxy_label"].notna()
    labels = aligned.loc[included, "proxy_label"].astype(int).to_numpy()
    predictions = aligned.loc[included, "alert_active"].astype(bool).to_numpy()
    tp = int(np.sum(predictions & (labels == 1)))
    fp = int(np.sum(predictions & (labels == 0)))
    tn = int(np.sum(~predictions & (labels == 0)))
    fn = int(np.sum(~predictions & (labels == 1)))
    healthy_count = fp + tn
    anomalous_count = tp + fn

    events = extract_alert_events(aligned)
    engine_rows: list[dict[str, Any]] = []
    evaluated_events: list[dict[str, Any]] = []
    for engine, engine_trace in aligned.groupby("engine", sort=True):
        engine_id = int(engine)
        onset_values = engine_trace["onset_cycle"].astype(int).unique()
        if len(onset_values) != 1:
            raise ValueError("Each engine/policy must have exactly one onset cycle")
        onset = int(onset_values[0])
        max_cycle_values = engine_trace["max_cycle"].astype(int).unique()
        if len(max_cycle_values) != 1:
            raise ValueError("Each engine must have exactly one maximum cycle")
        max_cycle = int(max_cycle_values[0])
        engine_events = events[events["engine"] == engine_id]
        false_events = engine_events[engine_events["event_start_cycle"] < onset]
        valid_events = engine_events[engine_events["event_start_cycle"] >= onset]
        crossing_events = engine_events[
            (engine_events["event_start_cycle"] < onset)
            & (engine_events["event_end_cycle"] >= onset)
        ]
        for event in engine_events.to_dict(orient="records"):
            event_start = int(event["event_start_cycle"])
            event_end = int(event["event_end_cycle"])
            evaluated_events.append(
                {
                    **event,
                    "policy_id": str(engine_trace["policy_id"].iloc[0]),
                    "onset_cycle": onset,
                    "false_pre_onset_event": event_start < onset,
                    "valid_post_onset_detection_event": event_start >= onset,
                    "crosses_onset": event_start < onset <= event_end,
                }
            )
        detected = not valid_events.empty
        first_detection = (
            int(valid_events["event_start_cycle"].min()) if detected else None
        )
        engine_rows.append(
            {
                "policy_id": str(engine_trace["policy_id"].iloc[0]),
                "engine": engine_id,
                "onset_cycle": onset,
                "max_cycle": max_cycle,
                "first_detection_end_cycle": first_detection,
                "detected": detected,
                "missed": not detected,
                "false_event_count": int(len(false_events)),
                "healthy_false_alert": bool(len(false_events)),
                "crossing_event_count": int(len(crossing_events)),
                "total_event_count": int(len(engine_events)),
                "first_alert_delay": (
                    first_detection - onset if first_detection is not None else np.nan
                ),
                "lead_cycles": (
                    max_cycle - first_detection if first_detection is not None else np.nan
                ),
            }
        )

    per_engine = pd.DataFrame(engine_rows)
    evaluated_event_frame = pd.DataFrame(evaluated_events)
    engine_count = int(len(per_engine))
    detected_count = int(per_engine["detected"].sum())
    false_engine_count = int(per_engine["healthy_false_alert"].sum())
    false_event_count = int(per_engine["false_event_count"].sum())
    delays = per_engine.loc[per_engine["detected"], "first_alert_delay"].astype(float).tolist()
    leads = per_engine.loc[per_engine["detected"], "lead_cycles"].astype(float).tolist()
    delay_median, delay_q1, delay_q3 = _quartiles(delays)
    lead_median, lead_q1, lead_q3 = _quartiles(leads)
    event_durations = (
        events["event_duration_endpoints"].astype(float).tolist() if len(events) else []
    )
    metric = {
        "policy_id": str(aligned["policy_id"].iloc[0]),
        "selection_policy": bool(aligned["selection_policy"].iloc[0]),
        "evaluated_endpoints": int(len(labels)),
        "healthy_evaluated_endpoints": healthy_count,
        "anomalous_evaluated_endpoints": anomalous_count,
        "ambiguous_excluded_endpoints": int((~included).sum()),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": _ratio(tp, tp + fp),
        "recall": _ratio(tp, tp + fn),
        "f1": _ratio(2 * tp, 2 * tp + fp + fn),
        "specificity": _ratio(tn, tn + fp),
        "false_positive_alerted_endpoints_per_1000_healthy_endpoints": _ratio(
            fp, healthy_count, scale=1000.0
        ),
        "false_alert_event_count": false_event_count,
        "false_alert_events_per_1000_healthy_endpoints": _ratio(
            false_event_count, healthy_count, scale=1000.0
        ),
        "validation_engine_count": engine_count,
        "engines_with_healthy_false_alert": false_engine_count,
        "percent_engines_with_healthy_false_alert": _ratio(
            false_engine_count, engine_count, scale=100.0
        ),
        "total_event_count": int(len(events)),
        "median_event_duration_endpoints": (
            float(np.median(event_durations)) if event_durations else float("nan")
        ),
        "event_fragmentation_per_engine": _ratio(len(events), engine_count),
        "events_crossing_proxy_onset": int(per_engine["crossing_event_count"].sum()),
        "detected_engine_count": detected_count,
        "missed_engine_count": engine_count - detected_count,
        "engine_detection_coverage": _ratio(detected_count, engine_count, scale=100.0),
        "missed_engine_rate": _ratio(engine_count - detected_count, engine_count, scale=100.0),
        "median_first_alert_delay": delay_median,
        "first_alert_delay_q1": delay_q1,
        "first_alert_delay_q3": delay_q3,
        "median_lead_cycles": lead_median,
        "lead_cycles_q1": lead_q1,
        "lead_cycles_q3": lead_q3,
    }
    return metric, per_engine, evaluated_event_frame


def aggregate_candidate_metrics(
    candidate_policy_metrics: pd.DataFrame,
    *,
    selection_policy_ids: Iterable[str],
    feasibility_limit: float,
) -> pd.DataFrame:
    """Aggregate the three registered endpoint policies for deterministic selection."""
    selection_ids = tuple(selection_policy_ids)
    selected = candidate_policy_metrics[
        candidate_policy_metrics["policy_id"].isin(selection_ids)
    ]
    rows: list[dict[str, Any]] = []
    identity_columns = [
        "candidate_id",
        "detector_id",
        "threshold_context",
        "threshold_rule_id",
        "ewma_id",
        "ewma_alpha",
        "persistence",
    ]
    for candidate_id, group in selected.groupby("candidate_id", sort=False):
        if set(group["policy_id"]) != set(selection_ids) or len(group) != len(selection_ids):
            raise ValueError(f"Candidate {candidate_id} lacks the three selection policies")
        base = {column: group.iloc[0][column] for column in identity_columns}
        delays = group["median_first_alert_delay"].to_numpy(dtype=float)
        leads = group["median_lead_cycles"].to_numpy(dtype=float)
        row = {
            **base,
            "minimum_engine_detection_coverage": float(group["engine_detection_coverage"].min()),
            "mean_engine_detection_coverage": float(group["engine_detection_coverage"].mean()),
            "worst_false_positive_alerted_endpoints_per_1000": float(group["false_positive_alerted_endpoints_per_1000_healthy_endpoints"].max()),
            "worst_false_alert_events_per_1000": float(group["false_alert_events_per_1000_healthy_endpoints"].max()),
            "worst_percent_engines_with_healthy_false_alert": float(group["percent_engines_with_healthy_false_alert"].max()),
            "median_policy_median_detection_delay": float(np.median(delays)) if np.isfinite(delays).all() else float("nan"),
            "median_policy_median_lead_cycles": float(np.median(leads)) if np.isfinite(leads).all() else float("nan"),
        }
        row["feasible"] = bool(
            row["worst_false_positive_alerted_endpoints_per_1000"]
            <= float(feasibility_limit)
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _selection_key(row: pd.Series) -> tuple[Any, ...]:
    delay = float(row["median_policy_median_detection_delay"])
    lead = float(row["median_policy_median_lead_cycles"])
    return (
        -float(row["minimum_engine_detection_coverage"]),
        -float(row["mean_engine_detection_coverage"]),
        float(row["worst_false_alert_events_per_1000"]),
        float(row["worst_percent_engines_with_healthy_false_alert"]),
        delay if np.isfinite(delay) else float("inf"),
        -lead if np.isfinite(lead) else float("inf"),
        str(row["candidate_id"]),
    )


def select_best_candidates(
    aggregated: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select one feasible candidate per detector and one overall, or none."""
    feasible = aggregated[aggregated["feasible"].astype(bool)]
    if feasible.empty:
        empty = aggregated.iloc[:0].copy()
        return empty, empty
    per_detector_rows = []
    for _, group in feasible.groupby("detector_id", sort=False):
        best_index = min(group.index, key=lambda index: _selection_key(group.loc[index]))
        per_detector_rows.append(feasible.loc[best_index].to_dict())
    best_overall_index = min(
        feasible.index, key=lambda index: _selection_key(feasible.loc[index])
    )
    return pd.DataFrame(per_detector_rows), pd.DataFrame(
        [feasible.loc[best_overall_index].to_dict()]
    )
