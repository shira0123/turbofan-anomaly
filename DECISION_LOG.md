# Decision Log

This file records consequential research and implementation decisions. Each entry states the decision, rationale, evidence boundary, and owner. Superseded or unvalidated historical decisions remain visible rather than being erased.

## 2025-07-09 — Use FD002 as the primary dataset

- **Decision:** Use NASA C-MAPSS FD002 as the primary study dataset.
- **Rationale:** FD002 contains multiple operating regimes and a single fault mode, which makes it suitable for studying operating-condition effects without adding multi-fault ambiguity.
- **Owner:** Shivam.

## 2025-07-10 — Investigate operating-condition-aware normalization

- **Decision:** Treat per-mode normalization, implemented with operating-condition clustering and mode-specific sensor scalers, as the main research treatment.
- **Rationale:** Operating-condition shifts can look like degradation under a global representation. A mode-aware treatment is therefore compared against a global-normalization control.
- **Evidence boundary:** This was a research hypothesis, not a validated conclusion. The exact clustering choice was revisited in the 2026-08-22 preprocessing study.
- **Owner:** Shivam.

## 2025-07-11 — Use an LSTM autoencoder as the deep sequence model

- **Decision:** Use an LSTM autoencoder as the principal deep unsupervised model after classical controls are established.
- **Rationale:** It provides a sequence reconstruction baseline while retaining a direct per-window anomaly score.
- **Evidence boundary:** The historical smoke runs did not use the current engine-disjoint manifest and are not accepted as research evidence.
- **Owner:** Project team.

## 2025-07-12 — Adopt a machine-readable experiment ledger

- **Decision:** Record experiment configuration, sample counts, metrics, notes, and artifact locations in `experiments/experiments.csv`.
- **Rationale:** A ledger connects reported results to their run configuration and artifacts.
- **Owner:** Shivam.

## 2026-06-27 — Establish classical baselines before deep-model selection

- **Decision:** Evaluate classical anomaly detectors before running the LSTM architecture study.
- **Rationale:** Classical controls make it possible to judge whether a deep sequence model adds value and expose data or evaluation problems at lower computational cost.
- **Owner:** Project team.

## 2026-06-27 — Historical baseline metrics are diagnostic only

- **Decision:** Preserve the historical ROC-AUC, Precision@K, false-alarm, and delay outputs, but do not use them as final comparative evidence.
- **Rationale:** Their data split and proxy-label provenance do not satisfy the revised engine-disjoint protocol.
- **Supersedes:** The earlier assumption that the June 2026 baseline metrics were directly comparable final evidence.
- **Owner:** Shivam.

## 2026-07-21 — Historical inference and adaptive-threshold checkpoint is a prototype

- **Decision:** Retain the inference API and adaptive-threshold implementation as prototype code only.
- **Rationale:** The threshold was calibrated from historical reconstruction scores that are not tied to the current split manifest and approved preprocessing pipeline. Online adaptation can also absorb degradation unless separately constrained and validated.
- **Supersedes:** The earlier description of this checkpoint as “validated.”
- **Owner:** Shivam.

## 2026-08-22 — Freeze an engine-disjoint FD002 split manifest

- **Decision:** Use `configs/splits/fd002-primary-v1.json` as the source of truth for a deterministic 60/20/20 internal split, stratified by maximum-cycle quintile with seed 42.
- **Allocation:** 156 train engines, 52 validation engines, and 52 held-out internal-test engines; there is no engine overlap.
- **Rationale:** All windows from an engine must remain in one partition. A versioned manifest prevents later runs from silently changing the evaluation population.
- **Artifact identity:** Manifest SHA-256 `953f6bee71022a644fc0e3e155f4c212bb2cc9a10794c2665c9d7d9cb6594327`; raw FD002 training-file SHA-256 `bc1d293b8dc6173c1bfb0fff64fe797c2cde35dbb1a1a075dae8ca1177b49a52`.
- **Evidence boundary:** The internal test partition remains frozen until model, preprocessing, proxy policies, and thresholds are fixed. NASA's supplied test set is reserved for later external evaluation.
- **Owner:** Shivam.

## 2026-08-22 — Separate the healthy-training assumption from evaluation proxies

- **Decision:** Fit unsupervised models only on training windows ending in the first 30% of each training engine's observed life. Evaluate on explicit normalized-life proxy policies rather than treating the training rule as ground-truth anomaly labels.
- **Primary validation policies:** Endpoint last 10%, last 20%, and last 30% of observed life.
- **Sensitivity policies:** Full-window last 20% and last 30%, with boundary-crossing windows marked ambiguous and excluded from the corresponding metric.
- **Rationale:** FD002 does not provide per-cycle anomaly labels. Separating assumptions from evaluation policies prevents proxy labels from being presented as physical ground truth.
- **Owner:** Shivam.

## 2026-08-22 — Select six operating regimes for the P1 pipeline

- **Decision:** Compare P0 global normalization against P1 mode-aware normalization with six KMeans operating regimes. Defer more complex preprocessing variants until P0/P1 establish a clear need.
- **Candidates considered:** K=4, K=6, and K=8, fit on training operating settings only.
- **Rationale:** K=6 achieved validation silhouette `0.99703695`, five-seed subsample stability ARI `1.0`, minimum validation occupancy `0.1469696`, and no rare-mode fallback. K=4 merged distinct settings; K=8 was less stable and created a small validation cluster.
- **Approval:** Shivam approved K=6 at the preprocessing decision gate.
- **Evidence:** `reports/preprocessing/model_selection.csv`; report SHA-256 recorded in `configs/preprocessing/fd002-preprocessing-selection-v1.json`.
- **Leakage boundary:** Operating-condition clustering and all sensor scalers are fit on training rows only; sensor scalers use only the early-life training subset.
- **Disclosure:** Aggregate operating-setting ranges and counts from the internal-test partition were printed during an early schema check. They were not used for fitting or selection. This is recorded as a minor procedural exposure; test outcomes and anomaly scores remain unseen.
- **Owner:** Shivam.

## 2026-08-22 — Use validation-only multi-policy selection for classical baselines

- **Decision:** Evaluate PCA reconstruction, One-Class SVM, Isolation Forest, and Local Outlier Factor under both P0 and P1/K=6. Select each model/pipeline candidate by mean validation PR-AUC across the three endpoint policies, with mean ROC-AUC and then candidate ID as deterministic tie-breakers.
- **Rationale:** PR-AUC is appropriate for imbalanced proxy outcomes, and averaging over several declared policies reduces dependence on a single arbitrary anomaly boundary.
- **Score calibration:** Fit each model's empirical score CDF on eligible training scores only.
- **Evidence boundary:** These are validation proxy diagnostics on 52 unseen engines, not held-out test performance and not estimates of real-world fault-detection accuracy. No threshold, F1 score, event metric, or test claim is frozen yet.
- **Evidence:** `reports/baselines_v2/` and `configs/baselines/fd002-classical-baselines-v1.json`.
- **Owner:** Shivam.

## 2026-08-22 — Make tracking and atomic commits part of the experiment protocol

- **Decision:** For every experiment-producing phase, use the sequence: registered configuration → run-specific artifacts and hashes → experiment-ledger entry → decision/progress update → tests → atomic commit.
- **Rationale:** Research conclusions must be traceable to code, configuration, data provenance, and immutable repository history.
- **Commit policy:** Commit completed, verified units promptly on `research-validation-v2`. Do not push or merge without explicit user authorization.
- **Owner:** Shivam.
