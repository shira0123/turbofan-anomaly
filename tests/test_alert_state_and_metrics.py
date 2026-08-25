from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from turbofan_anomaly.alerting.persistence import apply_alert_policy
from turbofan_anomaly.alerting.thresholds import FittedThresholds
from turbofan_anomaly.evaluation.alerts import (
    aggregate_candidate_metrics,
    align_policy_frame,
    evaluate_alert_policy,
    extract_alert_events,
    select_best_candidates,
)


def _scores(
    values: list[float],
    *,
    cycles: list[int] | None = None,
    modes: list[int] | None = None,
    engines: list[int] | None = None,
) -> pd.DataFrame:
    count = len(values)
    return pd.DataFrame(
        {
            "window_id": [f"w{i}" for i in range(count)],
            "engine": engines or [1] * count,
            "start_cycle": list(range(1, count + 1)),
            "end_cycle": cycles or list(range(1, count + 1)),
            "max_cycle": [count] * count,
            "op_mode": modes or [0] * count,
            "alert_score": values,
        }
    )


def _global_threshold(value: float) -> FittedThresholds:
    return FittedThresholds("global", "fixture", {None: value}, {None: 10})


def test_ewma_initialization_engine_and_gap_resets() -> None:
    frame = _scores(
        [0.2, 0.6, 0.8, 0.4],
        cycles=[1, 2, 4, 1],
        engines=[1, 1, 1, 2],
    )
    trace = apply_alert_policy(
        frame, _global_threshold(0.5), ewma_alpha=0.5, persistence=1
    )
    assert np.allclose(trace["smoothed_score"], [0.2, 0.4, 0.8, 0.4])
    assert trace["state_segment_id"].tolist() == [0, 0, 1, 2]


def test_mode_change_does_not_reset_ewma_or_persistence() -> None:
    frame = _scores([0.8, 0.8, 0.8], modes=[0, 1, 0])
    thresholds = FittedThresholds(
        "per_mode", "fixture", {0: 0.7, 1: 0.7}, {0: 5, 1: 5}
    )
    trace = apply_alert_policy(
        frame, thresholds, ewma_alpha=0.5, persistence=3
    )
    assert np.allclose(trace["smoothed_score"], [0.8, 0.8, 0.8])
    assert trace["persistence_count"].tolist() == [1, 2, 3]
    assert trace["alert_active"].tolist() == [False, False, True]


def test_strict_threshold_equality_is_not_a_violation_and_closes_alert() -> None:
    trace = apply_alert_policy(
        _scores([0.8, 0.8, 0.7, 0.9]),
        _global_threshold(0.7),
        ewma_alpha=None,
        persistence=1,
    )
    assert trace["threshold_violation"].tolist() == [True, True, False, True]
    assert trace["alert_active"].tolist() == [True, True, False, True]
    assert trace["persistence_count"].tolist() == [1, 2, 0, 1]


@pytest.mark.parametrize("persistence", [1, 3, 5, 8])
def test_persistence_begins_at_mth_violation_without_backdating(
    persistence: int,
) -> None:
    trace = apply_alert_policy(
        _scores([0.9] * 8),
        _global_threshold(0.5),
        ewma_alpha=None,
        persistence=persistence,
    )
    active_cycles = trace.loc[trace["alert_active"], "end_cycle"].tolist()
    assert active_cycles[0] == persistence
    assert all(not value for value in trace["alert_active"].iloc[: persistence - 1])


def test_event_extraction_handles_closure_engine_boundaries_and_gaps() -> None:
    trace = _scores(
        [0.9] * 7,
        cycles=[1, 2, 3, 5, 6, 1, 2],
        engines=[1, 1, 1, 1, 1, 2, 2],
    )
    trace["alert_active"] = [False, True, True, True, False, True, True]
    events = extract_alert_events(trace)
    assert events[["engine", "event_start_cycle", "event_end_cycle"]].values.tolist() == [
        [1, 2, 3],
        [1, 5, 5],
        [2, 1, 2],
    ]
    assert events["event_duration_endpoints"].tolist() == [2, 1, 2]


def _policy(frame: pd.DataFrame, onset: int, *, ambiguous: set[int] | None = None) -> pd.DataFrame:
    ambiguous = ambiguous or set()
    labels = []
    states = []
    for cycle in frame["end_cycle"].astype(int):
        if cycle in ambiguous:
            labels.append(pd.NA)
            states.append("ambiguous")
        elif cycle < onset:
            labels.append(0)
            states.append("healthy")
        else:
            labels.append(1)
            states.append("anomalous")
    return pd.DataFrame(
        {
            "window_id": frame["window_id"],
            "engine": frame["engine"],
            "policy_id": "fixture_endpoint",
            "selection_policy": True,
            "onset_cycle": onset,
            "label_state": states,
            "proxy_label": pd.array(labels, dtype="Int64"),
        }
    )


def test_event_metrics_keep_crossing_event_false_and_use_confirmed_start() -> None:
    trace = _scores([0.1] * 10)
    trace["alert_active"] = [False, True, True, False, True, True, False, True, True, False]
    metric, engines, events = evaluate_alert_policy(trace, _policy(trace, 6))
    assert metric["fp"] == 3
    assert metric["false_positive_alerted_endpoints_per_1000_healthy_endpoints"] == 600.0
    assert metric["false_alert_event_count"] == 2
    assert metric["false_alert_events_per_1000_healthy_endpoints"] == 400.0
    assert metric["events_crossing_proxy_onset"] == 1
    assert metric["engine_detection_coverage"] == 100.0
    assert engines.loc[0, "first_detection_end_cycle"] == 8
    assert engines.loc[0, "first_alert_delay"] == 2
    assert engines.loc[0, "lead_cycles"] == 2
    crossing = events[events["crosses_onset"]]
    assert len(crossing) == 1
    assert not bool(crossing.iloc[0]["valid_post_onset_detection_event"])


def test_ambiguous_windows_are_excluded_and_zero_denominators_are_missing() -> None:
    trace = _scores([0.8, 0.1, 0.9])
    trace["alert_active"] = [True, False, True]
    metric, _, _ = evaluate_alert_policy(trace, _policy(trace, 1, ambiguous={2}))
    assert metric["ambiguous_excluded_endpoints"] == 1
    assert metric["evaluated_endpoints"] == 2
    assert metric["healthy_evaluated_endpoints"] == 0
    assert np.isnan(metric["specificity"])
    assert np.isnan(metric["false_positive_alerted_endpoints_per_1000_healthy_endpoints"])


def test_exact_alignment_rejects_missing_and_duplicate_window_ids() -> None:
    trace = _scores([0.1, 0.2])
    policy = _policy(trace, 2)
    duplicate = policy.copy()
    duplicate.loc[1, "window_id"] = duplicate.loc[0, "window_id"]
    with pytest.raises(ValueError, match="unique"):
        align_policy_frame(trace, duplicate)
    with pytest.raises(ValueError, match="differ"):
        align_policy_frame(trace, policy.iloc[:1])


def _candidate_rows() -> pd.DataFrame:
    rows = []
    policy_ids = ["p10", "p20", "p30"]
    candidates = [
        ("candidate_b", "lof", 90.0, 50.0, 2.0, 5.0, 4.0, 20.0),
        ("candidate_a", "lof", 90.0, 50.0, 2.0, 5.0, 4.0, 20.0),
        ("candidate_c", "ocsvm", 95.0, 61.0, 1.0, 2.0, 2.0, 25.0),
    ]
    for candidate, detector, coverage, fp, false_events, false_engines, delay, lead in candidates:
        for policy_id in policy_ids:
            rows.append(
                {
                    "candidate_id": candidate,
                    "detector_id": detector,
                    "threshold_context": "global",
                    "threshold_rule_id": "q",
                    "ewma_id": "off",
                    "ewma_alpha": np.nan,
                    "persistence": 1,
                    "policy_id": policy_id,
                    "engine_detection_coverage": coverage,
                    "false_positive_alerted_endpoints_per_1000_healthy_endpoints": fp,
                    "false_alert_events_per_1000_healthy_endpoints": false_events,
                    "percent_engines_with_healthy_false_alert": false_engines,
                    "median_first_alert_delay": delay,
                    "median_lead_cycles": lead,
                }
            )
    return pd.DataFrame(rows)


def test_selection_enforces_feasibility_and_lexicographic_tie_break() -> None:
    aggregate = aggregate_candidate_metrics(
        _candidate_rows(),
        selection_policy_ids=["p10", "p20", "p30"],
        feasibility_limit=60.0,
    )
    per_detector, overall = select_best_candidates(aggregate)
    assert set(per_detector["candidate_id"]) == {"candidate_a"}
    assert overall.iloc[0]["candidate_id"] == "candidate_a"
    assert not bool(aggregate.set_index("candidate_id").loc["candidate_c", "feasible"])


def test_no_feasible_candidate_returns_no_winner() -> None:
    aggregate = aggregate_candidate_metrics(
        _candidate_rows(),
        selection_policy_ids=["p10", "p20", "p30"],
        feasibility_limit=10.0,
    )
    per_detector, overall = select_best_candidates(aggregate)
    assert per_detector.empty
    assert overall.empty
