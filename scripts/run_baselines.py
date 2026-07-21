"""Train and evaluate baseline anomaly detectors."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.log_experiment import log_experiment
from src.models.baselines import (
    evaluate_baseline,
    run_isolation_forest,
    run_lof_novelty,
    sequence_summary_features,
)


SEQS_PATH = Path("data/processed/sequences_train.npy")
MODES_PATH = Path("data/processed/op_modes_train.npy")
HEALTH_PATH = Path("data/processed/is_healthy_train.npy")
TRAIN_DA_PATH = Path("data/processed/train_domain_adapted.csv")
OUT_DIR = Path("reports/baselines")


def build_sequence_metadata(train_df: pd.DataFrame, window_size: int = 30, healthy_fraction: float = 0.3) -> pd.DataFrame:
    rows = []
    for engine in sorted(train_df["engine"].unique()):
        ed = train_df[train_df["engine"] == engine].sort_values("cycle")
        n = len(ed)
        max_i = n - window_size + 1
        healthy_cutoff = int(n * healthy_fraction)
        onset_idx = max(0, healthy_cutoff - window_size + 1)

        for local_i in range(max_i):
            window_end = local_i + window_size
            rows.append(
                {
                    "engine": int(engine),
                    "local_window_idx": int(local_i),
                    "window_end": int(window_end),
                    "is_healthy": int(window_end <= healthy_cutoff),
                    "onset_idx": int(onset_idx),
                }
            )
    return pd.DataFrame(rows)


def validate_inputs() -> None:
    required = [SEQS_PATH, MODES_PATH, HEALTH_PATH, TRAIN_DA_PATH]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")


def result_to_row(result, params: dict, train_size: int, valid_size: int) -> list[str]:
    return [
        f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{result.model_name}",
        datetime.now().isoformat(timespec="seconds"),
        "shivam",
        f"baseline_{result.model_name}",
        result.model_name,
        str(params),
        str(train_size),
        str(valid_size),
        "roc_auc",
        f"{result.roc_auc:.6f}",
        (
            f"p_at_k={result.precision_at_k:.6f}; "
            f"far={result.false_alarm_rate:.6f}; "
            f"delay={result.mean_detection_delay}; "
            f"coverage={result.detection_coverage:.6f}"
        ),
        str(OUT_DIR / "baseline_metrics.csv"),
    ]


def main() -> None:
    validate_inputs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sequences = np.load(SEQS_PATH)
    _ = np.load(MODES_PATH)
    is_healthy = np.load(HEALTH_PATH).astype(int)
    train_df = pd.read_csv(TRAIN_DA_PATH)

    metadata = build_sequence_metadata(train_df)
    if len(metadata) != len(sequences):
        raise RuntimeError(
            f"Metadata windows ({len(metadata)}) do not match sequence count ({len(sequences)})."
        )

    x = sequence_summary_features(sequences)
    y_true = 1 - is_healthy

    healthy_mask = is_healthy == 1
    x_train_healthy = x[healthy_mask]
    contamination = float(np.clip(y_true.mean(), 0.01, 0.49))

    onset_by_engine = metadata.groupby("engine")["onset_idx"].first().to_dict()
    engine_ids = metadata["engine"].values
    local_window_index = metadata["local_window_idx"].values

    if_scores = run_isolation_forest(x_train_healthy, x, contamination=contamination)
    if_result = evaluate_baseline(
        model_name="isolation_forest",
        scores=if_scores,
        y_true=y_true,
        engine_ids=engine_ids,
        local_window_index=local_window_index,
        onset_index_by_engine=onset_by_engine,
    )

    lof_scores = run_lof_novelty(x_train_healthy, x, contamination=contamination)
    lof_result = evaluate_baseline(
        model_name="lof",
        scores=lof_scores,
        y_true=y_true,
        engine_ids=engine_ids,
        local_window_index=local_window_index,
        onset_index_by_engine=onset_by_engine,
    )

    metrics_df = pd.DataFrame(
        [
            {
                "model": if_result.model_name,
                "roc_auc": if_result.roc_auc,
                "precision_at_k": if_result.precision_at_k,
                "false_alarm_rate": if_result.false_alarm_rate,
                "mean_detection_delay": if_result.mean_detection_delay,
                "detection_coverage": if_result.detection_coverage,
            },
            {
                "model": lof_result.model_name,
                "roc_auc": lof_result.roc_auc,
                "precision_at_k": lof_result.precision_at_k,
                "false_alarm_rate": lof_result.false_alarm_rate,
                "mean_detection_delay": lof_result.mean_detection_delay,
                "detection_coverage": lof_result.detection_coverage,
            },
        ]
    )
    metrics_df.to_csv(OUT_DIR / "baseline_metrics.csv", index=False)

    common_params = {
        "feature": "summary(mean,std,slope)",
        "window": 30,
        "contamination": contamination,
        "train_fit": "healthy_only",
    }
    log_experiment(result_to_row(if_result, common_params, len(x_train_healthy), len(x)))
    log_experiment(result_to_row(lof_result, common_params, len(x_train_healthy), len(x)))

    print(metrics_df)
    print(f"Saved baseline metrics to: {OUT_DIR / 'baseline_metrics.csv'}")


if __name__ == "__main__":
    main()