"""Ranking metrics for explicitly declared degradation-onset proxies."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


def proxy_ranking_metrics(
    calibrated_scores: np.ndarray,
    policy_frames: list[pd.DataFrame],
    *,
    required_selection_policies: int = 3,
) -> tuple[list[dict[str, Any]], float, float]:
    """Evaluate PR-AUC/ROC-AUC while excluding ambiguous proxy windows."""
    scores_all = np.asarray(calibrated_scores, dtype=float).reshape(-1)
    rows: list[dict[str, Any]] = []
    selection_pr: list[float] = []
    selection_roc: list[float] = []
    for policy_frame in policy_frames:
        if len(policy_frame) != len(scores_all):
            raise ValueError("Policy frame and score lengths differ")
        included = policy_frame["proxy_label"].notna().to_numpy()
        labels = policy_frame.loc[included, "proxy_label"].astype(int).to_numpy()
        scores = scores_all[included]
        if len(np.unique(labels)) < 2:
            pr_auc = float("nan")
            roc_auc = float("nan")
        else:
            pr_auc = float(average_precision_score(labels, scores))
            roc_auc = float(roc_auc_score(labels, scores))
        is_selection = bool(policy_frame["selection_policy"].iloc[0])
        if is_selection:
            if not np.isfinite(pr_auc) or not np.isfinite(roc_auc):
                raise RuntimeError("A selection policy produced a non-finite metric")
            selection_pr.append(pr_auc)
            selection_roc.append(roc_auc)
        counts = policy_frame["label_state"].value_counts()
        rows.append(
            {
                "policy_id": str(policy_frame["policy_id"].iloc[0]),
                "policy_semantics": str(policy_frame["policy_semantics"].iloc[0]),
                "selection_policy": is_selection,
                "healthy_windows": int(counts.get("healthy", 0)),
                "ambiguous_windows": int(counts.get("ambiguous", 0)),
                "anomalous_windows": int(counts.get("anomalous", 0)),
                "pr_auc": pr_auc,
                "roc_auc": roc_auc,
            }
        )
    if len(selection_pr) != required_selection_policies:
        raise RuntimeError(
            f"Exactly {required_selection_policies} selection policies are required"
        )
    return rows, float(np.mean(selection_pr)), float(np.mean(selection_roc))
