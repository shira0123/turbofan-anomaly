"""Calibrate adaptive threshold parameters from reconstruction scores."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from scripts.log_experiment import log_experiment
from src.thresholding import AdaptiveThresholdEngine


SCORES_PATH = Path("reports/lstm_ae/reconstruction_scores.csv")
ENGINE_PATH = Path("models/adaptive_threshold.pkl")
SUMMARY_PATH = Path("reports/lstm_ae/threshold_summary.csv")


def main() -> None:
    if not SCORES_PATH.exists():
        raise FileNotFoundError(
            f"Missing reconstruction scores at {SCORES_PATH}. Run scripts.export_lstm_scores first."
        )

    scores_df = pd.read_csv(SCORES_PATH)
    required_cols = {"op_mode", "is_healthy", "reconstruction_error"}
    missing = required_cols - set(scores_df.columns)
    if missing:
        raise RuntimeError(f"Missing required columns in reconstruction scores: {sorted(missing)}")

    healthy_df = scores_df[scores_df["is_healthy"] == 1].copy()
    if healthy_df.empty:
        raise RuntimeError("No healthy reconstruction scores available for threshold calibration")

    engine = AdaptiveThresholdEngine()
    engine.fit_baseline_parameters(
        healthy_errors=healthy_df["reconstruction_error"].values,
        operational_modes=healthy_df["op_mode"].values,
    )

    ENGINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(engine, ENGINE_PATH)

    summary_rows = []
    for mode in sorted(healthy_df["op_mode"].unique()):
        mode_df = healthy_df[healthy_df["op_mode"] == mode]
        mu = engine.mu_per_mode[int(mode)]
        sigma = engine.sigma_per_mode[int(mode)]
        summary_rows.append(
            {
                "op_mode": int(mode),
                "healthy_windows": int(len(mode_df)),
                "mu": mu,
                "sigma": sigma,
                "threshold": mu + engine.k * sigma,
            }
        )

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary_rows).to_csv(SUMMARY_PATH, index=False)

    log_experiment(
        [
            f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_adaptive_threshold",
            datetime.now().isoformat(timespec="seconds"),
            "shivam",
            "adaptive_threshold_calibration",
            "adaptive_threshold",
            str({"alpha": engine.alpha, "k": engine.k, "m": engine.m, "decay": engine.decay, "update_interval": engine.update_interval}),
            int(len(healthy_df)),
            int(len(scores_df)),
            "threshold_modes",
            str(len(summary_rows)),
            f"checkpoint={ENGINE_PATH}; source={SCORES_PATH}",
            str(SUMMARY_PATH),
        ]
    )

    print({
        "checkpoint": str(ENGINE_PATH),
        "summary": str(SUMMARY_PATH),
        "modes": len(summary_rows),
    })


if __name__ == "__main__":
    main()