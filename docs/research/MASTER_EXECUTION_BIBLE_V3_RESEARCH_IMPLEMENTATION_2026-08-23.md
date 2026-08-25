# Master Execution Bible v3 — Research and Implementation Protocol

**Project:** Operating-condition-aware anomaly detection for turbofan engines
**Primary dataset:** NASA C-MAPSS FD002
**Version:** 3.0
**Evidence cutoff:** 23 August 2026
**Repository checkpoint audited:** `research-validation-v2` at `3aa9f0fd6b6f8f92395e3f4940b839859a84664d`
**Literature base:** 100-source evidence matrix v3
**Status:** Active implementation authority after owner approval

> This Bible supersedes v2 for future implementation and scientific claims. It does not erase v2, the decision log, progress history, old results, or legacy artifacts. Those remain provenance. When this document conflicts with executable evidence, the evidence hierarchy in Section 2 applies.

---

# 0. How to Use This Bible

This document has four jobs:

1. state what the project is actually trying to prove;
2. distinguish completed evidence from planned work;
3. control implementation so that leakage, accidental test use, and untraceable results do not enter the study;
4. help student contributors understand and defend every important decision.

Before any experiment, read:

- Section 1 for the research question;
- Section 2 for evidence and claim rules;
- Section 4 for the current checkpoint;
- the relevant module specification in Section 8;
- the decision gate in Section 10.

Before reporting any number, verify:

- which engines produced it;
- whether it is training, validation, or held-out test evidence;
- which proxy-label policy was used;
- which metric definition and aggregation rule were used;
- which config, commit, artifact, and random seed reproduce it.

---

# 1. North Star

## 1.1 Problem

FD002 sensor measurements vary for at least two different reasons:

1. the engine is operating under a different legitimate operating condition; and
2. the engine is degrading.

An anomaly detector can fail if it treats normal operating-condition changes as faults. The project therefore studies whether explicitly modeling operating context improves anomaly ranking and operational alert behavior on unseen engines.

## 1.2 Primary research question

> On unseen C-MAPSS FD002 engines, how much does operating-condition-aware preprocessing improve anomaly ranking and alert behavior compared with global preprocessing, under multiple declared degradation-onset proxy policies?

## 1.3 Secondary questions

1. Do condition-aware thresholds add value after condition-aware preprocessing is already used?
2. How much do EWMA smoothing and persistence reduce false alerts, and what delay do they introduce?
3. Does the LSTM autoencoder add value over PCA, Isolation Forest, LOF, and One-Class SVM under the same split and evaluation protocol?
4. Are conclusions stable when the healthy-training fraction or anomaly-onset proxy changes?
5. Does score fusion improve a predeclared operational metric enough to justify its complexity?

## 1.4 Defensible contribution

> A leakage-controlled, reproducible comparative and ablation study of global versus operating-condition-aware preprocessing, classical and LSTM-autoencoder anomaly scores, contextual alert policies, and onset-label sensitivity on engine-disjoint FD002 data.

This is primarily an **experimental-methodology contribution**, not a claim of a new anomaly-detection algorithm.

## 1.5 Claims explicitly outside scope

Until new evidence satisfies the final publication gate, do not claim:

- the first condition-aware method for C-MAPSS;
- the first use of per-regime scaling, K-Means, LSTM autoencoders, residualization, persistence, or score fusion in turbofan studies;
- true physical fault-onset detection from FD002;
- production readiness or real-aircraft validation;
- that the LSTM is superior to classical models;
- that validation PR-AUC is final test performance;
- that a sensor-deviation heuristic is SHAP;
- that any legacy target has been achieved.

## 1.6 Success criteria

The project is successful when it provides:

1. an auditable engine-disjoint experiment;
2. a fair P0-versus-P1 comparison;
3. strong simple controls and a fairly trained LSTM;
4. threshold and event-level evaluation selected only on validation engines;
5. sensitivity to the unknown degradation-onset definition;
6. engine-level uncertainty and failure-case analysis;
7. one untouched internal-test evaluation after freezing choices;
8. code, artifacts, documentation, and claims that agree;
9. explanations that every team member can defend.

---

# 2. Evidence, Literature, and Claims Policy

## 2.1 Evidence hierarchy

When descriptions disagree, use this order:

1. executable code, automated tests, raw/split/config hashes, stored models, stored scores, and reproducible reports;
2. registered experiment protocols and frozen configurations;
3. `DECISION_LOG.md` and `PROGRESS.md` at the relevant commit;
4. this Bible and the claims ledger;
5. the validated literature evidence matrix and validation report;
6. explanatory guides, README files, presentations, and historical plans.

Documentation never upgrades a missing experiment into a result.

## 2.2 Result classes

Every number must carry one class:

| Class | Meaning | Allowed use |
|---|---|---|
| Target | Desired future value | Planning only |
| Smoke result | Small execution check | Engineering progress only |
| Historical diagnostic | Old or protocol-incompatible output | Debugging/history only |
| Development result | Current training-side diagnostic | Model development only |
| Validation result | Engine-disjoint validation evidence | Selection and bounded interim reporting |
| Sensitivity result | Validation/test result under an alternate declared assumption | Robustness analysis |
| Final internal-test result | One frozen run on untouched internal-test engines | Final comparison and paper claims |
| External result | Evaluation on the separately declared NASA test or another dataset | Generalization evidence |

No target, example, smoke result, or historical diagnostic may be promoted to a validation or final result.

## 2.3 Literature evidence rule

The 100-source matrix is a structured evidence register, not a claim that all related literature has been exhausted.

Access status must remain visible:

- `full_text_checked`: PDF or full HTML inspected far enough to verify the relevant method, protocol, or reported result;
- `full_text_checked_prior_review`: full text was inspected in the earlier validated review;
- `abstract_checked`: suitable for discovery and broad background only;
- `abstract_or_record_checked_prior_review`: earlier screening evidence only;
- `official_record_checked`: authoritative dataset or technical record, not necessarily an empirical detector paper.

A strong novelty, method, or numerical comparison claim requires full-text verification of the relevant passages. Abstract-only evidence may guide discovery but must not support a precise comparative claim.

Current matrix quality summary:

| Item | Count |
|---|---:|
| Total sources | 100 |
| Tier A | 90 |
| Tier B | 9 |
| Tier C | 1 |
| Core sources | 42 |
| Full text checked in this or the prior review | 68 |

The matrix includes peer-reviewed papers, preprints, foundational methods, NASA technical/dataset records, and evaluation studies. It is deliberately broader than a table of directly comparable FD002 results.

## 2.4 Numerical comparison rule

Two numbers may be placed in the same direct-comparison column only when these semantics are compatible:

1. dataset variant;
2. train/validation/test population and experimental unit;
3. anomaly or onset label definition;
4. metric definition;
5. score threshold or operating-point selection;
6. point-, range-, event-, or engine-level aggregation;
7. use or non-use of point adjustment;
8. repeated-run or single-run summary.

If any item differs, show the literature number as **context only** and explain the mismatch. Do not compare PR-AUC with accuracy, F1, detection rate, or RUL score as if they measured the same outcome.

## 2.5 Claims ledger

Create `docs/research/CLAIMS_LEDGER.md` with one row per proposed claim:

| Field | Required content |
|---|---|
| Claim ID | Stable identifier |
| Proposed wording | Exact sentence intended for report/paper |
| Evidence class | Validation, sensitivity, final test, or external |
| Run/config | Reproducible ID and path |
| Split | Manifest and population |
| Label policy | Exact policy ID |
| Metric | Definition and aggregation |
| Uncertainty | CI or repeated-seed summary |
| Literature support | Source IDs and access status |
| Contradicting evidence | Known limitations or negative results |
| Status | Planned, supported, weakened, rejected |

---

# 3. What the New Literature Changes

## 3.1 Findings that directly change implementation

| Literature finding | Project consequence |
|---|---|
| Operating-condition clustering, normalization, and residualization already exist in C-MAPSS/prognostics research | Do not claim novelty for K-Means or per-regime scaling; evaluate them as a controlled treatment |
| Autoencoder and LSTM reconstruction are established anomaly/health-index methods | The LSTM-AE is a benchmark component, not the contribution by itself |
| Simple baselines often remain competitive across anomaly benchmarks | Keep PCA, LOF, OCSVM, and IF as first-class controls |
| Time-series anomaly rankings depend strongly on metric and post-processing choices | Freeze score, threshold, persistence, and aggregation semantics; report multiple operational metrics |
| Point adjustment can inflate apparent performance | Prohibit point-adjusted headline F1 |
| FD002 has run-to-failure trajectories but no physical per-cycle anomaly labels | Treat all onset boundaries as explicit proxies and perform sensitivity analysis |
| Dynamic thresholds, EWMA, CUSUM, EVT, persistence, and change-point methods are established | Compare a small registered alert-policy set; do not claim a novel threshold without evidence |
| Online adaptation can absorb anomalies during drift | Keep online threshold recalibration off in the primary study |
| Model-agnostic explanations can be temporally misleading or low-fidelity | Prefer native reconstruction contributions; use SHAP only with a real method and fidelity evaluation |
| N-CMAPSS supplies richer, more realistic flight profiles | Reserve it as a future/external extension, not a silent replacement for FD002 |

## 3.2 Research scope after the review

The project should not respond to the larger literature by adding every modern model. The minimum publishable study is stronger when it isolates a small number of causal contrasts:

1. P0 global versus P1 K=6 condition-aware preprocessing;
2. classical controls versus the selected LSTM-AE;
3. global versus per-mode thresholds;
4. smoothing/persistence off versus on;
5. stable versus unstable conclusions across onset assumptions;
6. best single detector versus fusion only if complementarity exists.

Modern models such as transformers, GANs, graph networks, normalizing flows, Deep SVDD, DAGMM, and change-point systems belong in related work or a later extension unless a registered result exposes a specific need.

---

# 4. Verified Repository Checkpoint

## 4.1 Source of truth

This checkpoint was verified on branch `research-validation-v2` at commit `3aa9f0f`. A different local VS Code branch or working tree must be re-audited before implementation.

## 4.2 Phase status

| Phase | Status | Evidence boundary |
|---|---|---|
| Phase 0 — evidence foundation | Audit complete; remediation incomplete | Claims ledger, environment lock, ledger migration, and path portability still open |
| Phase 1 — engine-disjoint split | Complete | Deterministic 60/20/20 manifest; zero engine overlap |
| Phase 2 — preprocessing study | Complete | K=6 selected on validation evidence; P0 retained as control |
| Phase 3 — classical baselines | Complete | Validation proxy results only |
| Phase 4 — LSTM screen | Nine-run screen complete; Gate 3 pending | Validation proxy results only; final refit not done |
| Phase 5 — threshold/event study | Not started | No frozen F1, FAR, persistence, or delay result |
| Phase 6 — sensitivity/fusion/explanation | Not started | Optional components remain conditional |
| Phase 7 — final/internal/external evaluation | Not started | Internal-test scores remain unopened by the study |

## 4.3 Data foundation

| Item | Verified value |
|---|---:|
| FD002 engines | 260 |
| Training engines | 156 |
| Validation engines | 52 |
| Held-out internal-test engines | 52 |
| Training rows | 32,107 |
| Validation rows | 10,873 |
| Internal-test rows | 10,779 |
| Training windows, length 30 | 27,583 |
| Validation windows, length 30 | 9,365 |
| Internal-test windows, length 30 | 9,271 |
| Engine overlap | 0 |

Manifest: `configs/splits/fd002-primary-v1.json`
Split method: 60/20/20 by engine, seed 42, stratified by maximum-cycle quintile.

## 4.4 Plain-language meaning of P0 and P1

- **P0 global:** fit one sensor scaler on eligible early-life rows from training engines, then use that same scaler everywhere.
- **P1 K=6:** scale the three operating settings using training statistics, learn six operating regimes on training data, and fit one sensor scaler per regime using eligible early-life training rows. A frozen global scaler is the declared rare-regime fallback.

P1 is not a model architecture. It is a preprocessing pipeline.

## 4.5 K selection

| K | Validation silhouette | Stability ARI mean | Minimum validation occupancy | Decision |
|---:|---:|---:|---:|---|
| 4 | 0.85179450 | 1.00000000 | 0.14816518 | Rejected: merged distinct conditions |
| 6 | 0.99703695 | 1.00000000 | 0.14696956 | Selected |
| 8 | 0.89306060 | 0.93224270 | 0.04902051 | Rejected: less stable and over-split a small regime |

This result validates K=6 as the current preprocessing choice. It does not prove that six physical operating regimes were discovered in a causal sense.

## 4.6 Classical validation results

Fit population: 5,037 eligible early-life windows from 156 training engines.
Validation population: 9,365 windows from 52 unseen engines.
Selection metric: mean validation PR-AUC over endpoint final-10%, final-20%, and final-30% normalized-life proxy policies.

| Pipeline | Detector | Selected parameter | Mean PR-AUC | Mean ROC-AUC |
|---|---|---|---:|---:|
| P0 | Isolation Forest | `max_samples=5000` | 0.254595 | 0.561099 |
| P0 | LOF | `n_neighbors=20` | 0.495310 | 0.772648 |
| P0 | One-Class SVM | `nu=0.01`, `gamma=scale` | 0.348877 | 0.686445 |
| P0 | PCA | `variance=0.99` | 0.721719 | 0.929476 |
| P1 K=6 | Isolation Forest | `max_samples=256` | 0.789169 | 0.955921 |
| P1 K=6 | LOF | `n_neighbors=20` | **0.849695** | 0.964363 |
| P1 K=6 | One-Class SVM | `nu=0.10`, `gamma=scale` | **0.832808** | 0.964371 |
| P1 K=6 | PCA | `variance=0.90` | 0.772407 | 0.925035 |

All 12 matched parameter pairs favored P1 over P0 on mean validation PR-AUC. This supports carrying P1 forward. It is not a final causal conclusion because the policies and pipeline were selected using validation evidence.

## 4.7 LSTM screen results

Registered protocol:

- 3,988 eligible windows from 124 training engines for optimization;
- 1,049 eligible windows from 32 separate training engines for early stopping;
- 9,365 windows from 52 validation engines for model selection;
- nine total runs;
- Stage 1: three architectures under P1 at seed 42;
- Stage 2: selected architecture under P0 and P1 at matched seeds 43–45.

| Architecture | Parameters | Best epoch | Mean PR-AUC | Meaning |
|---|---:|---:|---:|---|
| Compact 32×8, one layer | 16,733 | 31 | 0.810262 | Nearly tied |
| Balanced 64×16, one layer | 59,045 | 49 | **0.812090** | Recommended by registered rule |
| Stacked 64×16, two layers | 125,605 | 13 | 0.808745 | No benefit in screen |

Matched-seed robustness:

| Pipeline | Seeds | Median mean PR-AUC | Mean PR-AUC | Standard deviation |
|---|---|---:|---:|---:|
| P0 | 43–45 | 0.240047 | 0.241986 | 0.005576 |
| P1 K=6 | 43–45 | **0.810883** | 0.811096 | 0.001595 |

Interpretation:

- P1 is stable and substantially better than P0 within this screen.
- The architecture margin is tiny; do not claim the balanced architecture is scientifically superior.
- P1 LOF and OCSVM remain stronger validation controls than the screened LSTM.
- The LSTM screen used fewer optimization windows than the classical fit, so cross-family differences are not yet a fully controlled final comparison.

## 4.8 Verification evidence

- 26 automated tests passed at the checkpoint.
- Eight serialized classical artifacts reproduce their recorded validation scores.
- Nine LSTM checkpoint hashes were verified.
- All 84,285 stored LSTM validation scores were reproduced.
- Maximum observed reproduction differences were approximately `7.1e-15` raw and `1.2e-16` calibrated.
- The study did not score the held-out internal test.

## 4.9 Open evidence problems

1. Gate 3 has not been formally closed by the owner.
2. The final LSTM refit on all 5,037 eligible training windows has not run.
3. Phase 5 thresholds, EWMA, persistence, false-alert, and delay metrics do not exist under the current protocol.
4. Healthy-fraction and onset-policy sensitivity are incomplete.
5. A claims ledger is missing.
6. A complete environment lock is missing.
7. Some JSON report/model paths use Windows backslashes and are not portable.
8. Historical rows in `experiments/experiments.csv` are not strictly parseable as standard CSV because of pre-quote spaces and embedded comma formatting.
9. Current and legacy scripts coexist, making the execution path difficult to understand.
10. The API and adaptive-threshold code are legacy prototypes and are not part of the validated pipeline.

---

# 5. Scientific Design

## 5.1 Experimental unit

The experimental unit is the **engine trajectory**. A window is a model input, not an independent engine.

Consequences:

- all windows from one engine stay in one split;
- monitor engines and development engines remain disjoint;
- uncertainty is estimated by engine, not by overlapping window;
- failure cases are reported per engine;
- test access occurs only after the entire pipeline is frozen.

## 5.2 Window contract

Default window shape:

\[
X \in \mathbb{R}^{N \times 30 \times 21}
\]

where:

- `N` is the number of windows;
- `30` is the chronological cycle length;
- `21` is the number of sensor values per cycle.

Every window must retain:

| Field | Purpose |
|---|---|
| `dataset_variant` | Prevent silent FD001/FD002 mixing |
| `manifest_id` | Bind the window to a split |
| `split` | Train, validation, internal test, or external |
| `engine_id` | Prevent leakage and enable engine aggregation |
| `window_index` | Stable row identity |
| `start_cycle` / `end_cycle` | Preserve chronology |
| `max_cycle` | Compute normalized life and RUL proxies |
| `normalized_life_start/end` | Apply onset policies reproducibly |
| `rul_proxy_start/end` | Support alternate onset definitions |
| `operating_mode` | Audit contextual transforms/thresholds |
| `pipeline_id` | Distinguish P0 and P1 arrays |
| `healthy_fraction` | Record training assumption |
| `training_eligible` | Control one-class fitting |
| `policy_id` / `label` | Keep evaluation assumptions separate |

## 5.3 Healthy training versus anomaly evaluation

These are not the same label.

- **Healthy-training fraction:** early-life portion allowed to fit one-class models and calibrators.
- **Onset proxy:** rule used only to evaluate whether scores rank or detect late-life windows.

Primary development assumption: first 30% of observed training life is eligible for healthy-only fitting.

Required sensitivity:

| Dimension | Registered values |
|---|---|
| Healthy-training fraction | 20%, 30%, 40% |
| Endpoint late-life proxy | final 10%, 20%, 30% |
| Full-window proxy | final 20%, 30%; boundary windows ambiguous |
| RUL proxy | 130 and 150 cycles, if compatible with the chosen representation |
| Change-point estimate | Secondary analysis only; never called ground truth |

## 5.4 Split protocol

1. Keep `fd002-primary-v1` frozen for the main study.
2. Fit every learned transform on training engines only.
3. Use monitor engines only for LSTM convergence/early stopping.
4. Use validation engines for candidate, threshold, and policy selection.
5. Freeze preprocessing, detector, calibration, threshold, smoothing, persistence, and metric code.
6. Evaluate once on the held-out internal test.
7. Treat the official NASA test set as a separately specified external/generalization study because its trajectories are truncated and its endpoint information differs.

## 5.5 Score direction and calibration

Every detector must expose a raw score where **larger means more anomalous**.

An empirical CDF calibrator may map training scores to a common `[0,1]` scale:

\[
c(s)=\frac{1}{n}\sum_{i=1}^{n}\mathbf{1}(s_i \leq s)
\]

Calibration is fitted on declared training scores only. It is not recomputed on validation or test sequences.

## 5.6 LSTM reconstruction score

For one window:

\[
e=\frac{1}{30\times21}\sum_{t=1}^{30}\sum_{j=1}^{21}(x_{t,j}-\hat{x}_{t,j})^2
\]

The project assumes a model fitted on early-life patterns will reconstruct similar windows well and unusual/degrading windows less well. This is a modeling assumption to test, not a guarantee.

---

# 6. Target Research Architecture

## 6.1 Offline experiment flow

1. validate raw FD002 schema and hash;
2. load frozen engine manifest;
3. fit P0 and P1 preprocessing on eligible training rows;
4. generate chronological arrays and enriched metadata;
5. fit classical controls and the selected LSTM protocol;
6. produce raw scores with a common direction;
7. fit score calibration on eligible training scores;
8. tune threshold, EWMA, and persistence on validation engines;
9. run onset and healthy-fraction sensitivity;
10. close all human decision gates;
11. freeze a versioned pipeline bundle;
12. score the held-out internal test once;
13. compute engine-level uncertainty, failure cases, and paper artifacts;
14. optionally evaluate the official NASA test set under a separate protocol.

## 6.2 Phase 5 alert flow

For each engine in chronological order:

> calibrated detector score → optional EWMA → global/per-mode threshold → persistence counter → alert event → event-level metrics

EWMA:

\[
z_t=\alpha s_t+(1-\alpha)z_{t-1}
\]

Persistence `m` means an alert begins only after `m` consecutive threshold violations. It can reduce isolated false alerts but necessarily adds delay.

## 6.3 Primary threshold study

Register a bounded validation-only grid:

| Factor | Values |
|---|---|
| Score source | P1 LOF, P1 OCSVM, P1 PCA, final P1 LSTM; IF optional |
| Threshold context | Global, per-mode |
| Threshold rule | Healthy-score quantile; mean + `kσ` |
| EWMA | Off; on with a small registered alpha set |
| Persistence | 1, 3, 5, 8 |
| Online recalibration | Off |

Select using a predeclared operational objective, for example:

> maximize engine detection coverage subject to a maximum validation false-alert-event rate, then minimize median delay as tie-breaker.

Do not select by whichever metric looks best after inspection.

## 6.4 Fusion policy

Fusion is optional and must earn inclusion.

Proceed only if the best single detectors show useful error complementarity across engines and onset policies. Compare:

- best single detector;
- equal-weight calibrated-score average;
- rank/percentile fusion;
- at most one validation-selected low-complexity weighted fusion.

Reject fusion if the gain is inconsistent, smaller than uncertainty, or obtained only by adding validation-tuned parameters.

## 6.5 Explanation policy

Primary explanation:

\[
e_j=\frac{1}{30}\sum_{t=1}^{30}(x_{t,j}-\hat{x}_{t,j})^2
\]

Report per-sensor reconstruction contribution and, optionally, a time-by-sensor heat map. Contributions should reconcile with the total reconstruction score within numerical tolerance.

SHAP is optional. Use the name “SHAP” only when the SHAP algorithm is actually run on the frozen detector or a documented surrogate whose fidelity is measured. A sensor deviation from its own temporal mean is not SHAP.

## 6.6 Interface policy

API/dashboard work follows the research pipeline. A versioned deployment bundle must include:

- feature order and window length;
- P0/P1 preprocessing objects;
- detector artifact;
- calibrator;
- threshold/EWMA/persistence configuration;
- explanation method;
- manifest/config/commit identity.

The primary paper does not depend on a production API.

---

# 7. Target Repository Structure

The refactor should converge toward this structure without destroying evidence:

```text
project-root/
├── README.md
├── DECISION_LOG.md
├── PROGRESS.md
├── pyproject.toml
├── .python-version                 # optional
├── .gitattributes
├── configs/
│   ├── splits/
│   ├── preprocessing/
│   ├── baselines/
│   ├── lstm/
│   ├── alerting/
│   └── evaluation/
├── docs/
│   ├── research/
│   │   ├── MASTER_EXECUTION_BIBLE_V3.md
│   │   ├── LITERATURE_EVIDENCE_MATRIX.xlsx
│   │   └── CLAIMS_LEDGER.md
│   └── guides/
│       └── PROJECT_UNDERSTANDING_GUIDE.md
├── notebooks/
│   └── 01_fd002_eda.ipynb
├── src/
│   └── turbofan_anomaly/
│       ├── data/
│       │   ├── io.py
│       │   ├── splits.py
│       │   ├── preprocessing.py
│       │   ├── windows.py
│       │   └── metadata.py
│       ├── evaluation/
│       │   ├── proxies.py
│       │   ├── ranking.py
│       │   ├── alerts.py
│       │   └── uncertainty.py
│       ├── models/
│       │   ├── classical.py
│       │   ├── lstm_autoencoder.py
│       │   └── lstm_training.py
│       ├── alerting/
│       │   ├── calibration.py
│       │   ├── thresholds.py
│       │   └── persistence.py
│       ├── explainability/
│       │   └── reconstruction.py
│       └── api/                    # prototype/deferred
├── scripts/                        # thin CLI wrappers only
├── experiments/
│   ├── experiments.csv             # preserved historical ledger
│   └── experiments_v2.csv          # schema-valid ledger if migration is approved
├── reports/
│   ├── current/
│   └── legacy/                     # only if archival move is approved
└── tests/
```

Rules:

- `src/` contains reusable logic; `scripts/` only parses arguments and calls library functions.
- notebooks call package functions and do not become a second implementation.
- `configs/` controls experiments; no important constant lives only inside a notebook.
- reports are derived evidence; configs and manifests identify how they were created.
- raw data and large generated arrays/models remain outside ordinary Git unless explicitly managed.
- historical evidence is migrated or archived with a manifest; it is never silently deleted.

---

# 8. Module Specifications and Acceptance Criteria

## M0 — Repository and evidence hygiene

**Deliverables**

- dependency/import graph;
- current-versus-legacy inventory;
- migration manifest with old path, new path, evidence class, hashes, and action;
- environment lock;
- canonical path policy;
- claims ledger;
- schema-valid experiment ledger for new runs.

**Acceptance**

- no artifact or decision history is silently lost;
- existing hashes and metrics do not change during structural refactor;
- Windows and POSIX paths resolve through canonical relative paths;
- historical ledger remains preserved byte-for-byte or its migration is explicitly recorded;
- all future rows parse with a declared schema version.

## M1 — Data loading and split manifest

**Deliverables**

- strict FD002 loader;
- schema checks;
- deterministic split manifest;
- raw and manifest hashes;
- zero-overlap tests.

**Acceptance**

- 156/52/52 engine allocation reproduces exactly;
- row/window counts reconcile;
- no window crosses engines;
- no test modeling operation occurs before the final gate.

## M2 — Operating context and sensor preprocessing

**Deliverables**

- P0 global preprocessor;
- P1 K=6 operating-setting scaler, K-Means model, and per-mode sensor scalers;
- K study artifacts;
- explicit rare-mode fallback.

**Acceptance**

- every learned statistic is fitted on training data only;
- K=6 evidence reproduces;
- transforms are finite and deterministic;
- P0/P1 differ only in the intended treatment.

## M3 — Windows and metadata

**Deliverables**

- `(N,30,21)` arrays;
- enriched metadata table;
- training eligibility fields;
- registered proxy-policy outputs.

**Acceptance**

- array length equals metadata length;
- chronology and engine boundaries are preserved;
- policy labels are reproducible from metadata rather than stored as unexplained booleans;
- ambiguous windows remain explicitly ambiguous where required.

## M4 — Classical detectors

**Minimum set**

- PCA reconstruction;
- One-Class SVM;
- Isolation Forest;
- LOF in novelty-compatible mode.

**Acceptance**

- fit only on eligible training windows;
- larger score always means more anomalous;
- selected artifacts reproduce validation scores;
- runtime and memory are recorded;
- classical models remain eligible for the final system.

## M5 — Final LSTM refit

**Approved candidate after Gate 3**

- architecture: balanced 64 hidden, 16 latent, one layer;
- pipeline: P1 K=6;
- final refit population: all 5,037 eligible training windows;
- longer convergence budget and seed policy declared before training.

Use a two-step protocol so “early stopping” and “use all training windows” are not confused:

1. **Convergence selection:** retain an engine-disjoint development/monitor split inside the training partition, use a longer registered maximum epoch budget, and select a deterministic epoch rule from monitor behavior.
2. **Locked refit:** freeze that epoch rule, then refit the same architecture on all 5,037 eligible training windows without consulting validation loss. If several seeds are registered, report all of them or use a predeclared aggregation/ensemble rule; never choose the seed with the best validation score after the fact.

**Required training controls**

- fixed seeds;
- early stopping and best-checkpoint saving during convergence selection;
- a fixed epoch count during the all-training-window locked refit;
- gradient clipping;
- deterministic loader policy;
- learning curves;
- exact package/hardware provenance;
- checkpoint and score hashes.

**Acceptance**

- checkpoint reload reproduces scores;
- the run is compared fairly with classical controls;
- the final configuration is chosen before Phase 5 threshold tuning;
- the LSTM is retained only if its accuracy, temporal behavior, explanation value, or operational trade-off justifies it.

## M6 — Score calibration

**Deliverables**

- explicit score direction;
- empirical CDF or another registered calibration fitted on training scores;
- calibration artifact and tests.

**Acceptance**

- validation/test distributions never refit the calibrator;
- calibration is monotonic;
- saved calibration reproduces scores;
- raw and calibrated scores are both retained.

## M7 — Thresholds and alert events

**Deliverables**

- global/per-mode threshold functions;
- quantile and mean-plus-standard-deviation rules;
- EWMA state;
- persistence state machine;
- event extraction;
- validation-only model-selection report.

**Acceptance**

- synthetic tests cover boundary conditions, mode changes, missing cycles, and reset behavior;
- no online recalibration in the primary study;
- thresholds are frozen before test;
- cycle-, event-, and engine-level metrics reconcile.

## M8 — Sensitivity, uncertainty, and failure analysis

**Deliverables**

- onset-policy sensitivity;
- healthy-fraction sensitivity;
- engine bootstrap confidence intervals;
- per-mode and per-engine failure tables;
- selected qualitative trajectories.

**Acceptance**

- conclusions are labeled stable, conditional, or unstable;
- overlapping windows are not bootstrapped as independent units;
- negative or contradictory cases remain visible.

## M9 — Final evaluation

**Deliverables**

- frozen pipeline manifest;
- one internal-test scoring run;
- complete metric and uncertainty report;
- claim-ledger update;
- immutable paper tables/figures.

**Acceptance**

- code/config/artifact hashes are recorded;
- no post-test retuning is hidden;
- any necessary post-test correction creates a new explicitly disclosed protocol version;
- results are reproducible from a clean environment.

## M10 — Explanation and API

**Deliverables**

- native per-sensor reconstruction contributions for reconstruction models;
- optional fidelity-tested SHAP surrogate;
- optional API using one frozen bundle.

**Acceptance**

- contributions reconcile with the detector score;
- response schema distinguishes score, threshold, alert, mode, and explanation;
- online output reproduces offline output;
- prototype code is never described as production-ready.

---

# 9. Metrics and Reporting

## 9.1 Ranking metrics

- PR-AUC: primary ranking metric under imbalanced late-life proxies;
- ROC-AUC: secondary ranking metric;
- score distributions by split, mode, engine, and proxy;
- per-engine ranking summaries where meaningful.

Ranking metrics do not define an operating threshold.

## 9.2 Point/cycle metrics at a frozen threshold

- precision;
- recall;
- F1;
- specificity;
- false-positive cycles per 1,000 declared healthy cycles.

## 9.3 Operational/event metrics

- false-alert events per 1,000 healthy cycles;
- percentage of engines with any false alert in the healthy region;
- percentage of engines detected after proxy onset;
- missed-engine rate;
- first-alert delay after proxy onset;
- lead cycles before end of observed life;
- alert duration and fragmentation;
- delay introduced by smoothing/persistence.

## 9.4 Uncertainty

Use engine-level bootstrap intervals and matched per-engine contrasts. If compute allows, add repeated engine-disjoint splits as a secondary robustness study. Do not bootstrap individual overlapping windows as independent observations.

## 9.5 Report labeling

Every result table must state:

- `Validation proxy result` or `Final internal-test result`;
- manifest ID;
- pipeline and detector;
- policy ID;
- threshold selection rule;
- aggregation level;
- seed/repetition count;
- uncertainty method.

---

# 10. Roadmap and Decision Gates

## Gate 0 — Repository safety and provenance

**Decision:** approve the refactor inventory and environment/provenance plan.
**Status:** pending.
**No deletion, branch rewrite, or evidence migration before approval.**

## Gate 1 — Split protocol

**Decision:** 60/20/20 engine-disjoint `fd002-primary-v1`.
**Status:** complete.

## Gate 2 — Preprocessing

**Decision:** P1 K=6 is the condition-aware treatment; P0 is the global control.
**Status:** complete.

## Gate 3 — LSTM candidate

**Recommendation:** `balanced_64x16_l1 + P1/K=6`.
**Status:** pending formal owner approval.

Required owner statement:

> I approve the balanced 64×16 one-layer LSTM under P1/K=6 for the registered final-refit protocol. I understand that the architecture margin was small and the LSTM has not beaten LOF/OCSVM on validation.

After approval:

1. register the final-refit configuration;
2. run a longer convergence-selection study using the engine-disjoint development/monitor split;
3. freeze the epoch and seed rule before using validation scores for downstream alert selection;
4. refit on all 5,037 eligible training windows for the frozen epoch count;
5. verify checkpoint hashes and validation scores;
6. close the detector freeze before Phase 5.

## Gate 4 — Alert-policy freeze

Select on validation only:

- detector(s);
- calibration;
- threshold type and parameters;
- global or per-mode context;
- EWMA state and alpha;
- persistence `m`;
- operational selection objective.

Status: pending.

## Gate 5 — Sensitivity closure

Complete healthy-fraction, onset-policy, uncertainty, and failure-case analyses. Decide which conclusions are stable enough for the claims ledger.

Status: pending.

## Gate 6 — Final internal test

Open internal-test scores exactly once after Gates 3–5 and code/config freeze. Produce immutable final reports.

Status: pending.

## Gate 7 — External evaluation and paper

Specify the official NASA test or N-CMAPSS protocol separately. Submit only after all paper claims are supported and every author can explain the pipeline.

Status: pending.

## Immediate ordered work

1. complete the safe repository refactor audit without changing evidence;
2. create claims ledger, environment lock, and path/ledger migration plan;
3. enrich window metadata and tests;
4. formally close Gate 3;
5. register and run the final LSTM refit;
6. freeze candidate detectors;
7. implement Phase 5 alert-policy evaluation;
8. run sensitivity and engine-bootstrap analysis;
9. freeze all choices;
10. evaluate internal test once;
11. build the final comparison table and presentation from frozen artifacts.

---

# 11. Refactor and Evidence-Preservation Rules

## 11.1 Legacy does not mean useless

Legacy means “not part of the current validated execution path.” A legacy artifact may still be useful as:

- historical evidence;
- a regression fixture;
- a prototype reference;
- a migration source;
- a documented negative result.

## 11.2 Candidate legacy paths

The following require dependency analysis before any action:

- `scripts/fit_domain_adapter_and_save.py`;
- `scripts/transform_and_save_processed.py`;
- `scripts/create_sequences_save.py`;
- `scripts/run_eda.py`;
- `scripts/run_baselines.py`;
- `scripts/train_lstm_smoke.py`;
- `scripts/export_lstm_scores.py`;
- `scripts/fit_adaptive_threshold.py`;
- `src/data/domain_adapter.py`;
- `src/models/baselines.py`;
- `src/thresholding/adaptive_threshold.py`;
- legacy API code;
- `reports/baselines/`, `reports/lstm_ae/`, and historical EDA outputs.

Each path must be classified as:

- `retain_current`;
- `migrate`;
- `archive`;
- `delete_candidate`;
- `generated_cache`.

Deletion requires an owner-approved manifest that records dependencies, replacement, evidence value, and recoverability.

## 11.3 Experiment ledger migration

Do not silently repair old rows. Preserve the historical file byte-for-byte or record its hash before migration.

Preferred approach:

1. retain `experiments/experiments.csv` as historical evidence;
2. create a schema-versioned `experiments/experiments_v2.csv` or Parquet ledger;
3. migrate parseable fields through a reviewed mapping;
4. store original row text or original-row hash;
5. use strict CSV/JSON serialization for all new entries;
6. test round-trip parsing.

## 11.4 Portable paths and hashes

- store repository-relative POSIX paths using `Path.as_posix()`;
- never serialize platform-specific backslashes as canonical paths;
- add a documented `.gitattributes` line-ending policy;
- define whether hashes cover raw bytes or canonicalized text;
- never rewrite a hashed artifact without changing its version and recording why.

---

# 12. EDA Notebook Specification

Create `notebooks/01_fd002_eda.ipynb` as a reproducible teaching and diagnostic notebook, not as a parallel data pipeline.

## Required properties

- imports reusable functions from `src/turbofan_anomaly`;
- configuration-driven paths;
- fixed seed;
- no hidden state or manual cell-order dependency;
- executable from a clean kernel;
- training and validation descriptive analysis only;
- no held-out internal-test scoring or model selection;
- outputs saved to a versioned report directory;
- notebook output policy declared before commit.

## Required sections

1. objective, evidence boundary, and dataset source;
2. FD002 schema and column meanings;
3. row/engine/cycle counts;
4. engine lifespan distribution;
5. missing, non-finite, constant, and near-constant sensors;
6. operating-setting distributions;
7. K=4/6/8 occupancy, centroids, silhouette, and stability summary;
8. train-versus-validation operating-condition coverage;
9. sensor distributions globally and by regime;
10. sensor correlations with warnings against causal interpretation;
11. representative normalized-life degradation trajectories;
12. P0-versus-P1 visual comparison;
13. window-count and tensor-shape checks;
14. engine-disjoint leakage checks;
15. limitations and observations that become decision-log candidates.

The notebook must not fit alternative models merely for visual interest.

---

# 13. Project Understanding Guide Specification

Create one detailed `docs/guides/PROJECT_UNDERSTANDING_GUIDE.md` that replaces scattered overlapping explanations. It must be written for a learner who needs intermediate technical ownership.

Required chapters:

1. project problem in plain language;
2. what FD002 contains and does not contain;
3. complete execution flow;
4. file and folder map with current, generated, and legacy labels;
5. row, window, feature, and tensor shapes;
6. P0, P1, K-Means, silhouette, ARI, and scaler fit/transform;
7. healthy-training assumptions and evaluation proxies;
8. PCA, IF, LOF, OCSVM, and LSTM-AE intuition and mathematics;
9. reconstruction score and empirical CDF calibration;
10. PR-AUC, ROC-AUC, precision, recall, F1, false-alert events, and delay;
11. threshold, EWMA, persistence, and state transitions;
12. configs, models, scores, reports, hashes, and experiment ledger;
13. exact commands for a clean smoke/test/current experiment path;
14. verified current results and their evidence classes;
15. known limitations and prohibited claims;
16. data leakage checklist;
17. debugging and troubleshooting guide;
18. glossary of project terms;
19. likely viva/review questions with concise answers;
20. small exercises that require the student to trace or change code safely.

For each important module, use:

> purpose → inputs → outputs → shapes → code flow → mathematics → fitting boundary → failure modes → tests → review explanation

---

# 14. Reproducibility Contract

Every experiment-producing run must record:

- run ID and UTC timestamp;
- owner;
- Git commit and branch;
- dirty/clean working-tree state;
- Python, NumPy, Pandas, scikit-learn, PyTorch, and CUDA versions;
- OS, CPU/GPU, device name, and deterministic-mode flags;
- seeds for Python, NumPy, PyTorch, split logic, and estimators;
- raw-data hash;
- split-manifest ID/hash;
- input-array/metadata hashes;
- complete config path/hash;
- sample and engine counts;
- fit/monitor/validation population identities;
- output paths and hashes;
- metric definitions;
- evidence class;
- warnings/failures;
- decision-log reference.

Recommended execution sequence:

> register config → verify inputs → run → write versioned artifacts → hash outputs → verify reload/reproduction → append ledger → update decision/progress → run tests → atomic commit → human-approved push

---

# 15. AI-Assisted Development and Learning Rules

Codex may accelerate implementation, but it must not silently own research decisions.

For every meaningful change:

1. explain the problem and current behavior;
2. identify the smallest coherent change;
3. state inputs, outputs, shapes, and fitting boundary;
4. state leakage and provenance risks;
5. request approval at a declared decision gate;
6. implement with tests;
7. interpret the result without overclaiming;
8. give the student one code-reading or modification exercise.

The team must be able to answer:

- Why does this module exist?
- What data is fitted, transformed, or scored?
- What shape enters and leaves it?
- Which equation or intuition explains it?
- What would leakage look like here?
- Which test proves the contract?
- What does the latest number prove and not prove?

Large opaque rewrites are disallowed. Structural refactors must use migration maps and staged verification.

---

# 16. Safe Current Claims

The following status statement is supported at commit `3aa9f0f`:

> We have completed a deterministic engine-disjoint FD002 foundation, selected a six-regime condition-aware preprocessing treatment, evaluated four classical detector families under global and condition-aware preprocessing, and completed a registered nine-run LSTM architecture screen. Condition-aware preprocessing improved all matched classical parameter pairs and was stable across matched LSTM seeds on validation proxy policies. The best current validation controls are LOF and One-Class SVM; the balanced one-layer LSTM is recommended for a controlled final refit but is not yet superior. Threshold/event evaluation, onset sensitivity, and the untouched internal test remain pending.

Do not shorten this into “our model achieved 85% accuracy.” That statement changes both the metric and evidence class and is false.

---

# 17. Paper Plan

## Working title

**Leakage-Controlled Evaluation of Operating-Condition-Aware Anomaly Detection on C-MAPSS FD002**

## Planned structure

1. motivation and research question;
2. related work and novelty boundary;
3. FD002 data, split, assumptions, and proxy labels;
4. P0/P1 preprocessing and detector methods;
5. alert-policy and sensitivity protocol;
6. validation and frozen test methodology;
7. results and matched ablations;
8. engine-level uncertainty and failure cases;
9. limitations and external validity;
10. reproducibility statement and conclusion.

## Submission gate

- [ ] every strong related-work claim has full-text support;
- [ ] all literature metrics are marked comparable or contextual;
- [ ] engine-disjoint split proof is included;
- [ ] Gate 3 final refit is complete;
- [ ] alert-policy selection is frozen on validation;
- [ ] healthy-fraction and onset sensitivity are complete;
- [ ] internal-test evaluation was run once after freeze;
- [ ] uncertainty is engine-level;
- [ ] no point-adjusted headline result is used;
- [ ] claims ledger supports every abstract/conclusion statement;
- [ ] code, configs, artifacts, tables, and figures share provenance;
- [ ] all authors can explain the experiment and its limitations.

---

# 18. Glossary for the Team

| Term | Plain-language meaning |
|---|---|
| Engine-disjoint split | An engine and all its cycles/windows occur in only one partition |
| Leakage | Information from validation/test influences fitting or selection when it should not |
| P0 | One global sensor normalization control |
| P1 K=6 | Six learned operating regimes with mode-specific sensor normalization |
| K-Means | Groups operating-setting vectors by Euclidean distance to learned centroids |
| Silhouette | Measures whether points are closer to their own cluster than other clusters |
| ARI | Measures agreement between cluster assignments across repeated fits |
| Window | Thirty consecutive cycles from one engine, with 21 sensors per cycle |
| Healthy eligibility | Early-life assumption controlling which training windows may fit one-class models |
| Onset proxy | Declared evaluation rule standing in for unknown physical fault onset |
| PR-AUC | Ranking quality emphasizing precision/recall under class imbalance |
| ROC-AUC | Ranking probability across positive/negative pairs; can look optimistic under imbalance |
| Calibration | Monotonic mapping that puts detector scores on a common reference scale |
| EWMA | Smoothed score combining the current and prior state |
| Persistence | Require several consecutive violations before declaring an alert |
| False-alert event | A contiguous alert episode in a region declared healthy by the policy |
| Decision gate | A point where the human owner approves a consequential research choice |
| Ablation | Controlled comparison changing one component while holding others fixed |
| Validation result | Used to choose the system; not final unbiased performance |
| Held-out test | Engines untouched until the complete pipeline is frozen |
| Provenance | Evidence linking a result to data, code, config, environment, and artifacts |

---

# 19. Final Instruction

The next engineering action is **not** another model search and **not** a presentation. It is a staged, evidence-preserving repository refactor audit followed by Gate 3 closure, a registered final LSTM refit, and Phase 5 alert-policy evaluation. Presentation material must be generated only after the intended repository commit and report artifacts are frozen.
