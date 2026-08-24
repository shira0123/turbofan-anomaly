# Project Understanding Guide

This guide is the practical bridge between the research protocol and the Python code. It is written for a contributor who knows basic Python and needs to become able to trace, test, explain, and safely extend the project.

The governing research document is the [Master Execution Bible v3](../research/MASTER_EXECUTION_BIBLE_V3_RESEARCH_IMPLEMENTATION_2026-08-23.md). Executable code, tests, frozen configs, stored hashes, and reproducible artifacts outrank this guide if they disagree. A description never upgrades missing work into a result.

## 1. The problem in plain language

Each FD002 engine has a time-ordered stream of 21 sensor readings. Those readings can change because:

1. the engine is operating under a different legitimate condition;
2. the engine is degrading;
3. measurement and modeling noise are present.

A detector can therefore make a basic mistake: call a normal operating-condition change a fault. The project asks whether removing more of that operating-context effect before anomaly scoring improves ranking and later alert behavior on engines that were not used for fitting.

A useful mental model is

\[
x_{t,j}=g_j(\text{operating condition}_t)+d_j(\text{degradation}_t)+\epsilon_{t,j},
\]

where sensor \(j\) at cycle \(t\) combines an operating-condition component, a possible degradation component, and noise. P0 and P1 make different choices about estimating the first component.

The defensible contribution is a leakage-controlled comparison of preprocessing, detectors, and eventually alert policies. It is not a claim that K-Means, per-regime scaling, PCA, LOF, OCSVM, Isolation Forest, or an LSTM autoencoder is a new algorithm.

## 2. What FD002 contains—and what it does not

### 2.1 Row schema

The run-to-failure FD002 training file has one row per engine cycle and 26 columns:

| Columns | Count | Meaning |
|---|---:|---|
| `engine` | 1 | engine trajectory identifier |
| `cycle` | 1 | chronological cycle within that engine |
| `op1`, `op2`, `op3` | 3 | operating settings |
| `sensor_1` … `sensor_21` | 21 | sensor measurements |

An engine contributes many rows. A row is not an independent engine, and overlapping windows are not independent engines either.

### 2.2 Frozen primary split

The registered manifest is `configs/splits/fd002-primary-v1.json`.

| Partition | Engines | Rows | Length-30 windows | Allowed role now |
|---|---:|---:|---:|---|
| Training | 156 | 32,107 | 27,583 | fit learned state; create monitor split for LSTM convergence |
| Validation | 52 | 10,873 | 9,365 | select preprocessing, candidates, and later alert policy |
| Held-out internal test | 52 | 10,779 | 9,271 | frozen; do not open before all gates close |

The split is deterministic 60/20/20 by whole engine, uses seed 42, and balances maximum-cycle quintiles. Engine overlap is zero. The internal-test counts above are registered authority facts; this refactor did not inspect the held-out contents to obtain them.

### 2.3 What FD002 does not provide

FD002 does **not** provide:

- a physical per-cycle fault-onset label;
- proof that the first 30% of observed life is physically healthy;
- a production alert threshold;
- real-aircraft operating validation;
- a basis for calling a validation PR-AUC “accuracy.”

The late-life boundaries in this project are declared **evaluation proxies**. They let us compare rankings under stated assumptions; they are not ground truth about when a physical fault began.

The official NASA test set is a different, truncated-trajectory external protocol. It must not be silently substituted for the current held-out internal split.

## 3. Evidence language: what a number is allowed to mean

Use these classes when reading or reporting a result:

| Evidence class | Meaning here |
|---|---|
| Target | desired future value; planning only |
| Smoke result | small engineering execution check |
| Historical diagnostic | old or protocol-incompatible output |
| Development result | current training-side diagnostic |
| Validation result | engine-disjoint validation evidence used for selection |
| Sensitivity result | alternate declared assumption on validation/test |
| Final internal-test result | one frozen run after the complete pipeline is locked |
| External result | separately specified NASA test or another dataset |

Before repeating a number, identify its engines, proxy policy, metric definition, aggregation, config, artifact, seed, and evidence class. The [claims ledger](../research/CLAIMS_LEDGER.md) records what may be said publicly.

The literature matrix is an evidence register, not proof that all literature has been exhausted. Abstract-only records can support discovery and broad background, but precise novelty, method, or numerical-comparison claims need the relevant full text. Literature numbers are direct comparisons only when dataset, population, proxy, metric, threshold, aggregation, point-adjustment, and repetition semantics match.

## 4. Complete active and planned flow

### 4.1 Current validated path

```text
FD002 run-to-failure source
    |
    v
strict schema checks + SHA-256
    |
    v
frozen engine manifest (156 train / 52 validation / 52 internal test)
    |
    +--> training rows ------------------------------+
    |                                                |
    +--> validation rows ----------------------------|---- no fitting
                                                     |
                         +---------------------------+
                         v
              P0 global or P1/K=6 preprocessing
                         |
                         v
          engine-local metadata + [N, 30, 21] windows
                         |
             +-----------+------------------+
             |                              |
             v                              v
      [N, 63] summary features       LSTM sequence reconstruction
             |                              |
       PCA / IF / LOF / OCSVM          raw MSE score
             |                              |
             +-------------+----------------+
                           v
          larger-is-more-anomalous raw score
                           |
                           v
      training-fitted empirical-CDF calibrated score
                           |
                           v
      declared validation proxy labels and ranking metrics
                           |
                           v
       registered configs, reports, hashes, and ledger rows
```

The current validated implementation stops after classical validation and the nine-run LSTM screen. The held-out internal test does not participate in this path.

### 4.2 Planned Phase 5 and later path

```text
frozen calibrated score in engine-cycle order
    -> optional EWMA
    -> frozen global or per-mode threshold
    -> persistence counter
    -> alert events
    -> cycle/event/engine metrics on validation
    -> onset and healthy-fraction sensitivity
    -> owner gates and complete freeze
    -> one internal-test evaluation
```

Threshold selection, EWMA, persistence, event extraction, sensitivity, and final internal-test evaluation have **not** started under the current protocol. Equations later in this guide describe the registered plan, not completed evidence.

### 4.3 Human decision gates

- Gate 1, split: complete.
- Gate 2, P1/K=6 preprocessing: complete.
- Gate 3, balanced LSTM candidate: recommended but formal approval and final refit remain pending.
- Gate 4, alert-policy freeze: pending.
- Gate 5, sensitivity closure: pending.
- Gate 6, one-time internal-test access: pending.

## 5. Active file and folder map

| Path | Status | Responsibility |
|---|---|---|
| `pyproject.toml` | current | package metadata, Python compatibility, dependencies, pytest settings |
| `.python-version` | current | records Python `3.12.8` |
| `configs/` | current, registered | protocols and selections; do not casually rewrite |
| `src/turbofan_anomaly/` | current | reusable code imported by scripts, tests, and notebook |
| `scripts/` | current | thin CLI argument parsing and workflow calls |
| `tests/` | current | synthetic/unit/safety contracts |
| `reports/preprocessing/` | current evidence | registered K-selection diagnostics |
| `reports/baselines_v2/` | current evidence | registered classical validation reports |
| `reports/lstm_v2/` | current evidence | registered LSTM screen and verification reports |
| `experiments/runs_v2.jsonl` | current evidence register | one schema-versioned JSON object per current-protocol run |
| `docs/research/` | current governance | Bible, matrix, claims, migration/artifact manifests, path/hash policy |
| `notebooks/01_fd002_eda.ipynb` | current structure, execution pending | training/validation-only descriptive EDA |
| `data/` | generated/local; absent here | raw input, materialized splits, processed tables and arrays |
| `models/` | generated/local; absent here | preprocessing, classical, and LSTM artifacts |

There is no active `legacy/` directory. Obsolete scripts, API code, adaptive-threshold prototype, fake-SHAP language, redundant guides, and obsolete reports are recoverable from Git history. Their removals and replacements are recorded in `docs/research/MIGRATION_MANIFEST.md`.

Do not infer that a file is current merely because it still exists in an older commit. The active package import root is `turbofan_anomaly`, not the former `src.data`, `src.models`, or prototype API paths.

## 6. Rows, windows, features, and shapes

### 6.1 From one engine to windows

Suppose one engine has \(L\) consecutive cycles and the window length is \(W=30\). With stride 1, its number of windows is

\[
N_e=\max(0,L-W+1).
\]

An engine with 192 cycles therefore has \(192-30+1=163\) windows. Window 1 covers cycles 1–30, window 2 covers 2–31, and so on. A window must never cross an engine boundary.

### 6.2 Main shapes

| Object | Shape | Meaning |
|---|---|---|
| raw/transformed row table | `[R, 26]` or `[R, 27]` | 26 source fields; transformed tables add `op_mode` |
| one sensor window | `[30, 21]` | 30 chronological cycles by 21 sensors |
| all sequence windows | `[N, 30, 21]` | batch-ready NumPy array |
| metadata | `[N, M]` | one traceability row per sequence window |
| classical summary features | `[N, 63]` | 21 means + 21 standard deviations + 21 end-minus-start slopes |
| raw detector score | `[N]` | one larger-is-more-anomalous score per window |
| calibrated score | `[N]` | training-reference percentile in `[0,1]` |
| LSTM batch | `[B, 30, 21]` | batch, time, sensors |
| LSTM reconstruction | `[B, 30, 21]` | same shape as input |

The metadata row order and array row order are a contract. `metadata.iloc[i]` must describe `sequences[i]`. Overlapping windows share cycles, so uncertainty must be computed at engine level—not by treating all \(N\) windows as independent samples.

### 6.3 Current metadata contract

Current metadata records include a stable `window_id`, engine, start/end/midpoint cycles, maximum cycle, end-of-life fraction, window size, split, manifest ID, source hash, operating mode placeholder, and explicit unassigned/unlabeled policy fields.

Bible v3 also calls for richer future metadata such as normalized-life start, RUL proxies, pipeline ID, healthy fraction, and explicit training eligibility. Do not claim that those fields exist until code, artifacts, and tests implement them.

## 7. Important module contracts

Every module description uses the same review pattern: purpose → inputs → outputs → shapes → code flow → mathematics → fit boundary → failure modes → tests → review explanation.

### 7.1 `turbofan_anomaly.data.io`

**Purpose.** Define the canonical 26-column FD002 schema and load either the whitespace-delimited source or an already materialized CSV without changing its role.

**Inputs.** A source/split `Path`, or a DataFrame for direct validation.

**Outputs.** A validated DataFrame whose engine/cycle identity and chronology satisfy the active workflows.

**Shapes.** The raw source and split tables are `[R,26]`; validation preserves all rows and columns.

**Code flow.** Check path → parse with the correct delimiter/schema → reject empty/null/duplicate identity rows → group by engine → assert consecutive cycles → return the frame.

**Mathematics.** No learned transformation occurs. Chronology requires consecutive within-engine differences: `diff(sorted(cycle)) == 1`.

**Fit boundary.** This module fits nothing and does not decide which split may be opened. The caller must supply only an authorized path.

**Leakage/failure modes.** Reading a CSV as the whitespace source; silently inferring the wrong schema; accepting duplicate engine/cycle rows; using the generic loader as permission to open held-out data.

**Tests.** Data/split workflow tests exercise valid parsing and rejection of missing, duplicate, empty, or non-consecutive inputs.

**How to explain it in review.** “The loader establishes the table contract; authorization remains in the workflow, so loading capability is not test-access permission.”

### 7.2 `turbofan_anomaly.data.splits`

**Purpose.** Load FD002 strictly, summarize whole engines, build the deterministic engine-disjoint manifest, hash the source, and materialize only explicitly authorized partitions.

**Inputs.** A `Path` to the FD002 run-to-failure training file; a DataFrame with canonical columns; split ratios; seed 42; five maximum-cycle strata.

**Outputs.** A validated row DataFrame, engine summary, explicit JSON-serializable manifest, and registered split CSV paths. The manifest records every engine assignment rather than depending on a future scikit-learn version to recreate it.

**Shapes.** Source `[R,26]`; engine summary `[260,3]` plus stratum/split during assignment; each materialized partition keeps 26 columns.

**Code flow.** `load_fd002` → schema/chronology checks → `summarize_engines` → rank maximum life into quintiles → two seeded stratified splits → overlap/completeness validation → deterministic JSON/hash → registered CSV materialization.

**Mathematics.** Engines—not rows—are sampled. The first split separates 60% training from 40% held out; the second divides that held-out set equally into validation and internal test. Stratification uses rank-based equal-frequency bins of engine maximum cycle.

**Fit boundary.** A split is not model fitting, but it is a high-impact data decision. Only engine-level life-length information is used for balancing. No sensor behavior, proxy label, or model score may influence assignment.

**Leakage/failure modes.** Duplicate or missing cycles; duplicated engines; row-level random splitting; wrong source hash; a ratio not summing to one; or downstream opening of the frozen partition. Split materialization is an evidence-regeneration operation, not a routine check. Never open the internal-test file to “check” it.

**Tests.** `tests/test_engine_splits.py` checks determinism, complete coverage, zero overlap, seed sensitivity, and exact row partitioning on synthetic data. Safety tests check the default output boundary.

**How to explain it in review.** “We split complete engine trajectories, stratified only by maximum life, and persisted explicit assignments. No cycle from one engine can leak into another partition.”

### 7.3 `turbofan_anomaly.data.preprocessing`

**Purpose.** Implement the controlled preprocessing contrast: P0 global sensor scaling versus P1 operating-condition-aware scaling.

**Inputs.** Training or transform DataFrames containing identifiers, three operating settings, and 21 sensors; manifest ID; healthy fraction; for P1, `K`, random seed, `n_init`, and rare-mode minimum rows.

**Outputs.** A DataFrame with unchanged engine/cycle/operating-setting fields, transformed sensor values, and `op_mode`; fitted joblib payloads with fit metadata.

**Shapes.** Input `[R,26]`; output `[R,27]`; P1 K-Means input `[R,3]`; each sensor scaler sees `[R_h,21]` or its per-mode subset.

**Code flow.** Validate schema → calculate early-life training eligibility → fit learned state on the allowed training population → transform training/validation without refitting → preserve row identity → save the object and provenance metadata.

**Mathematics.** Standard scaling is

\[
z_j=\frac{x_j-\mu_j}{\sigma_j},
\]

with \(\mu_j\) and \(\sigma_j\) learned once from the declared fit rows. P1 first standardizes operating settings, then K-Means minimizes

\[
\sum_i\left\|u_i-c_{a(i)}\right\|_2^2,
\]

where \(u_i\) is a scaled three-setting vector and \(c_{a(i)}\) its assigned centroid. It then applies the sensor scaler fitted for that regime.

**Fit boundary.** P0 sensor statistics use eligible early-life rows from training engines only. P1's operating-setting scaler and K-Means use all rows from training engines; its sensor scalers use eligible early-life training rows within each learned regime. A frozen global healthy-training sensor scaler is the rare-regime fallback. Validation is transformed only.

**Leakage/failure modes.** Calling `fit` on validation; recomputing centroids or scaling statistics per split; treating ineligible early-life-mask rows as known anomalies; missing/non-finite columns; tiny modes without declared fallback; changing row order. P1 regime numbers are cluster IDs, not causal physical labels such as “high altitude” unless separately supported.

**Tests.** `tests/test_preprocessing.py` checks training-only statistics, transform-without-refit behavior, deterministic regimes, row preservation, rare-mode fallback, and artifact provenance.

**How to explain it in review.** “P0 uses one sensor reference. P1 learns six operating contexts from training settings and uses a training-fitted sensor reference inside each context. P1 is preprocessing—not the LSTM.”

### 7.4 `turbofan_anomaly.data.metadata`

**Purpose.** Create one auditable, initially unlabeled record per chronological engine-local window.

**Inputs.** A single split DataFrame, split name, manifest ID, 64-character source SHA-256, and window size 30.

**Outputs.** A DataFrame with one stable ID and traceability record per window. At this stage `op_mode` is null and label fields are explicitly `unassigned`/`unlabeled`.

**Shapes.** For engine \(e\), `[L_e,26]` becomes `[max(0,L_e-29),M]` metadata rows. Across a split, the row count is the sum over engines.

**Code flow.** Group by engine → sort cycles → assert consecutive cycles → slide start offset by one → compute bounds/life fraction/stable ID → validate count, uniqueness, chronology, split, and unlabeled state.

**Mathematics.** The end-of-life fraction is `end_cycle / max_cycle`. A stable ID combines manifest, split, engine, and cycle range; it is not a model feature.

**Fit boundary.** This module fits nothing. It must not learn operating modes or assign anomaly proxies. Learned/contextual and evaluation fields are attached only by later, explicit stages.

**Leakage/failure modes.** A window crossing engines; non-consecutive cycles; duplicate IDs; metadata row reorder after array creation; preassigning labels; using internal-test metadata in development.

**Tests.** `tests/test_window_metadata.py` checks exact counts and bounds, engine isolation, identity fields, unlabeled defaults, and invalid chronology.

**How to explain it in review.** “Metadata is the audit trail for each array row. It preserves which engine and cycles produced a window before any proxy label is applied.”

### 7.5 `turbofan_anomaly.data.windows`

**Purpose.** Build sensor tensors aligned with metadata and derive fixed classical features.

**Inputs.** A transformed DataFrame, matching metadata, ordered 21-sensor list, and `float32` dtype.

**Outputs.** Sequence array `[N,30,21]`; summary feature matrix `[N,63]`.

**Shapes.** For every window \(X_i\in\mathbb{R}^{30\times21}\). Summary features concatenate three 21-vectors.

**Code flow.** Validate columns and metadata → group source by engine → map each metadata cycle range to row offsets → copy exactly 30 sensor rows → assert finiteness. For classical features, reduce over time to mean, standard deviation, and end-minus-start slope.

**Mathematics.** For sensor \(j\) in window \(i\):

\[
\bar{x}_{ij}=\frac{1}{30}\sum_t x_{itj},\qquad
s_{ij}=\sqrt{\frac{1}{30}\sum_t(x_{itj}-\bar{x}_{ij})^2},\qquad
\Delta x_{ij}=x_{i,30,j}-x_{i,1,j}.
\]

**Fit boundary.** Window construction and summary reduction fit no learned state. Their inputs must already have been transformed using training-fitted preprocessing.

**Leakage/failure modes.** Metadata/source misalignment; wrong sensor order; missing cycles; non-finite values; allowing one engine's last cycles to join another's first cycles; treating overlapping windows as independent bootstrap units.

**Tests.** `tests/test_window_arrays.py` checks exact values, shape, metadata order, engine boundaries, finite values, and 63-feature construction.

**How to explain it in review.** “The same `[30,21]` window feeds the LSTM directly; classical controls receive a fixed `[63]` summary of its levels, variation, and simple trend.”

### 7.6 `turbofan_anomaly.evaluation.proxies`

**Purpose.** Keep the healthy-fitting assumption separate from late-life evaluation labels and make every proxy policy explicit.

**Inputs.** Window metadata and either a healthy fraction or a normalized-life onset policy with endpoint/full-window semantics.

**Outputs.** A boolean training-eligibility mask or a policy DataFrame with onset cycle, `healthy`/`ambiguous`/`anomalous` state, and nullable 0/1 proxy label.

**Shapes.** Metadata `[N,M]` maps to mask `[N]` or label table `[N,P]` without changing order.

**Code flow.** Validate required metadata → compute engine-specific boundary → apply declared window semantics → preserve ambiguous windows as null labels → record policy ID and whether it participates in selection.

**Mathematics.** For final fraction \(q\), the onset cycle is

\[
o=\lfloor L(1-q)\rfloor+1.
\]

Endpoint semantics label a window anomalous when its end cycle is at or after \(o\). Full-window semantics label it anomalous only when its start is at or after \(o\); a window crossing \(o\) is ambiguous and excluded from that metric.

**Fit boundary.** The early-life eligibility mask controls fitting only on training engines. Proxy labels evaluate scores only and must never fit preprocessing, detectors, calibrators, or thresholds.

**Leakage/failure modes.** Calling every non-eligible training window anomalous; using validation proxy labels as model inputs; silently converting ambiguous labels; changing the proxy after seeing a favored result.

**Tests.** `tests/test_proxy_policies.py` checks endpoint labels, full-window ambiguity, and strict separation of fitting eligibility from evaluation labels.

**How to explain it in review.** “The first-30% rule says which training windows a one-class model may learn from. The final-10/20/30% rules are separate, uncertain yardsticks used only to evaluate ranking.”

### 7.7 `turbofan_anomaly.evaluation.ranking`

**Purpose.** Compute PR-AUC and ROC-AUC for explicitly declared proxy-policy frames while excluding ambiguous windows and enforcing the registered number of selection policies.

**Inputs.** Calibrated score vector `[N]`, policy DataFrames aligned to it, and the expected selection-policy count (three in the primary study).

**Outputs.** One metric/count record per policy plus the mean PR-AUC and mean ROC-AUC over selection policies.

**Shapes.** Each policy frame and score vector must have length `N`; aggregate outputs are scalar means and a short list of policy rows.

**Code flow.** Validate length → exclude null proxy labels → require both classes → compute metrics → record healthy/ambiguous/anomalous counts → average exactly the registered selection policies.

**Mathematics.** PR-AUC integrates precision against recall as threshold varies; ROC-AUC integrates true-positive against false-positive rate. The module uses scikit-learn's registered definitions.

**Fit boundary.** Metrics fit no model, but validation metrics may select candidates. They must not be used for gradient updates, CDF fitting, or hidden post-test tuning.

**Leakage/failure modes.** Misaligned score/label rows; coercing ambiguous labels; silently dropping a selection policy; averaging alternate sensitivities into the primary result; calling the aggregate accuracy.

**Tests.** Proxy-policy and classical tests cover the upstream label/score contracts, but there is not yet a dedicated synthetic unit test for `proxy_ranking_metrics`. Alignment, ambiguity exclusion, required-policy enforcement, and known metric values remain a focused coverage gap.

**How to explain it in review.** “The evaluator applies the same declared proxy set to aligned scores and averages only the three registered endpoint policies.”

### 7.8 `turbofan_anomaly.alerting.calibration`

**Purpose.** Share one training-reference empirical-CDF score calibration contract across classical and LSTM detectors.

**Inputs.** A finite non-empty training score vector for `fit`, then any finite raw score vector for `transform`.

**Outputs.** Frozen sorted training scores and calibrated percentiles `[N]` in `[0,1]`.

**Shapes.** Fit reference `[N_h]`; transformed output has the same one-dimensional length as its input.

**Code flow.** Flatten/validate → sort the training reference → use right-sided binary-search ranks → divide by reference count.

**Mathematics.** It implements `c(s) = count(s_i <= s) / n`; the map is monotonic and preserves detector ranking apart from ties.

**Fit boundary.** Fit on declared eligible training scores only. Validation and test call `transform` and never redefine the reference.

**Leakage/failure modes.** Fitting on validation/test; interpreting a percentile as fault probability; using different references when comparing models; accepting NaN/Inf or an empty reference.

**Tests.** Calibration/classical tests check exact tied ranks, monotonicity, bounded values, pre-fit rejection, and non-finite input rejection.

**How to explain it in review.** “Calibration puts different raw score scales on a common training-percentile axis; it does not learn from proxy labels or estimate failure probability.”

### 7.9 `turbofan_anomaly.models.classical`

**Purpose.** Provide strong, consistently scored PCA, Isolation Forest, LOF, and One-Class SVM controls plus training-fitted empirical-CDF calibration.

**Inputs.** Eligible training feature matrix `[N_h,63]`, registered detector parameters, and any scoring feature matrix `[N,63]`.

**Outputs.** A fitted feature scaler/detector/calibrator artifact; raw and calibrated score vectors `[N]`, always oriented so larger means more anomalous.

**Shapes.** Feature scaler `[N_h,63]`; PCA latent dimension is variance-selected; every detector produces one scalar per window.

**Code flow.** Validate finite features → fit feature `StandardScaler` → fit registered detector → convert native output to larger-is-more-anomalous → fit empirical CDF on training scores → transform validation scores without refitting → save model plus manifest/preprocessing identity.

**Mathematics and intuition.**

- **PCA:** learn a low-dimensional linear subspace of early-life features. Score reconstruction error

  \[
  e_i=\frac{1}{D}\lVert u_i-\hat{u}_i\rVert_2^2.
  \]

- **Isolation Forest (IF):** random splits isolate unusual points in fewer tree steps. The wrapper negates scikit-learn's normality-oriented `score_samples` so larger means more anomalous.
- **LOF:** compare a point's local reachability density with its neighbors' densities. A simplified view is

  \[
  \operatorname{LOF}_k(x)=\frac{1}{|N_k(x)|}\sum_{y\in N_k(x)}
  \frac{\operatorname{lrd}_k(y)}{\operatorname{lrd}_k(x)}.
  \]

  Values above one indicate lower density than neighbors. The implementation uses novelty mode so it can score unseen validation rows.
- **One-Class SVM (OCSVM):** learn a kernel boundary around early-life features,

  \[
  f(x)=\sum_i\alpha_iK(x_i,x)-\rho,
  \]

  and use `-f(x)` as anomaly score.

**Fit boundary.** Feature scaling, detector state, and empirical CDF are fitted only on eligible training windows. Candidate selection uses validation proxy metrics, so selected numbers are validation results—not final estimates.

**Leakage/failure modes.** Fitting the feature scaler or CDF on validation; using LOF without novelty mode; forgetting score direction; fitting on fewer than required windows; comparing candidates under different features/proxies; tuning after seeing internal-test results.

**Tests.** `tests/test_classical_baselines.py` checks the monotonic training-fitted CDF, all four unseen-row score contracts, bounded calibrated output, provenance enforcement, and the small registered grid.

**How to explain it in review.** “These are first-class controls, not disposable baselines. They share the same split, P0/P1 treatment, early-life fit population, proxy policies, and score direction.”

### 7.10 `turbofan_anomaly.models.lstm_autoencoder`

**Purpose.** Reconstruct a 30-cycle sensor window through a compressed temporal representation.

**Inputs.** PyTorch tensor `[B,30,21]` and registered architecture dimensions.

**Outputs.** Reconstruction tensor `[B,30,21]` with the same time and sensor order.

**Shapes.** The recommended screened architecture uses 21 inputs, 64 hidden units, 16 latent dimensions, one LSTM layer, and zero effective inter-layer dropout because it has one layer.

**Code flow.** Encoder LSTM reads the sequence → last hidden state maps to latent vector → latent vector maps to a repeated decoder seed → decoder LSTM generates a time sequence → linear head returns 21 reconstructed sensors per time step.

**Mathematics.** Abstractly,

\[
h=\operatorname{Encoder}(X),\qquad z=W_zh+b_z,\qquad
\hat X=\operatorname{Decoder}(W_dz+b_d).
\]

The anomaly score for one window is

\[
e=\frac{1}{30\times21}\sum_{t=1}^{30}\sum_{j=1}^{21}(x_{t,j}-\hat{x}_{t,j})^2.
\]

The modeling assumption is that early-life patterns reconstruct better than unusual/degrading patterns. That is an assumption tested by ranking—not a guarantee.

**Fit boundary.** The model sees eligible training windows during optimization and a separate set of eligible training-engine windows for convergence monitoring. Validation scores select the screened candidate. Validation windows never update weights.

**Leakage/failure modes.** Wrong sensor dimension/order; random window-level monitor split that shares engines; using validation loss for gradient updates; choosing the best random seed after validation; treating a small architecture margin as scientific superiority; nondeterministic hardware behavior without provenance.

**Tests.** `tests/test_lstm_validation.py` includes shape rejection and end-to-end tiny synthetic training/reload scoring.

**How to explain it in review.** “The LSTM compresses and reconstructs temporal windows. Its MSE is an anomaly ranking score. It is a benchmark component, and the current screen does not beat LOF or OCSVM.”

### 7.11 `turbofan_anomaly.models.lstm_training`

**Purpose.** Make engine-disjoint convergence monitoring, deterministic training, reconstruction scoring, and checkpoint provenance reusable.

**Inputs.** Training metadata/eligibility, development and monitor tensors, architecture dataclass, training settings, seed, and CPU/CUDA device.

**Outputs.** Engine-disjoint masks, fit history, best epoch/loss, fitted model, reconstruction scores `[N]`, and checkpoint containing state, architecture, sorted training-score reference, and metadata.

**Shapes.** Screen fit populations were 3,988 eligible windows from 124 development engines and 1,049 from 32 monitor engines. Validation used 9,365 windows from 52 unseen engines.

**Code flow.** Stratify eligible training engines → seed Python/NumPy/PyTorch → deterministic loaders → AdamW optimization with MSE and gradient clipping → monitor early stopping → restore best state → score without gradients → save/reload with identity checks.

**Mathematics.** Training minimizes mean reconstruction error. Early stopping retains the epoch with monitor loss improvement greater than `min_delta`; patience stops after a registered number of unimproved epochs. Gradient norm clipping caps unstable updates.

**Fit boundary.** Development and monitor engines are disjoint subsets of the training partition. Monitor affects epoch choice but not gradient fitting. Validation affects registered screen selection only. The future final refit must first freeze an epoch/seed rule, then train on all 5,037 eligible training windows without consulting validation loss.

**Leakage/failure modes.** Window-level development/monitor split; non-covered eligible windows; selecting seed by best validation score; checkpoint/config mismatch; loading a different preprocessing decision; silently switching PyTorch/CUDA builds; requesting CUDA when unavailable.

**Tests.** `tests/test_lstm_validation.py` checks deterministic complete engine-disjoint masks, tiny CPU training/scoring, artifact reload equality, provenance enforcement, and dimension validation.

**How to explain it in review.** “Monitoring is inside the training partition and split by engine. Validation chooses among registered screens; it never performs weight updates. The all-training-window final refit is still pending.”

### 7.12 `turbofan_anomaly.evaluation.provenance`

**Purpose.** Resolve portable repository-relative artifact paths and verify registered SHA-256 values without rewriting evidence.

**Inputs.** Serialized path text, repository root, artifact `Path`, and expected 64-character digest.

**Outputs.** Canonical POSIX path text, root-confined resolved paths, exact-byte hashes, or a verification record stating whether raw/LF/CRLF bytes matched.

**Shapes.** This module handles bytes and scalar path/hash values, not model arrays.

**Code flow.** Normalize separators in memory → reject absolute/drive/parent-traversal paths → resolve under root → stream bytes into SHA-256 → permit only documented raw or line-ending-equivalent text matches.

**Mathematics.** SHA-256 maps exact bytes to a 256-bit digest. No JSON, whitespace, encoding, Unicode, or numeric canonicalization is allowed.

**Fit boundary.** No statistical fit. The boundary is filesystem scope: resolution must stay inside the repository, and verification must not mutate the checked file.

**Leakage/failure modes.** Treating a historical backslash as a literal POSIX character; accepting `..` or an absolute path; normalizing arbitrary whitespace to force a match; rewriting a registered file after mismatch.

**Tests.** Provenance/path tests cover POSIX serialization, historical backslash compatibility, root-escape rejection, exact and LF/CRLF hash matching, and mismatch errors.

**How to explain it in review.** “We normalize paths only while resolving them and compare controlled byte representations; frozen evidence bytes remain untouched.”

### 7.13 `turbofan_anomaly.workflows.*`, thin scripts, and the ledger

**Purpose.** Scripts expose command-line arguments and call package behavior; the ledger makes current-protocol runs parseable and traceable.

**Inputs.** Registered config paths and local training/validation artifacts.

**Outputs.** Depending on the script, manifests, arrays, models, reports, or validation output. `runs_v2.jsonl` contains one valid JSON object per line with `schema_version`, source identity, evidence class, and artifact/config provenance.

**Shapes.** Scripts do not define new scientific shapes. They pass the package's row/window/feature contracts through. The ledger is line-oriented records, not a rectangular model input.

**Code flow.** Thin script parses CLI → calls its matching package workflow → workflow validates config/input identities → reusable modules perform work → workflow validates and records outputs. New paths are repository-relative POSIX paths; historical backslash paths are resolved compatibly without rewriting hashed configs.

**Mathematics.** None beyond the called module. SHA-256 hashes cover exact bytes under the documented policy.

**Fit boundary.** A wrapper must not hide fitting, selection, or internal-test access. Any command that fits or rewrites evidence inherits the relevant research gate.

**Leakage/failure modes.** Logic duplicated in a script/notebook; a wrapper default opening internal test; malformed JSONL; rewriting a registered config only to normalize slashes; recording a validation proxy as final evidence.

**Tests.** CLI help smoke checks, package unit tests, ledger round-trip/schema tests, path compatibility tests, and default safety tests.

**How to explain it in review.** “The scientific logic lives in the importable package. Scripts only orchestrate it, while the ledger binds each result to its original source and evidence class.”

## 8. Why P0 and P1/K=6 are different

### 8.1 P0 global control

P0 fits one 21-sensor scaler on early-life eligible rows from training engines. Every row—regardless of operating condition—is transformed through that one reference. `op_mode=-1` means “no regime used,” not a seventh physical mode.

### 8.2 P1/K=6 treatment

P1:

1. fits a scaler for the three operating settings on all training rows;
2. fits K-Means on those scaled settings;
3. predicts one of six regimes for each row;
4. fits a 21-sensor scaler on eligible early-life training rows within each regime;
5. uses a frozen global eligible-training scaler if a regime has too few fit rows;
6. transforms validation with that frozen training state.

Again: **P1 is preprocessing.** The same P1 arrays can feed PCA, IF, LOF, OCSVM, or the LSTM.

### 8.3 Why scale operating settings before K-Means

K-Means uses Euclidean distance. Without scaling, an operating setting with a larger numeric range can dominate distance even if it is not more scientifically important.

### 8.4 K-selection evidence

Silhouette compares average within-cluster distance \(a(i)\) with nearest-other-cluster distance \(b(i)\):

\[
s(i)=\frac{b(i)-a(i)}{\max(a(i),b(i))}.
\]

Higher is more separated. Adjusted Rand Index (ARI) measures agreement between assignments from repeated/subsampled fits after correcting expected chance agreement. ARI 1 means identical partitions; values near 0 mean chance-level agreement.

| K | Validation silhouette | Mean stability ARI | Minimum validation occupancy | Decision |
|---:|---:|---:|---:|---|
| 4 | 0.85179450 | 1.00000000 | 0.14816518 | rejected; merged distinct conditions |
| 6 | 0.99703695 | 1.00000000 | 0.14696956 | selected |
| 8 | 0.89306060 | 0.93224270 | 0.04902051 | rejected; less stable and over-split a small regime |

This validates K=6 as the current preprocessing choice on validation evidence. It does not prove six causal physical regimes.

## 9. Healthy fitting and evaluation proxies are different questions

The primary development assumption lets models fit only windows ending within the first 30% of each training engine's observed life:

\[
\text{eligible}=\mathbf{1}\left[\text{end cycle}\leq\lfloor0.30L\rfloor\right].
\]

An ineligible window is **unlabeled for fitting**, not a confirmed anomaly.

The primary selection proxy policies label validation windows by whether their endpoint falls in the final 10%, 20%, or 30% of observed life. Secondary full-window policies for the final 20% and 30% exclude onset-crossing windows as ambiguous.

Planned sensitivity also includes healthy fractions 20/30/40%, RUL-proxy values 130/150 where compatible, and secondary change-point estimates. Those sensitivity results do not exist yet.

## 10. Reconstruction error and empirical-CDF calibration

Raw scores from different detector families have different units. Every wrapper first ensures that larger means more anomalous. A training-fitted empirical CDF then maps raw score \(s\) to

\[
c(s)=\frac{1}{n}\sum_{i=1}^n\mathbf{1}(s_i\leq s).
\]

Interpretation: `0.95` means the score is at least as large as about 95% of the training reference scores. It does **not** mean a 95% probability of failure.

The CDF must be fitted once on declared training scores. Refitting it on validation or test would let those populations redefine what “high” means and would leak information.

For reconstruction models, per-sensor contribution may be reported as

\[
e_j=\frac{1}{30}\sum_{t=1}^{30}(x_{t,j}-\hat{x}_{t,j})^2.
\]

The mean/sum of contributions must reconcile with total reconstruction error within a stated numerical tolerance. A temporal-deviation heuristic is not SHAP. Use the name SHAP only if the actual SHAP algorithm is run and explanation fidelity is evaluated.

## 11. Metrics: ranking is not classification accuracy

### 11.1 Current ranking metrics

- **PR-AUC:** area under the precision-recall curve as the score threshold moves. It emphasizes performance on the proxy-positive class and is primary under imbalance.
- **ROC-AUC:** probability that a randomly chosen proxy-positive window ranks above a randomly chosen proxy-negative window. It can look optimistic under strong imbalance.

Neither chooses an operating threshold. Neither is accuracy.

### 11.2 Threshold-dependent metrics (future Phase 5)

At a frozen threshold:

\[
\text{precision}=\frac{TP}{TP+FP},\qquad
\text{recall}=\frac{TP}{TP+FN},\qquad
F1=\frac{2PR}{P+R}.
\]

The planned study will also report specificity and false-positive cycles per 1,000 declared healthy cycles. No current-protocol F1, false-alert rate, or delay result exists.

### 11.3 Operational/event metrics (future)

The operational questions are engine-oriented:

- false-alert events per 1,000 declared healthy cycles;
- engines with any healthy-region false alert;
- engines detected after proxy onset;
- missed-engine rate;
- first-alert delay after proxy onset;
- lead cycles before observed end of life;
- event duration and fragmentation;
- delay added by smoothing and persistence.

Confidence intervals must resample engines, not individual overlapping windows.

## 12. Planned threshold, EWMA, and persistence behavior

This section explains the registered plan. It is **not current verified implementation or evidence**.

A global threshold uses one boundary; a per-mode threshold uses the frozen operating regime. Candidate rules are healthy-score quantiles and \(\mu+k\sigma\), selected on validation under a predeclared objective.

EWMA smooths calibrated score \(s_t\):

\[
z_t=\alpha s_t+(1-\alpha)z_{t-1}.
\]

Persistence \(m\) requires consecutive threshold violations:

\[
c_t=
\begin{cases}
c_{t-1}+1,&z_t>\tau(\text{mode}_t),\\
0,&\text{otherwise},
\end{cases}
\qquad
\text{alert}_t=\mathbf{1}[c_t\geq m].
\]

Persistence can suppress isolated spikes but necessarily adds delay. The registered study considers `m` in `{1,3,5,8}`, a small predeclared EWMA alpha set, and online recalibration **off**. Mode changes, missing cycles, reset behavior, and event boundaries require synthetic state-machine tests before use.

## 13. Current verified results and their boundaries

### 13.1 Classical validation proxy diagnostics

Fit population: 5,037 eligible early-life windows from 156 training engines. Validation population: 9,365 windows from 52 unseen engines. Selection is mean PR-AUC across endpoint final-10%, final-20%, and final-30% proxy policies.

| Pipeline | Detector | Selected parameter | Mean PR-AUC | Mean ROC-AUC | Evidence class |
|---|---|---|---:|---:|---|
| P0 | Isolation Forest | `max_samples=5000` | 0.254595 | 0.561099 | validation proxy result |
| P0 | LOF | `n_neighbors=20` | 0.495310 | 0.772648 | validation proxy result |
| P0 | One-Class SVM | `nu=0.01`, `gamma=scale` | 0.348877 | 0.686445 | validation proxy result |
| P0 | PCA | `variance=0.99` | 0.721719 | 0.929476 | validation proxy result |
| P1/K=6 | Isolation Forest | `max_samples=256` | 0.78916934 | 0.955921 | validation proxy result |
| P1/K=6 | LOF | `n_neighbors=20` | **0.84969513** | 0.964363 | validation proxy result |
| P1/K=6 | One-Class SVM | `nu=0.10`, `gamma=scale` | **0.83280767** | 0.964371 | validation proxy result |
| P1/K=6 | PCA | `variance=0.90` | 0.77240729 | 0.925035 | validation proxy result |

All 12 matched classical parameter pairs favored P1 on mean validation PR-AUC. This supports carrying P1 forward; it is not final causal or test evidence.

### 13.2 LSTM screen

Nine runs completed: three architectures under P1 at seed 42, then the selected architecture under P0/P1 at matched seeds 43–45.

| Screen item | Verified value | Meaning |
|---|---:|---|
| `compact_32x8_l1`, stage 1 | 0.810262 mean PR-AUC | nearly tied architecture |
| `balanced_64x16_l1`, stage 1 | 0.812090 mean PR-AUC | registered recommendation |
| `stacked_64x16_l2`, stage 1 | 0.808745 mean PR-AUC | no screen benefit |
| P0 matched-seed median | 0.240047 | validation proxy screen |
| P1/K=6 matched-seed median | **0.81088283** | validation proxy screen |

The architecture margin is tiny. Do not say the balanced architecture is scientifically superior. P1 LOF and OCSVM remain stronger validation controls than the screened LSTM. The LSTM used fewer optimization windows than the classical fit, so the current cross-family difference is not a fully controlled final comparison.

At the audited checkpoint, 26 automated tests passed. Nine checkpoint hashes and all 84,285 stored validation score rows also reproduced, with maximum differences about `7.1e-15` raw and `1.2e-16` calibrated. Those are checkpoint test/artifact-reproduction facts, not a substitute for rerunning the refactored suite and not new model performance.

### 13.3 Safe status statement

The safe summary is:

> The project has a deterministic engine-disjoint FD002 foundation, a selected six-regime condition-aware preprocessing treatment, four classical detector families evaluated under P0 and P1, and a registered nine-run LSTM screen. P1 improved all matched classical parameter pairs and was stable across matched LSTM seeds on validation proxy policies. LOF and One-Class SVM are the strongest current validation controls. The balanced one-layer LSTM is recommended for a controlled final refit but is not yet superior. Threshold/event evaluation, sensitivity, and the untouched internal test remain pending.

Do not shorten this to “our model achieved 85% accuracy.” That changes the metric, evidence class, and meaning, and is false.

## 14. What remains incomplete

- formal owner closure of Gate 3;
- longer convergence selection and locked LSTM refit on all 5,037 eligible training windows;
- detector freeze before alert-policy selection;
- Phase 5 global/per-mode thresholds, EWMA, persistence, and event metrics;
- healthy-fraction and onset-policy sensitivity;
- engine-level bootstrap uncertainty and failure analysis;
- optional fusion only if complementarity justifies it;
- one frozen internal-test evaluation;
- separately specified official-test/external evaluation;
- a reproducible environment lockfile.

The raw data, processed arrays, and model checkpoint directories are absent from this checkout. In particular, notebook execution needs `data/splits/train.csv`, `data/splits/validation.csv`, `models/preprocessing/p0_global.joblib`, and `models/preprocessing/p1_k6.joblib`; they are absent. Some optional/runtime dependencies may also be absent before setup. Those facts block notebook execution, artifact reproduction, and experiment workflows. Do not fabricate substitutes or download data silently.

## 15. Configs, reports, models, hashes, and ledger

### 15.1 Registered controls

- `configs/splits/fd002-primary-v1.json`: explicit engine assignment and source identity.
- `configs/preprocessing/fd002-preprocessing-study-v1.json`: registered P0/P1 and K study.
- `configs/preprocessing/fd002-preprocessing-selection-v1.json`: selected P1/K=6 decision.
- `configs/baselines/fd002-classical-baselines-v1.json`: candidate grid, paths, fit and validation identities.
- `configs/lstm/fd002-lstm-screen-protocol-v1.json`: nine-run protocol registered before execution.
- `configs/lstm/fd002-lstm-screen-results-v1.json`: run hashes, report hashes, verification, and recommendations.
- `configs/evaluation/fd002-eda-v1.json`: training/validation-only notebook inputs, fixed seed, and descriptive evidence boundary.

A config says what should or did run. A report contains derived evidence. A model artifact contains learned state. None substitutes for the others.

### 15.2 Hash rules

SHA-256 identifies exact bytes. New serialized paths use repository-relative POSIX form, for example `reports/lstm_v2/run_summary.csv`. Some frozen historical configs contain Windows backslashes. Compatibility resolution may read them on either platform, but do not rewrite a hashed config merely to replace slashes. A changed byte requires a new version and a recorded reason.

Read `docs/research/PATH_AND_HASH_POLICY.md` and `docs/research/ARTIFACT_MANIFEST.md` before moving any registered artifact.

### 15.3 Experiment ledger

`experiments/runs_v2.jsonl` replaces the malformed mixed-protocol CSV in the active branch. Each line is an independent JSON object and includes a schema version, source run ID, original-row/source hash where available, evidence class, split/config/artifact identities, and preserved values.

The ledger does not upgrade an old row. A validation proxy diagnostic remains a validation proxy diagnostic. Validate every line by parsing it and round-tripping through the registered validator/test before accepting changes.

The focused read-only validator command is `python -m pytest tests/test_experiment_ledger.py -q`.

### 15.4 Reproducibility record for a future run

Record run ID/time/owner, branch/commit/dirty state, Python and package versions, OS/CPU/GPU/CUDA, deterministic flags, all seeds, source and manifest hashes, input array/metadata hashes, config hash, engine/window counts, population roles, output paths/hashes, metric definitions, evidence class, warnings, and decision-log reference.

## 16. Exact commands and safety boundaries

Run all commands from the repository root in PowerShell.

### 16.1 Environment setup

Python 3.12.8 is the recorded target. `pyproject.toml` is the dependency authority. There is no lockfile yet.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

This creates a usable current environment, not a byte-for-byte historical environment. Do not silently change PyTorch/CUDA to reproduce a registered run.

### 16.2 Verification-only commands

These commands do not fit models or regenerate registered research reports:

```powershell
python -c "import turbofan_anomaly; print(turbofan_anomaly.__version__)"
pytest -q
python -m pytest tests/test_experiment_ledger.py -q

python -m scripts.make_splits --help
python -m scripts.create_window_metadata --help
python -m scripts.run_preprocessing_study --help
python -m scripts.run_classical_baselines --help
python -m scripts.run_lstm_screen --help
python -m scripts.verify_lstm_screen --help

python -m json.tool notebooks/01_fd002_eda.ipynb | Out-Null
git diff --check
```

`python -m scripts.verify_lstm_screen --device cpu` is also read-only with respect to registered evidence, but it requires the absent training/validation sequence arrays and all nine model checkpoints. It verifies hashes and recomputes recorded **validation** scores; it does not need or permit held-out data.

### 16.3 Commands that create or regenerate evidence

The following are **not** routine verification. They create splits/arrays, fit learned state, train models, or rewrite registered reports. During this clean refactor they are prohibited. Run them later only after the applicable owner gate, input/hash check, clean environment record, and explicit output-version plan.

```powershell
# Regenerates the manifest and registered partition files.
# This is not a verification command; never inspect the frozen output.
python -m scripts.make_splits

# Generates training/validation metadata only by default.
python -m scripts.create_window_metadata

# Fits P0 and P1 candidates and rewrites preprocessing outputs/reports.
python -m scripts.run_preprocessing_study

# Fits four detector families and rewrites baseline models/reports.
python -m scripts.run_classical_baselines

# Trains the registered nine-run LSTM screen and rewrites its artifacts.
python -m scripts.run_lstm_screen --device auto
```

The commands are shown to make the execution path auditable, not to authorize a rerun. Do not pass an internal-test opt-in flag, do not open an internal-test file manually, and do not run the official NASA test path. Never regenerate into registered paths merely to see whether a command works.

### 16.4 Notebook status

The notebook is training/validation-only descriptive EDA and imports package functions. JSON/section structure can be verified now. Clean-kernel execution is pending because data and possibly notebook dependencies are absent. Do not fabricate outputs and do not redirect it to internal-test data.

## 17. Leakage and provenance checklist

Before any future run, answer every item:

- [ ] Are all windows from one engine in exactly one primary partition?
- [ ] Does the manifest ID/hash match every input artifact?
- [ ] Is the held-out internal test still unopened?
- [ ] Are official NASA test data excluded from this protocol?
- [ ] Were operating-setting scaler and K-Means fitted on training rows only?
- [ ] Were sensor scalers fitted only on eligible training rows?
- [ ] Was validation transformed with frozen training state, never refitted?
- [ ] Were detector feature scaler and detector fitted only on eligible training windows?
- [ ] Was the empirical CDF fitted only on declared training scores?
- [ ] Are development and monitor engines disjoint inside LSTM training?
- [ ] Were validation proxies used only for evaluation/selection?
- [ ] Are ambiguous full-window labels excluded rather than coerced?
- [ ] Does every score use the larger-is-more-anomalous direction?
- [ ] Do metadata rows and tensor rows remain exactly aligned?
- [ ] Are bootstrap/sensitivity units engines rather than overlapping windows?
- [ ] Was every candidate/config declared before examining its result?
- [ ] Are path/hash semantics unchanged for registered artifacts?
- [ ] Does the ledger state the correct evidence class?
- [ ] Is any claimed SHAP output produced by the actual SHAP algorithm with fidelity evidence?

If any answer is “no” or “unknown,” stop before interpreting a metric.

## 18. Troubleshooting

| Symptom | Likely cause | Safe response |
|---|---|---|
| `ModuleNotFoundError: turbofan_anomaly` | environment not activated or package not installed | activate `.venv`; run `python -m pip install -e ".[test]"`; retry import smoke test |
| Python version is not 3.12.8 | wrong interpreter selected | recreate/select a 3.12 environment; record any unavoidable deviation |
| raw/split/array/model file not found | large local artifacts are intentionally absent | stop the full workflow; run structural/unit checks only; do not download or fabricate data |
| hash mismatch | wrong artifact, changed bytes, line endings, or historical path resolution | stop; compare manifest/policy; never “fix” a frozen config in place |
| historical path with backslashes fails | frozen Windows path interpreted literally | use the compatibility resolver; preserve the config bytes |
| engine overlap assertion fails | wrong materialized split or row-level split | stop; do not continue fitting; trace manifest and source identity |
| window count/shape mismatch | wrong metadata, sensor order, window length, or row ordering | compare IDs/count equation; rebuild only into a new approved output path |
| non-finite transformed values | bad input/schema or invalid scaling state | inspect allowed training/validation schema only; test the preprocessor; do not substitute zeros silently |
| LOF cannot score unseen data | novelty mode disabled or too few fit windows | use the registered wrapper; add a synthetic regression test |
| CUDA requested but unavailable | local hardware/build differs | use CPU for safe tests/verification where supported; do not silently upgrade PyTorch/CUDA |
| deterministic PyTorch error | operation/build does not support deterministic mode | record the exact error/environment; do not disable determinism silently |
| ledger line fails JSON parsing | malformed or multi-line record | preserve source evidence; repair through reviewed migration and round-trip test, not manual reinterpretation |
| notebook cannot execute | missing data/kernel/dependency | leave outputs clear, report execution pending, and keep structural validation |
| metric seems much better than expected | wrong proxy, point adjustment, leakage, or aggregation | inspect policy/config/engine population before celebrating |

Changing the healthy fraction, detector grid, threshold, or seed just to make an error disappear is a research change—not troubleshooting.

## 19. Glossary

| Term | Plain-language meaning |
|---|---|
| engine-disjoint | one engine and all its rows/windows occur in one partition only |
| leakage | information influences fitting or selection outside its allowed boundary |
| P0 | one global sensor normalization control |
| P1/K=6 | six learned operating regimes with per-regime sensor normalization |
| K-Means | assigns setting vectors to nearest learned centroid |
| silhouette | within-versus-nearest-other cluster separation score |
| ARI | chance-adjusted agreement between two cluster assignments |
| window | 30 consecutive cycles from one engine, 21 sensors per cycle |
| healthy eligibility | early-life assumption controlling one-class fitting |
| onset proxy | declared evaluation rule standing in for unknown physical onset |
| ambiguity | a full window crosses a proxy boundary and is not forced to 0 or 1 |
| anomaly score | scalar ranking; larger is standardized here to mean more anomalous |
| PR-AUC | threshold-free precision/recall ranking summary under proxy labels |
| ROC-AUC | threshold-free positive-versus-negative ranking probability |
| calibration | monotonic mapping to a training-reference score scale |
| reconstruction error | mean squared difference between input and reconstruction |
| EWMA | smoothed score combining current score and previous state |
| persistence | required consecutive violations before an alert begins |
| false-alert event | contiguous alert episode in a region declared healthy by policy |
| validation result | evidence used to select the system; not final unbiased performance |
| held-out internal test | frozen engines opened once only after full pipeline freeze |
| provenance | links among data, code, config, environment, artifact, and result |
| SHA-256 | byte-level content identity hash |
| decision gate | point where the human owner approves a consequential research choice |

## 20. Likely review/viva questions and safe answers

**Why not split rows randomly?**
Rows from one engine are temporally related. Random row/window splitting would put the same degradation trajectory in fit and evaluation data. We split whole engines.

**What is the research treatment?**
P1/K=6 operating-condition-aware preprocessing compared with P0 global preprocessing, under common detector and evaluation rules.

**Is P1 the LSTM?**
No. P1 is preprocessing. PCA, IF, LOF, OCSVM, and the LSTM can all consume P1-transformed windows.

**Why K=6?**
Among registered K=4/6/8 candidates, K=6 had validation silhouette 0.99703695, mean stability ARI 1.0, and acceptable minimum validation occupancy. This is a validation preprocessing choice, not proof of six causal physical regimes.

**Why call the labels proxies?**
FD002 has run-to-failure trajectories but no physical per-cycle onset labels. Final-life fractions are explicit evaluation assumptions.

**Why can early-life eligibility and anomaly labels differ?**
Eligibility controls what a one-class model may learn from. Proxy labels judge score ranking later. Calling every non-eligible window anomalous would invent ground truth.

**Why PR-AUC? Is 0.8497 equal to 84.97% accuracy?**
No. PR-AUC summarizes precision/recall ranking across thresholds under a declared proxy. It is not classification accuracy and is not final-test evidence.

**Which current detector is best?**
On the current engine-disjoint validation proxy, P1 LOF has the highest mean PR-AUC, followed by P1 OCSVM. That is a validation control result, not final performance.

**Did the LSTM win?**
No. The recommended P1 balanced LSTM screen candidate has median matched-seed mean PR-AUC 0.81088283 and has not beaten LOF or OCSVM. Its final controlled refit is pending.

**Why keep simple models?**
Simple controls can be strong, cheaper, and easier to audit. A complex model must show a fair, useful benefit in ranking, temporal behavior, explanations, or operational trade-offs.

**How is score calibration leakage-controlled?**
The empirical CDF is fitted on declared training scores only and then frozen for validation/test transforms.

**What does persistence trade?**
It suppresses isolated violations but delays alert onset by requiring multiple consecutive exceedances. That trade-off has not yet been evaluated here.

**Why no production API?**
The research pipeline, calibration, threshold, persistence, and frozen bundle are incomplete. Prototype API code would overstate readiness and is not required for the paper.

**What is the internal-test policy?**
Do not open or score it until preprocessing, detector, calibration, alert policy, sensitivity, code, and configs are frozen and all owner gates are closed. Then evaluate once.

**Can we call sensor deviation SHAP?**
No. SHAP means the actual SHAP algorithm was used and its explanation fidelity was evaluated. Native reconstruction contributions should be named accurately.

**What would invalidate a registered report?**
A mismatched source/manifest/config/model, changed bytes without versioning, a different proxy/metric, or a fit boundary violation. Hashes and ledger records make those changes visible.

## 21. Small code-reading exercises

All exercises use synthetic data or read-only artifacts. None requires internal-test access.

1. **Trace a window.** In `tests/test_window_arrays.py`, choose one synthetic metadata row. Write down its engine, start/end cycles, tensor index, `[30,21]` shape, and the first element of its 63-feature summary.
2. **Prove engine disjointness.** Read `test_engine_splits.py` and explain why set disjointness is stronger than checking only row counts. Add a synthetic assertion for three pairwise intersections if one is missing.
3. **Separate fitting from labeling.** For an engine with maximum cycle 100, calculate the 30% fit cutoff and endpoint/full-window final-20% labels for windows 52–81 and 71–100. Confirm with `NormalizedLifeOnsetPolicy` in a Python shell.
4. **Trace a P1 transform.** On paper, identify which rows fit the operating scaler, K-Means, global fallback scaler, and one per-mode sensor scaler. Point to the test that would fail if validation changed a scaler mean.
5. **Check score direction.** Read each branch of `ClassicalAnomalyModel._raw_scores_scaled`. Explain why PCA is already larger-is-more-anomalous and why the other native scores are negated.
6. **Understand CDF ties.** Fit the calibrator to `[1,2,3]` and predict calibrated values for `[0,1,1.5,3,4]`. Compare with the unit test and explain `side="right"`.
7. **Count LSTM parameters conceptually.** Trace how `[B,30,21]` becomes the 16-dimensional latent vector and returns to `[B,30,21]`. Run the existing tiny synthetic model test on CPU.
8. **Audit a config without editing it.** Pick one registered config, compute SHA-256 with the package helper, and compare it with its referencing result file. If it differs, stop and document; do not rewrite.
9. **Validate the ledger.** Parse every nonblank line of `runs_v2.jsonl`, confirm `schema_version` and `evidence_class`, serialize/parse it again, and compare values. Use or extend the existing ledger test rather than hand-editing evidence.
10. **Explain an incomplete component.** Draw the planned score → EWMA → threshold → persistence state flow and list the synthetic edge cases required before implementation. Do not run an experiment.

## 22. How to continue safely

For ordinary development, activate the Python 3.12.8 environment, run the import smoke test and full unit suite, read the relevant config/module card, and make the smallest tested change. Use synthetic fixtures whenever possible.

For research-producing work, first obtain the relevant owner-gate approval. Register the config before execution, verify training/validation input hashes, record environment and seeds, write new versioned outputs, verify reload and reproduction, append the JSONL ledger, update governance documents, and only then prepare an atomic commit for human review.

The next research step is not another open-ended model search. It is formal Gate 3 closure, a registered controlled LSTM final-refit protocol, then Phase 5 validation-only alert-policy work. The internal test remains frozen throughout.
