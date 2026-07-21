# PROGRESS - Turbofan Anomaly Project

Last updated: 2026-07-21

## Summary (one-line)
Phase 2 and the initial Phase 3/4 implementation are now in place, with an inference API checkpoint added and adaptive-threshold calibration completed.

## Current checkpoint (2026-07-21)
- Added a working inference service that loads trained artifacts and returns anomaly predictions.
- Implemented adaptive-threshold calibration and saved the threshold artifact for later evaluation.
- Logged the current experiment runs and documented the implementation state.

## Roadmap Status
- Phase 0: Complete
- Phase 1: Complete
- Phase 2: Complete
- Phase 3: In progress
- Phase 4: In progress
- Phase 5: Pending
- Phase 6: Pending

## Completed
- Environment and repository setup
- FD002 dataset selection and ingestion
- Engine-level split with leakage prevention
- Domain adaptation with KMeans operating condition clustering
- Per-cluster StandardScaler normalization
- Domain-adapted train/test csv generation
- Sliding window sequence generation (window size 30)

## Added This Cycle (Phase 2)
- scripts/run_eda.py
	- Sensor distribution statistics
	- Operating mode counts and plot
	- Cluster validation (silhouette score)
	- Sensor correlation matrix and heatmap
	- Degradation trend plot across engine life bins
- src/models/baselines.py
	- Sequence feature extraction for classical models
	- Metrics: ROC-AUC, Precision@K, False Alarm Rate, Detection Delay, Detection Coverage
	- Isolation Forest and LOF scoring wrappers
- scripts/run_baselines.py
	- Trains Isolation Forest and LOF on healthy windows
	- Evaluates both models on all windows
	- Saves metrics to reports/baselines/baseline_metrics.csv
	- Logs results to experiments/experiments.csv

## Phase 2 Closure Evidence
- EDA outputs are present under reports/eda/.
- Baseline comparison is present in reports/baselines/baseline_metrics.csv.
- Baseline experiments are logged in experiments/experiments.csv.

## Added This Cycle (Phase 3 start)
- src/models/lstm_ae.py
	- LSTM encoder/decoder autoencoder for [batch, time, sensors] inputs
	- Configurable hidden, latent, layer, and dropout dimensions
- scripts/train_lstm_smoke.py
	- Healthy-window training pipeline
	- Checkpoint saving to models/
	- Training curve export to reports/lstm_ae/
	- Experiment logging to experiments/experiments.csv
	- CLI switches for smoke and full runs
- scripts/export_lstm_scores.py
	- Loads the latest or explicit LSTM checkpoint
	- Exports per-window reconstruction errors to reports/lstm_ae/
	- Writes a summary CSV for thresholding and calibration

## Added This Cycle (Phase 4 start)
- src/thresholding/adaptive_threshold.py
	- EWMA-based, per-mode threshold engine
	- Sustained violation handling and optional online background adaptation
- scripts/fit_adaptive_threshold.py
	- Calibrates per-mode thresholds from reconstruction scores
	- Saves threshold artifact to models/
	- Writes threshold summary to reports/lstm_ae/

## Next (priority order)
1. Begin Phase 3 LSTM autoencoder training pipeline using the same windowing assumptions.
2. Implement adaptive thresholding module and calibration loop.
3. Add explainability surrogate and SHAP attributions after deep model error pipeline is stable.

## Notes
- All raw data and model binaries remain local and ignored by git.
- Experiments are tracked in experiments/experiments.csv.
