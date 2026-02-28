# Turbofan Anomaly Detection

Short project summary:
- Goal: Detect early anomalies in turbofan engines using domain-adaptive LSTM autoencoders + adaptive thresholding + SHAP explanations.
- Phase plan: See MASTER_EXECUTION_BIBLE.md (source of truth).

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
python -m scripts.train_lstm_smoke
Artifacts (local, not committed):

data/raw/ (raw dataset; DO NOT COMMIT)

data/processed/ (processed csvs and npy files)

models/ (saved scalers, kmeans, model checkpoints)

Where to find docs:

MASTER_EXECUTION_BIBLE.md (project plan)

PROGRESS.md (progress tracker)

DECISION_LOG.md (decisions & rationale)

experiments/experiments.csv (experiment ledger)

Contact:

Data & Modeling Lead: Shivam Rajput (@shira0123)
