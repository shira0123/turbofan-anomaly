"""Run EDA and save visual/statistical artifacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score


TRAIN_PATH = Path("data/processed/train_domain_adapted.csv")
TEST_PATH = Path("data/processed/test_domain_adapted.csv")
OUT_DIR = Path("reports/eda")


def ensure_inputs() -> None:
    if not TRAIN_PATH.exists() or not TEST_PATH.exists():
        raise FileNotFoundError(
            "Missing processed domain-adapted CSV files. "
            "Run split + domain adaptation scripts first."
        )


def save_sensor_distribution_stats(train_df: pd.DataFrame, sensor_cols: list[str]) -> None:
    stats = train_df[sensor_cols].describe().T
    stats.to_csv(OUT_DIR / "sensor_distribution_stats.csv")


def save_operating_mode_plots(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    train_counts = train_df["op_mode"].value_counts().sort_index()
    test_counts = test_df["op_mode"].value_counts().sort_index()

    counts_df = pd.DataFrame({"train": train_counts, "test": test_counts}).fillna(0).astype(int)
    counts_df.to_csv(OUT_DIR / "op_mode_counts.csv")

    ax = counts_df.plot(kind="bar", figsize=(8, 4), title="Operating Mode Counts")
    ax.set_xlabel("op_mode")
    ax.set_ylabel("count")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "op_mode_counts.png", dpi=150)
    plt.close()


def save_cluster_validation(train_df: pd.DataFrame) -> None:
    op_cols = ["op1", "op2", "op3"]
    score = silhouette_score(train_df[op_cols].values, train_df["op_mode"].values)
    pd.DataFrame(
        [{"metric": "silhouette_score_op_space", "value": float(score)}]
    ).to_csv(OUT_DIR / "cluster_validation.csv", index=False)


def save_correlation_heatmap(train_df: pd.DataFrame, sensor_cols: list[str]) -> None:
    corr = train_df[sensor_cols].corr()
    corr.to_csv(OUT_DIR / "sensor_correlation_matrix.csv")

    plt.figure(figsize=(10, 8))
    plt.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    plt.colorbar(label="correlation")
    plt.title("Sensor Correlation Heatmap")
    ticks = np.arange(len(sensor_cols))
    plt.xticks(ticks, sensor_cols, rotation=90, fontsize=7)
    plt.yticks(ticks, sensor_cols, fontsize=7)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "sensor_correlation_heatmap.png", dpi=180)
    plt.close()


def save_degradation_trends(train_df: pd.DataFrame) -> None:
    sensor_candidates = ["sensor_2", "sensor_3", "sensor_4", "sensor_7", "sensor_11"]
    sensor_cols = [c for c in sensor_candidates if c in train_df.columns]
    if not sensor_cols:
        return

    edf = train_df.copy()
    max_cycle = edf.groupby("engine")["cycle"].transform("max")
    edf["life_fraction"] = edf["cycle"] / max_cycle
    edf["life_bin"] = pd.cut(edf["life_fraction"], bins=10, labels=False, include_lowest=True)

    trend = edf.groupby("life_bin")[sensor_cols].mean().reset_index()
    trend.to_csv(OUT_DIR / "degradation_trends.csv", index=False)

    plt.figure(figsize=(9, 5))
    for sensor in sensor_cols:
        plt.plot(trend["life_bin"], trend[sensor], marker="o", label=sensor)
    plt.title("Mean Sensor Trend Across Engine Life")
    plt.xlabel("life bin (0=early, 9=late)")
    plt.ylabel("normalized sensor value")
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "degradation_trends.png", dpi=150)
    plt.close()


def main() -> None:
    ensure_inputs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)
    sensor_cols = [c for c in train_df.columns if c.startswith("sensor_")]

    save_sensor_distribution_stats(train_df, sensor_cols)
    save_operating_mode_plots(train_df, test_df)
    save_cluster_validation(train_df)
    save_correlation_heatmap(train_df, sensor_cols)
    save_degradation_trends(train_df)

    print(f"EDA artifacts saved under: {OUT_DIR}")


if __name__ == "__main__":
    main()