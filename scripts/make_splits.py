# scripts/make_splits.py
import pandas as pd
from pathlib import Path

RAW = Path("data/raw/train_FD002.txt")
OUT_TRAIN = Path("data/splits/train.csv")
OUT_TEST  = Path("data/splits/test.csv")

def main():
    if not RAW.exists():
        raise FileNotFoundError(f"{RAW} not found. Place C-MAPSS FD002 file at {RAW}")
    cols = ["engine","cycle","op1","op2","op3"] + [f"sensor_{i}" for i in range(1,22)]
    df = pd.read_csv(RAW, sep=r"\s+", header=None, names=cols)
    engines = sorted(df.engine.unique())
    split_idx = int(len(engines) * 0.7)
    train_engines = engines[:split_idx]
    test_engines = engines[split_idx:]
    train_df = df[df.engine.isin(train_engines)].reset_index(drop=True)
    test_df  = df[df.engine.isin(test_engines)].reset_index(drop=True)
    train_df.to_csv(OUT_TRAIN, index=False)
    test_df.to_csv(OUT_TEST, index=False)
    print(f"Created {OUT_TRAIN} ({len(train_df)} rows) and {OUT_TEST} ({len(test_df)} rows)")
    assert set(train_df.engine.unique()).isdisjoint(set(test_df.engine.unique()))
    print("Split validated: no engine overlap")

if __name__ == "__main__":
    main()
