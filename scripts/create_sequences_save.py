"""
scripts/create_sequences_save.py
Creates windowed sequences from domain-adapted training data.
Run as: python -m scripts.create_sequences_save
"""

import pandas as pd
import numpy as np
import os

def create_sequences(df, sensor_cols, window_size=30, step=1, healthy_fraction=0.3):
    sequences, op_modes, is_healthy = [], [], []

    for engine in sorted(df.engine.unique()):
        ed = df[df.engine == engine].sort_values("cycle")

        arr = ed[sensor_cols].values
        modes = ed["op_mode"].values

        max_i = len(arr) - window_size + 1
        healthy_cutoff = int(len(arr) * healthy_fraction)

        for i in range(0, max_i, step):
            window = arr[i:i+window_size]
            sequences.append(window)
            op_modes.append(modes[i + window_size // 2])
            is_healthy.append((i + window_size) <= healthy_cutoff)

    return np.array(sequences), np.array(op_modes), np.array(is_healthy)


def main():
    os.makedirs("data/processed", exist_ok=True)

    df = pd.read_csv("data/processed/train_domain_adapted.csv")
    sensor_cols = [f"sensor_{i}" for i in range(1,22)]

    seqs, modes, healthy = create_sequences(
        df,
        sensor_cols,
        window_size=30,
        step=1,
        healthy_fraction=0.3
    )

    np.save("data/processed/sequences_train.npy", seqs)
    np.save("data/processed/op_modes_train.npy", modes)
    np.save("data/processed/is_healthy_train.npy", healthy)

    print("Saved sequences and metadata.")
    print("Sequences shape:", seqs.shape)


if __name__ == "__main__":
    main()
