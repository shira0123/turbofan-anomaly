"""scripts/fit_domain_adapter_and_save.py
Fits KMeans on train split and saves kmeans + per-cluster scalers into models/
Run as module: python -m scripts.fit_domain_adapter_and_save
"""
import pandas as pd
import joblib
import os
from src.data.domain_adapter import OperatingConditionNormalizer
from pathlib import Path

def main():
    RAW_SPLIT = Path("data/splits/train.csv")
    if not RAW_SPLIT.exists():
        raise FileNotFoundError(f"{RAW_SPLIT} not found. Please run the split script or place train.csv at data/splits/train.csv")

    df = pd.read_csv(RAW_SPLIT)
    adapter = OperatingConditionNormalizer(n_clusters=4)
    adapter.fit(df)

    os.makedirs("models", exist_ok=True)
    joblib.dump(adapter.kmeans, "models/kmeans_clusterer.pkl")
    for mode, scaler in adapter.scalers_per_mode.items():
        joblib.dump(scaler, f"models/scaler_cluster_{mode}.pkl")

    print("Saved: models/kmeans_clusterer.pkl and models/scaler_cluster_*.pkl")

if __name__ == "__main__":
    main()
