"""
scripts/transform_and_save_processed.py
Applies saved KMeans + per-cluster scalers to train/test splits.
"""

import pandas as pd
import joblib
import os
from pathlib import Path

def main():
    os.makedirs("data/processed", exist_ok=True)

    train_path = Path("data/splits/train.csv")
    test_path  = Path("data/splits/test.csv")

    if not train_path.exists():
        raise FileNotFoundError("train.csv not found. Run make_splits first.")

    train = pd.read_csv(train_path)
    test  = pd.read_csv(test_path)

    # ?? Convert sensor columns to float BEFORE scaling
    sensor_cols = [c for c in train.columns if c.startswith("sensor_")]
    train[sensor_cols] = train[sensor_cols].astype(float)
    test[sensor_cols]  = test[sensor_cols].astype(float)

    kmeans = joblib.load("models/kmeans_clusterer.pkl")

    scalers = {}
    for i in range(kmeans.n_clusters):
        scalers[i] = joblib.load(f"models/scaler_cluster_{i}.pkl")

    def transform_df(df):
        df = df.copy()
        op_cols = ['op1','op2','op3']
        df['op_mode'] = kmeans.predict(df[op_cols].values)

        for mode, scaler in scalers.items():
            mask = df.op_mode == mode
            if mask.sum() > 0:
                df.loc[mask, sensor_cols] = scaler.transform(
                    df.loc[mask, sensor_cols]
                )
        return df

    train_p = transform_df(train)
    test_p  = transform_df(test)

    train_p.to_csv("data/processed/train_domain_adapted.csv", index=False)
    test_p.to_csv("data/processed/test_domain_adapted.csv", index=False)

    print("Saved processed train and test CSV files.")

if __name__ == "__main__":
    main()
