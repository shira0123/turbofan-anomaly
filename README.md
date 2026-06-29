# Turbofan Anomaly Detection

Short project summary:
- Goal: Detect early anomalies in turbofan engines using context-aware preprocessing and anomaly models.

Quick start (Windows PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# place dataset: data/raw/train_FD002.txt
python -m scripts.make_splits
python -m scripts.fit_domain_adapter_and_save
python -m scripts.transform_and_save_processed
python -m scripts.create_sequences_save
python -m scripts.run_eda
python -m scripts.run_baselines
python -m scripts.train_lstm_smoke
```

Analysis artifacts:
- EDA reports: reports/eda/
- Baseline metrics: reports/baselines/baseline_metrics.csv
- Experiment ledger: experiments/experiments.csv

Artifacts (local, not committed):
- data/raw/ (raw dataset; do not commit)
- data/processed/ (processed csv and npy files)
- models/ (saved scalers, kmeans, model checkpoints)

Where to find docs:
- PROGRESS.md (progress tracker)
- DECISION_LOG.md (decisions and rationale)
- experiments/experiments.csv (experiment ledger)

Contact:
- Data and Modeling Lead: Shivam Rajput (@shira0123)
