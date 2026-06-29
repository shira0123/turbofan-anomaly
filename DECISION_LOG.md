# DECISION LOG

This file records major design decisions, why they were made, and who decided.

## 2025-07-09 � Use FD002 as primary dataset
**Who:** Shivam (Data & Modeling Lead)  
**Why:** Multi-regime dataset exercises domain-adaptation; single-fault simplifies analysis for baseline experiments. (Refer MASTER_EXECUTION_BIBLE.md)

## 2025-07-10 � Per-mode normalization (KMeans + scaler per mode)
**Who:** Shivam  
**Why:** Prevent false positives due to operating-condition shifts; easier to interpret per-mode reconstructions.

## 2025-07-11 � LSTM Autoencoder baseline
**Who:** Team  
**Why:** Good unsupervised baseline for reconstruction-based anomaly detection; surrogate for explainability.

## 2025-07-12 � Experiments ledger (CSV) adopted
**Who:** Shivam  
**Why:** Keep machine-readable record of hyperparameters + metrics for reproducibility.

## 2026-06-27 - Baseline-first evaluation before LSTM
**Who:** Team  
**Why:** Implement classical anomaly baselines (Isolation Forest and LOF) before LSTM autoencoder work to establish a measurable benchmark and de-risk later deep model choices.

## 2026-06-27 - Unified baseline metrics policy
**Who:** Team  
**Why:** Standardize baseline comparison using ROC-AUC, Precision@K, False Alarm Rate, and Detection Delay/Coverage to ensure model tradeoffs are visible before thresholding and explainability phases.
