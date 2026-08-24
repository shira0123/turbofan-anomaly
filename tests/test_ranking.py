from __future__ import annotations

import numpy as np
import pandas as pd

from turbofan_anomaly.evaluation.proxies import registered_validation_policies
from turbofan_anomaly.evaluation.ranking import proxy_ranking_metrics


def test_proxy_ranking_excludes_ambiguous_rows_and_averages_registered_policies() -> None:
    metadata = pd.DataFrame(
        {
            "window_id": ["early", "middle", "late"],
            "engine": [1, 1, 1],
            "start_cycle": [1, 52, 71],
            "end_cycle": [30, 81, 100],
            "max_cycle": [100, 100, 100],
        }
    )
    policy_frames = [
        policy.apply(metadata) for policy in registered_validation_policies()
    ]

    rows, mean_pr_auc, mean_roc_auc = proxy_ranking_metrics(
        np.array([0.1, 0.5, 0.9]), policy_frames
    )

    assert len(rows) == 5
    assert sum(row["selection_policy"] for row in rows) == 3
    assert mean_pr_auc == 1.0
    assert mean_roc_auc == 1.0
    full_window = next(
        row for row in rows if row["policy_id"].endswith("30pct_full_window")
    )
    assert full_window["ambiguous_windows"] == 1
