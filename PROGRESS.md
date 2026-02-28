# PROGRESS — Turbofan Anomaly Project

Last updated: (fill date)

## Summary (one-line)
Phase 0 & Phase 1 complete locally (split, domain-adapter, windowing). Entering Phase 2 (model training).

## Completed
- Repo scaffold (src, scripts, data, models, experiments)
- Dataset placed: data/raw/train_FD002.txt
- scripts/make_splits.py executed ? data/splits created
- scripts/fit_domain_adapter_and_save.py executed ? models/kmeans_clusterer.pkl and scaler_cluster_*.pkl
- scripts/transform_and_save_processed.py executed ? data/processed/*.csv
- scripts/create_sequences_save.py executed ? data/processed/sequences_train.npy, op_modes, is_healthy

## In progress / Next (priority order)
1. Train LSTM AE on healthy windows ? scripts/train_lstm_full.py (Owner: Data & Modeling)
2. Compute recon errors, fit adaptive threshold ? scripts/compute_recon_errors.py, scripts/fit_adaptive_threshold.py
3. Train surrogate + SHAP ? scripts/train_shap_surrogate.py
4. API & demo ? src/api/main.py + docker

## Blockers
- (list blockers, e.g., GPU OOM on batch_size X)

## Notes
- All raw data & models are local and ignored by git.
- See experiments/ for run logs.
