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

## 2026-08-22 — Recommend the balanced P1/K=6 LSTM at Gate 3

- **Decision status:** Recommended, pending owner approval.
- **Registered screen:** Three P1/K=6 architectures at seed 42, followed by the selected architecture under P0 and P1/K=6 at matched seeds 43–45; nine runs total.
- **Optimization boundary:** Early stopping used 32 monitor engines separated from 124 development engines, all drawn from the training partition. Validation proxy labels did not control gradient updates or early stopping.
- **Architecture recommendation:** `balanced_64x16_l1` (64 hidden units, 16 latent units, one layer, 59,045 parameters). Its Stage 1 mean validation PR-AUC was `0.81208952`, compared with `0.81026176` for the compact model and `0.80874495` for the stacked model.
- **Pipeline recommendation:** P1/K=6. Across matched seeds 43–45, its median mean validation PR-AUC was `0.81088283` with standard deviation `0.00159528`; P0's median was `0.24004696`.
- **Interpretation:** The pipeline effect is consistent within this screen, while the architecture margin is narrow. The LSTM is not declared superior to the P1 classical controls; P1 LOF and One-Class SVM retain higher validation mean PR-AUC diagnostics.
- **Convergence caveat:** Several balanced runs reached or nearly reached the 50-epoch screen limit. A longer final-refit budget must be registered separately after approval.
- **Evidence boundary:** Results use normalized-life validation proxies, not physical anomaly ground truth or held-out test outcomes. No detection threshold is selected.
- **Evidence:** `reports/lstm_v2/` and `configs/lstm/fd002-lstm-screen-results-v1.json`.
- **Owner:** Shivam.

## 2026-08-24 — Consolidate the validated path on `refactor/clean-v3`

- **Decision:** Replace the mixed legacy/prototype layout with one importable `turbofan_anomaly` package, six thin CLI wrappers, governed research documentation, a schema-versioned JSONL run ledger, and an output-cleared training/validation-only EDA notebook.
- **Scope boundary:** This is a structural and provenance refactor. The registered split, P0/P1 preprocessing decisions, classical selection behavior, LSTM screen behavior, metric definitions, configurations, and current report bytes were not changed.
- **Ledger migration:** Migrate 13 `run_20260822_*` records and nine `fd002_lstm_v1_*` records into `experiments/runs_v2.jsonl`; exclude ten historical/smoke rows rather than silently repairing or promoting them. The malformed CSV remains recoverable at base commit `3aa9f0f`.
- **Removal decision:** Remove the prototype API, placeholder explanation behavior, online adaptive-threshold prototype, alternate 70/30 workflows, smoke-only artifacts, obsolete active reports, and superseded documentation after dependency and replacement review. Every tracked removal is recoverable from Git history.
- **Safety boundary:** Metadata generation defaults to training and validation only. Internal-test metadata requires an explicit `--include-internal-test` flag, which was not exercised. The refactor did not open, transform, plot, score, or model the held-out internal test or official NASA test data.
- **Verification:** All 41 synthetic/unit tests passed under Python 3.12.8 and PyTorch 2.5.1+cu121; six CLI `--help` checks passed; AST, JSON/JSONL, notebook structure, local links, path rejection, strict raw/LF/CRLF provenance, registered-byte immutability, and stale-active-reference checks passed. Notebook execution remains pending because allowed split data and registered P0/P1 model artifacts are absent from this checkout.
- **Owner:** Shivam authorized the refactor; Codex implemented and verified it without committing, pushing, opening a PR, or merging.

## 2026-08-25 — Approve Gate 3 and register the governed final LSTM refit

- **Owner approval:** “I approve Gate 3: the balanced 64×16 one-layer LSTM under P1/K=6 may proceed to the registered final-refit protocol. I understand that its architecture advantage was small and that it has not beaten LOF or OCSVM on validation.”
- **Decision:** Freeze `balanced_64x16_l1` under P1/K=6 for the registered final-refit protocol. This approves a fair temporal comparator; it does not declare the LSTM superior to the classical controls.
- **Convergence rule:** Run seeds 43–45 sequentially on the registered engine-disjoint 3,988-development/1,049-monitor training-window assignment, with a 150-epoch maximum and monitor reconstruction loss as the only checkpoint criterion.
- **Epoch lock:** Use the integer median of the three best convergence epochs. Do not replace that rule after validation is visible.
- **Locked refit:** Reinitialize each seed and train for exactly the locked epoch count on all 5,037 eligible training windows. Fit each empirical CDF only on that seed's full-training reconstruction scores.
- **Ensemble:** Average the three per-seed calibrated scores after exact `window_id` alignment. Do not choose a best seed after validation.
- **Evidence boundary:** Validation proxy diagnostics occur only after every locked refit and calibrator exist. Validation does not control gradient updates, early stopping, seeds, or epoch choice. Thresholds, EWMA, persistence, fusion selection, held-out internal-test access, and official NASA-test access are outside this decision.
- **Execution status:** Protocol registration is complete, but project-data training has not run because the four registered P1 training/validation sequence and metadata inputs are absent from this checkout. No result config, final-refit report, successful ledger row, or performance claim exists.
- **Protocol:** `configs/lstm/fd002-lstm-final-refit-protocol-v1.json`.
- **Owner:** Shivam.

## 2026-08-25 — Complete the final LSTM refit and recommend the detector freeze

- **Execution:** The registered `fd002-lstm-final-refit-v1` workflow ran unchanged on the four hash-matched P1/K=6 training/validation inputs using the NVIDIA GeForce GTX 1650. The protocol remained `registered_before_execution`; the separate result config records successful completion.
- **Epoch lock:** Convergence best epochs were 47, 54, and 59 for seeds 43–45. The predeclared integer-median rule therefore locked all three final refits to epoch 54.
- **Final LSTM evidence:** The per-seed mean validation-proxy PR-AUC values were `0.816912`, `0.807820`, and `0.805471`. The predeclared calibrated-score ensemble beat every individual seed at mean PR-AUC `0.822121` and mean ROC-AUC `0.951289`.
- **Negative comparison retained:** The ensemble did not beat P1 LOF (`0.849695`) or P1 One-Class SVM (`0.832808`) on mean PR-AUC. It remained below LOF (`0.964363`), One-Class SVM (`0.964371`), and Isolation Forest (`0.955921`) on mean ROC-AUC.
- **Detector-freeze recommendation:** Freeze P1/K=6 LOF as the primary detector for Gate 4 because it remains the strongest registered detector on the primary mean validation-proxy PR-AUC objective. Retain One-Class SVM as the strongest classical sensitivity control and the calibrated LSTM ensemble as the frozen deep temporal comparator; do not select an individual LSTM seed.
- **Verification:** Three model artifacts, 13 reports, three sets of 9,365 validation scores, the 9,365-row aligned ensemble, and seven new ledger records passed independent hash/schema/reload verification. The complete suite passed 64 tests.
- **Evidence boundary:** These are validation-proxy diagnostics, not accuracy, physical fault-onset performance, or final-test results. No threshold, EWMA, persistence, fusion rule, or alert policy has been selected. Held-out internal-test and official NASA-test data remain unopened.
- **Next gate:** Register the Phase 5 alert-policy study only after the detector set and validation-only selection objective are accepted at Gate 4.
