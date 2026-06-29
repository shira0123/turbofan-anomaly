# PROGRESS - Turbofan Anomaly Project

Last updated: 2026-06-29

## Summary (one-line)
Phase 2 is formally complete. EDA and baseline evaluation are finished, artifacts are generated, and baseline metrics are logged.

## Roadmap Status
- Phase 0: Complete
- Phase 1: Complete
- Phase 2: Complete
- Phase 3: Pending
- Phase 4: Pending
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

## Next (priority order)
1. Begin Phase 3 LSTM autoencoder training pipeline using the same windowing assumptions.
2. Implement adaptive thresholding module and calibration loop.
3. Add explainability surrogate and SHAP attributions after deep model error pipeline is stable.

## Notes
- All raw data and model binaries remain local and ignored by git.
- Experiments are tracked in experiments/experiments.csv.
