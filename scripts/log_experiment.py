# scripts/log_experiment.py
import csv, sys
from pathlib import Path

def log_experiment(row):
    path = Path("experiments/experiments.csv")
    if not path.exists():
        raise RuntimeError("experiments/experiments.csv not found")
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

if __name__ == "__main__":
    # Usage: python -m scripts.log_experiment run_id datetime owner name model params train_size valid_size metric_name metric_value notes artifact_path
    log_experiment(sys.argv[1:])
