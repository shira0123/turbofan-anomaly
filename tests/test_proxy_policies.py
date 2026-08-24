from __future__ import annotations

import pandas as pd

from turbofan_anomaly.evaluation.proxies import (
    NormalizedLifeOnsetPolicy,
    registered_validation_policies,
    training_eligible_windows,
)


def _metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "window_id": "w1",
                "engine": 1,
                "start_cycle": 1,
                "end_cycle": 30,
                "max_cycle": 100,
            },
            {
                "window_id": "w2",
                "engine": 1,
                "start_cycle": 52,
                "end_cycle": 81,
                "max_cycle": 100,
            },
            {
                "window_id": "w3",
                "engine": 1,
                "start_cycle": 71,
                "end_cycle": 100,
                "max_cycle": 100,
            },
        ]
    )


def test_endpoint_policy_assigns_score_to_window_end_cycle() -> None:
    labels = NormalizedLifeOnsetPolicy(0.20, "endpoint", True).apply(_metadata())

    assert labels["onset_cycle"].tolist() == [81, 81, 81]
    assert labels["label_state"].tolist() == ["healthy", "anomalous", "anomalous"]
    assert labels["proxy_label"].astype(int).tolist() == [0, 1, 1]
    assert labels["selection_policy"].all()


def test_full_window_policy_excludes_onset_crossing_windows() -> None:
    labels = NormalizedLifeOnsetPolicy(0.30, "full_window", False).apply(
        _metadata()
    )

    assert labels["onset_cycle"].tolist() == [71, 71, 71]
    assert labels["label_state"].tolist() == ["healthy", "ambiguous", "anomalous"]
    assert labels["proxy_label"].isna().tolist() == [False, True, False]
    assert not labels["selection_policy"].any()


def test_training_assumption_does_not_label_non_fit_windows() -> None:
    eligible = training_eligible_windows(_metadata(), 0.30)
    assert eligible.tolist() == [True, False, False]
    policies = registered_validation_policies()
    assert len(policies) == 5
    assert sum(policy.selection_policy for policy in policies) == 3
