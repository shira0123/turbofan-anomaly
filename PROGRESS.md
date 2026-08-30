# Progress — Turbofan Anomaly Project

Last updated: 2026-08-30

## Current state

The revised validation foundation, LSTM architecture screen, governed final LSTM refit, and validation-only alert-policy study are implemented and verified. Gate 4 froze the PCA reconstruction per-mode q=0.995 / EWMA 0.20 / persistence-8 policy for confirmatory evaluation, with the calibrated LSTM ensemble retained as the nonprimary deep comparator. These are validation-proxy decisions, not final-test results. The held-out internal-test partition remains unopened, and evaluation is blocked before access because the exact fitted P1/K=6 preprocessor is absent and unhashed.

Active implementation branch: `research/phase5-validation`; Phase 5 execution-code commit `180eefb5585c3d994a9d68afa22f6f564cc21dd2`

## Roadmap status

| Phase | Status | Evidence / next gate |
|---|---|---|
| 0. Evidence and reproducibility audit | Complete; clean-v3 merged | Bible v3, 100-source evidence matrix, claims ledger, artifact/migration manifests, path/hash policy, and the 29-record current-protocol run ledger are present. |
| 1. Engine-disjoint data foundation | Complete | Versioned split manifest and aligned window metadata; 7 data-foundation tests are included in the full suite. |
| 2. Preprocessing study | Complete | K=6 approved for P1; P0 global normalization retained as control. |
| 3. Classical validation baselines | Complete | Eight selected P0/P1 model variants evaluated on validation proxies only. |
| 4. LSTM autoencoder study | Complete; final refit verified | Nine screen runs plus three training-only convergence runs, three locked refits, and the calibrated ensemble are recorded. Locked epoch: 54. |
| 5. Threshold and event-level evaluation | Complete; Gate 4 approved | Five score sources, 1,280 candidates, and 6,400 candidate-policy rows independently verified. PCA endpoint-mode q=0.995 / EWMA 0.20 / persistence-8 policy frozen for later confirmatory evaluation. |
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

## Gate 3 closure and final-refit registration — 2026-08-25

- Owner approval: “I approve Gate 3: the balanced 64×16 one-layer LSTM under P1/K=6 may proceed to the registered final-refit protocol. I understand that its architecture advantage was small and that it has not beaten LOF or OCSVM on validation.”
- Registered protocol: `configs/lstm/fd002-lstm-final-refit-protocol-v1.json`, status `registered_before_execution`.
- Convergence selection is predeclared for seeds 43, 44, and 45 using only the registered 3,988-development/1,049-monitor training-engine split, with a 150-epoch maximum and monitor-loss early stopping.
- Locked epoch count is the integer median of the three convergence best epochs. Each seed must then refit for exactly that count on all 5,037 eligible training windows, with no monitor split or validation feedback.
- The frozen ensemble is the arithmetic mean of the three window-ID-aligned calibrated validation scores. Each empirical CDF is fitted only on that seed's 5,037 eligible training scores.
- The four permitted P1 sequence/metadata inputs were provisioned with exact registered hashes, and the registered workflow completed without changing the frozen protocol.
- Phase 5 threshold, EWMA, persistence, fusion selection, and all internal/official test evaluation remain pending. No threshold has been selected.

## Final LSTM refit evidence — 2026-08-25

- Convergence best epochs were 47, 54, and 59 for seeds 43, 44, and 45; the predeclared median rule locked all three final refits to epoch 54.
- All three fixed-epoch refits used the same 5,037 eligible training windows. Each empirical CDF was fitted only on that seed's training reconstruction scores.
- Mean endpoint-policy validation-proxy PR-AUC was `0.816912`, `0.807820`, and `0.805471` for seeds 43–45. The calibrated ensemble reached `0.822121` mean PR-AUC and `0.951289` mean ROC-AUC, beating every individual final-refit LSTM seed.
- The ensemble remained below LOF (`0.849695`) and One-Class SVM (`0.832808`) on mean PR-AUC, and below LOF (`0.964363`), One-Class SVM (`0.964371`), and Isolation Forest (`0.955921`) on mean ROC-AUC.
- Independent reload verification reproduced three sets of 9,365 raw/calibrated scores and 9,365 aligned ensemble scores. Maximum differences were `7.11e-15` raw and `1.11e-16` calibrated; three artifacts, 13 reports, and seven new ledger records were hash/schema verified.
- Result classification is `validation_proxy_diagnostic_not_test_performance`. No best seed was selected, no threshold was selected, and no held-out internal-test or official NASA-test data was opened.

## Phase 5 metadata-lineage correction and alert-policy evidence — 2026-08-27

- The original Phase 1 window metadata remains byte-for-byte unchanged with null `op_mode`; blocked protocol v1 is preserved at SHA-256 `9734c465071401387f7ad2fc79abfc207d0eeb0e8724685267f74b7528f8cb6c`.
- Two registered P1/K=6 cycle frames were provisioned only after raw-hash verification. Derived train/validation window-context metadata assigns `op_mode` from `(engine, end_cycle)` using semantics `p1_k6_endpoint_cycle_mode_v1`; no reclustering, sensor inference, majority vote, or test access occurred.
- Eligible training mode counts are mode 0: 756, 1: 768, 2: 719, 3: 765, 4: 747, and 5: 1,282. Both splits contain exactly modes 0–5, every mode exceeds the 100-window minimum, and train/validation engines remain disjoint.
- Protocol v2 retained the five detectors, two threshold contexts, eight threshold rules, four EWMA states, four persistence values, five proxy policies, FAR constraint, event definitions, and selection order from v1. It evaluated 280 threshold rows, 1,280 candidates, and 6,400 candidate-policy rows.
- All five score sources reproduced their registered validation ranking diagnostics. Maximum raw-score difference was `7.11e-15`, maximum calibrated-score difference `1.11e-16`, and maximum ranking-metric difference `1.11e-16`.

Per-detector validation recommendations:

| Detector | Recommended policy | Min / mean coverage | Worst FP endpoints / 1,000 | Median policy delay | Result note |
|---|---|---:|---:|---:|---|
| LOF | global, mean + 2 std, EWMA 0.20, persistence 1 | 0.00% / 0.00% | 0.000 | missing | Feasible but emitted no alerts; negative result. |
| One-Class SVM | per-mode q=0.995, EWMA 0.20, persistence 8 | 46.15% / 78.85% | 45.802 | 20 cycles | Feasible; delay aspiration missed. |
| Isolation Forest | global, mean + 2 std, EWMA 0.20, persistence 1 | 0.00% / 0.00% | 0.000 | missing | Feasible but emitted no alerts; negative result. |
| PCA reconstruction | per-mode q=0.995, EWMA 0.20, persistence 8 | 57.69% / 78.21% | 44.711 | 23 cycles | Overall validation recommendation. |
| LSTM calibrated ensemble | per-mode q=0.995, EWMA 0.20, persistence 3 | 53.85% / 80.13% | 41.318 | 18 cycles | Feasible; delay aspiration missed. |

For the overall PCA recommendation, endpoint final-10%/20%/30% policies had engine coverage `57.69%`, `86.54%`, and `90.38%`; false-positive endpoints `44.711`, `15.342`, and `9.053` per 1,000 healthy endpoints; false-alert events `3.514`, `1.534`, and `0.658` per 1,000; false-alert-engine rates `44.23%`, `15.38%`, and `7.69%`; median delays `7`, `23`, and `38` cycles; and median leads `13`, `18`, and `22` cycles. All three FAR values satisfy the `<6%` endpoint target, but only the final-10% delay meets the `<=12`-cycle aspiration; the registered aggregate median delay is 23 cycles and therefore misses it.

The full-window final-20% sensitivity policy excluded 1,505 ambiguous windows and yielded precision/recall/F1 `0.8435/0.8594/0.8514`. The full-window final-30% policy excluded 1,508 and yielded `0.9473/0.5544/0.6995`. Pairwise complementarity was recorded without evaluating fusion. Independent verification reproduced five score sources, all tables, 16 report hashes, five local bundle hashes, and six ledger rows. Gate 4 subsequently froze the PCA recommendation; the threshold remains validation-selected and is not final-test-validated.

## Evaluation-policy counts

| Policy | Healthy | Ambiguous | Anomalous |
|---|---:|---:|---:|
| Endpoint last 10% | 8,253 | 0 | 1,112 |
| Endpoint last 20% | 7,170 | 0 | 2,195 |
| Endpoint last 30% | 6,075 | 0 | 3,290 |
| Full-window last 20% | 7,170 | 1,505 | 690 |
| Full-window last 30% | 6,075 | 1,508 | 1,782 |

These normalized-life policies are evaluation proxies, not physical anomaly ground truth.

## Verification state at the 2026-08-22 checkpoint

- Full automated suite: 26 tests passing.
- Git whitespace/error check: passing.
- Phase 3 artifacts are deterministic across reruns.
- Eight serialized model artifacts reproduce the recorded validation scores within serialization precision.
- Nine LSTM artifacts match their registered hashes and reproduce all 84,285 recorded per-window scores. Maximum absolute differences are `7.1e-15` for raw scores and `1.2e-16` for calibrated scores.
- Configuration files record input, output, report, and model hashes.

## Clean-v3 refactor verification — 2026-08-24

- Full synthetic/unit suite: 41 tests passed under Python 3.12.8 and PyTorch 2.5.1+cu121 (CUDA 12.1 build, NVIDIA GTX 1650 available); pytest used an explicit isolated base-temp because the account's default pytest temp directory denied access.
- Six retained CLI `--help` checks passed without running any experiment-producing workflow.
- All 26 checked authority/current config and report files matched their expected raw checkout SHA-256 values; strict registered LF hash forms also verified where declared.
- Package/import, AST, TOML, JSON, 22-line JSONL round-trip, notebook JSON/code/output state, Markdown links, path traversal/drive/UNC rejection, safe metadata defaults, and stale active-reference checks passed.
- The EDA notebook is structurally valid and output-cleared but was not executed: the allowed training/validation CSVs and registered P0/P1 model artifacts are absent from this checkout.
- No held-out internal-test or official-test data was accessed. No split materialization, preprocessing fit, model training on project data, score reproduction, or report regeneration was performed.
- No commit, push, PR creation, or merge was performed; the complete unstaged diff remains for owner review.

## Test-data status

- The internal-test partition has not been transformed, scored, thresholded, or used for selection.
- A prior schema check printed aggregate internal-test counts and operating-setting ranges. This did not influence fitting or selection, but is retained in the decision log as a procedural disclosure.
- The test partition stays frozen until preprocessing, model, proxy policies, and thresholds are fixed.

## Known limitations and open evidence work

- Historical Isolation Forest/LOF, LSTM smoke, reconstruction-score, and adaptive-threshold outputs do not declare the current manifest and are not accepted as comparative research evidence.
- The historical LSTM smoke split contains overlapping windows from the same engine and must not be cited as validation performance.
- FD002 supplies run-to-failure trajectories but no per-cycle anomaly labels; reported PR/ROC values therefore depend on declared normalized-life proxies.
- Stage 1 used one seed and the three architecture scores are close; architecture superiority should not be overstated.
- The final LSTM refit closed the longer-convergence question, but its ensemble still did not surpass the strongest P1 classical controls on the primary validation-proxy ranking objective.
- The classical and LSTM families now use the same 5,037 eligible final-fit windows, but model-family comparisons remain validation-selected proxy diagnostics without engine-bootstrap uncertainty.
- The Master Execution Bible v3 and validated 100-source evidence matrix are now present under `docs/research/`; earlier references to a missing v2 authority are superseded by the approved v3 research package.
- Phase 5 produced a validation-only alert-policy recommendation and Gate 4 froze it for confirmatory evaluation. Engine-bootstrap uncertainty, final internal-test metrics, and external-test metrics remain pending. The policy may be described as frozen, but not as final-test validated.

## Gate 4 approval and final-evaluation readiness — 2026-08-30

- Owner approval froze `pca_reconstruction__per_mode__quantile_0.995__ewma_alpha_0.20__persistence_8` as the primary confirmatory policy. Approval retains the validation-only evidence boundary, the achieved endpoint FAR target, and the missed 12-cycle aggregate delay aspiration.
- `configs/evaluation/fd002-final-evaluation-protocol-v1.json` freezes the P1/K=6 preprocessing and endpoint-mode lineage, PCA bundle and internal fingerprints, training-only empirical-CDF calibration, all six per-mode thresholds, EWMA/persistence state, proxy exclusions, event definitions, metrics, comparator identity, and authority/model hashes.
- The independent readiness verifier confirmed 10/10 authority hashes and the PCA bundle, LSTM ensemble bundle, and three final LSTM checkpoint hashes. It checked and opened zero held-out inputs and did not check the official NASA test.
- Readiness is blocked before test access because `models/preprocessing/p1_k6.joblib` is absent and has no registered artifact hash. The registered FD002 source needed to reproduce that fitted preprocessor is also absent. No substitute was built or inferred.
- Held-out availability and hashes remain deliberately uninspected. A later explicit test-access authorization plus a new readiness record are required; the frozen policy cannot change.

## Tracking protocol from this checkpoint

Every experiment-producing phase must leave all of the following before it is considered complete:

1. A registered, versioned configuration with fixed seeds and data-manifest identity.
2. Run-specific artifacts plus hashes for inputs and outputs.
3. One or more schema-valid records in `experiments/runs_v2.jsonl`, with an explicit `evidence_class`, evidence boundary, config identity, and artifact identity.
4. A decision-log update for any accepted/rejected alternative or protocol change.
5. A progress update that distinguishes completed evidence from pending work.
6. Relevant tests and an atomic commit. Pushes and merges remain explicit user decisions.

## Next action

Provision and hash-register the exact training-fitted P1/K=6 preprocessor without accessing test data, then create a new readiness record. Do not access the held-out internal test without a separate explicit authorization. Do not access the official NASA test.
