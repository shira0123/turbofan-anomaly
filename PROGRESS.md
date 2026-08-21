# Progress — Turbofan Anomaly Project

Last updated: 2026-08-22

## Current state

The revised validation foundation and LSTM architecture screen are implemented. The project now has a deterministic engine-disjoint split, train-only preprocessing with an approved six-regime P1 treatment, explicit proxy-label policies, classical controls, and a nine-run validation-only LSTM screen. The balanced one-layer architecture and P1/K=6 pipeline are recommended at Gate 3 but are not frozen until owner approval. The held-out internal-test partition has not been transformed, scored, or used for model selection.

Active branch: `research-validation-v2`

## Roadmap status

| Phase | Status | Evidence / next gate |
|---|---|---|
| 0. Evidence and reproducibility audit | Audit complete; remediation ongoing | Historical outputs classified as diagnostic/prototype where provenance is insufficient; missing research-planning documents still need recovery or replacement. |
| 1. Engine-disjoint data foundation | Complete | Versioned split manifest and aligned window metadata; 7 data-foundation tests are included in the full suite. |
| 2. Preprocessing study | Complete | K=6 approved for P1; P0 global normalization retained as control. |
| 3. Classical validation baselines | Complete | Eight selected P0/P1 model variants evaluated on validation proxies only. |
| 4. LSTM autoencoder study | Screen complete; Gate 3 pending | Nine registered runs completed and verified; balanced one-layer architecture with P1/K=6 is recommended for the final training protocol. |
| 5. Threshold and event-level evaluation | Pending | Freeze on validation only after model selection. |
| 6. Held-out and external evaluation | Pending | Open internal test once; NASA supplied test remains the external evaluation set. |

## Phase 1 — Data foundation

- Split source of truth: `configs/splits/fd002-primary-v1.json`.
- Strategy: 60/20/20 engine-disjoint allocation, seed 42, stratified by maximum-cycle quintile.
- Engine counts: 156 train, 52 validation, 52 held-out internal test.
- Row counts: 32,107 train, 10,873 validation, 10,779 test.
- Window counts at length 30: 27,583 train, 9,365 validation, 9,271 test.
- Engine overlap across partitions: zero.
- Raw-source and manifest hashes are recorded in the split manifest.
- Existing artifacts that do not declare this manifest are treated as legacy and incompatible with current validation/test claims.

## Phase 2 — Preprocessing decision

- P0: one global sensor scaler, fit on eligible early-life training rows only.
- P1: training-only KMeans on the three operating settings, then one sensor scaler per learned regime; rare regimes fall back to the training-only global scaler.
- Sensor-scaler fit population: 9,561 early-life rows from all 156 training engines.
- Candidate study: K=4, K=6, and K=8, using train/validation silhouette, occupancy, and five-seed 80%-engine-subsample stability.
- Selected treatment: P1 with K=6.

| K | Validation silhouette | Stability ARI mean | Minimum validation occupancy | Decision |
|---:|---:|---:|---:|---|
| 4 | 0.85179450 | 1.00000000 | 0.14816518 | Rejected: merges distinct operating settings. |
| 6 | 0.99703695 | 1.00000000 | 0.14696956 | Selected. |
| 8 | 0.89306060 | 0.93224270 | 0.04902051 | Rejected: less stable and over-splits a small regime. |

No candidate required the rare-mode fallback. Selection evidence is under `reports/preprocessing/`, and the approved choice is registered in `configs/preprocessing/fd002-preprocessing-selection-v1.json`.

## Phase 3 — Classical baseline validation

- Fit population: 5,037 healthy-assumption windows from 156 training engines.
- Validation population: 9,365 windows from 52 unseen engines.
- Window representation: 30 cycles × 21 sensors, summarized into 63 mean, standard-deviation, and endpoint-change features for classical models.
- Candidate count: 24 fits across two preprocessing pipelines, four detector families, and three parameter settings per family.
- Model selection: mean validation PR-AUC across endpoint last-10%, last-20%, and last-30% policies; mean ROC-AUC and candidate ID are tie-breakers.

Selected validation diagnostics:

| Pipeline | Model | Selected parameter | Mean PR-AUC | Mean ROC-AUC |
|---|---|---|---:|---:|
| P0 global | Isolation Forest | `max_samples=5000` | 0.25459545 | 0.56109940 |
| P0 global | LOF | `n_neighbors=20` | 0.49531022 | 0.77264825 |
| P0 global | One-Class SVM | `nu=0.01`, `gamma=scale` | 0.34887664 | 0.68644511 |
| P0 global | PCA | `variance=0.99` | 0.72171928 | 0.92947633 |
| P1 K=6 | Isolation Forest | `max_samples=256` | 0.78916934 | 0.95592104 |
| P1 K=6 | LOF | `n_neighbors=20` | 0.84969513 | 0.96436313 |
| P1 K=6 | One-Class SVM | `nu=0.10`, `gamma=scale` | 0.83280767 | 0.96437111 |
| P1 K=6 | PCA | `variance=0.90` | 0.77240729 | 0.92503450 |

All 12 matched parameter pairs have higher mean validation PR-AUC under P1 than P0. This is evidence that P1 is promising enough to carry into the LSTM study; it is not a held-out result or a final causal conclusion.

## Phase 4 — LSTM architecture screen

- Protocol: `configs/lstm/fd002-lstm-screen-protocol-v1.json`, committed before execution.
- Optimization population: 3,988 early-life windows from 124 development engines.
- Early-stopping population: 1,049 early-life windows from 32 separate training engines.
- Model-selection population: 9,365 windows from the same 52 unseen validation engines used by the registered proxy policies.
- Stage 1: three predeclared P1/K=6 architectures at seed 42.
- Stage 2: the selected architecture under P0 and P1/K=6 at matched seeds 43, 44, and 45.
- Total completed runs: 9 of 9.

Stage 1 validation diagnostics:

| Architecture | Parameters | Best epoch | Monitor MSE | Mean PR-AUC | Mean ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Compact: 32 hidden, 8 latent, 1 layer | 16,733 | 31 | 0.48414079 | 0.81026176 | 0.95314101 |
| Balanced: 64 hidden, 16 latent, 1 layer | 59,045 | 49 | 0.47989513 | 0.81208952 | 0.95193381 |
| Stacked: 64 hidden, 16 latent, 2 layers | 125,605 | 13 | 0.48459463 | 0.80874495 | 0.95121474 |

The registered rule recommends the balanced architecture because it has the highest mean validation PR-AUC. The margin over the compact model is only `0.00183`, so this is a pragmatic screen result rather than evidence that the larger architecture is materially superior.

Stage 2 matched-seed robustness:

| Pipeline | Seeds | Median mean PR-AUC | Mean mean PR-AUC | PR-AUC standard deviation | Median mean ROC-AUC |
|---|---|---:|---:|---:|---:|
| P0 global | 43–45 | 0.24004696 | 0.24198629 | 0.00557644 | 0.52340031 |
| P1 K=6 | 43–45 | 0.81088283 | 0.81109563 | 0.00159528 | 0.95104697 |

P1/K=6 is stable across the matched seeds and is recommended for the final LSTM training protocol. The LSTM does not automatically replace the classical controls: the selected P1 LOF and One-Class SVM validation diagnostics (`0.84970` and `0.83281` mean PR-AUC) remain higher than the LSTM screen median. Those comparisons are validation-proxy diagnostics, not held-out performance.

## Evaluation-policy counts

| Policy | Healthy | Ambiguous | Anomalous |
|---|---:|---:|---:|
| Endpoint last 10% | 8,253 | 0 | 1,112 |
| Endpoint last 20% | 7,170 | 0 | 2,195 |
| Endpoint last 30% | 6,075 | 0 | 3,290 |
| Full-window last 20% | 7,170 | 1,505 | 690 |
| Full-window last 30% | 6,075 | 1,508 | 1,782 |

These normalized-life policies are evaluation proxies, not physical anomaly ground truth.

## Verification state

- Full automated suite: 26 tests passing.
- Git whitespace/error check: passing.
- Phase 3 artifacts are deterministic across reruns.
- Eight serialized model artifacts reproduce the recorded validation scores within serialization precision.
- Nine LSTM artifacts match their registered hashes and reproduce all 84,285 recorded per-window scores. Maximum absolute differences are `7.1e-15` for raw scores and `1.2e-16` for calibrated scores.
- Configuration files record input, output, report, and model hashes.

## Test-data status

- The internal-test partition has not been transformed, scored, thresholded, or used for selection.
- A prior schema check printed aggregate internal-test counts and operating-setting ranges. This did not influence fitting or selection, but is retained in the decision log as a procedural disclosure.
- The test partition stays frozen until preprocessing, model, proxy policies, and thresholds are fixed.

## Known limitations and open evidence work

- Historical Isolation Forest/LOF, LSTM smoke, reconstruction-score, and adaptive-threshold outputs do not declare the current manifest and are not accepted as comparative research evidence.
- The historical LSTM smoke split contains overlapping windows from the same engine and must not be cited as validation performance.
- FD002 supplies run-to-failure trajectories but no per-cycle anomaly labels; reported PR/ROC values therefore depend on declared normalized-life proxies.
- Stage 1 used one seed and the three architecture scores are close; architecture superiority should not be overstated.
- Several balanced-model runs reached or nearly reached the 50-epoch screen budget. A final refit needs a separately registered, longer convergence budget after Gate 3 approval.
- The LSTM screen used 3,988 development windows while the classical models used all 5,037 eligible training windows; direct family comparisons should be treated as screening evidence, not a controlled model-capacity conclusion.
- The Master Execution Bible v2, literature-validation report, and validated evidence matrix referenced by the research workflow are not present in the repository. They must be recovered or rebuilt without inventing conclusions.
- Thresholds, event-level delay/coverage, false-alarm rates, final test metrics, and external-test metrics are not yet frozen.

## Tracking protocol from this checkpoint

Every experiment-producing phase must leave all of the following before it is considered complete:

1. A registered, versioned configuration with fixed seeds and data-manifest identity.
2. Run-specific artifacts plus hashes for inputs and outputs.
3. One or more rows in `experiments/experiments.csv`, with the evidence class stated in `notes`.
4. A decision-log update for any accepted/rejected alternative or protocol change.
5. A progress update that distinguishes completed evidence from pending work.
6. Relevant tests and an atomic commit. Pushes and merges remain explicit user decisions.

## Next action

Gate 3 decision: approve or revise the recommended balanced one-layer LSTM with P1/K=6. After approval, register a longer final-refit budget using all 5,037 eligible training windows, then freeze the model before threshold and event-level validation. No held-out test data will be opened before those choices are fixed.
