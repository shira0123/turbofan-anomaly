# Post-Confirmatory Implementation Roadmap

**Addendum ID:** `fd002-post-confirmatory-roadmap-v1`
**Date:** 2026-09-01
**Authority boundary:** Master Execution Bible v3 remains unchanged. This addendum begins after the first valid frozen internal held-out confirmatory run.

## Frozen-result rule

The reported confirmatory result is immutable. Future implementation, ablation, fusion, onset, external-data, official-test, or deployment work must receive a new identifier and evidence class and cannot alter, replace, pool with, or retroactively optimize the already reported confirmatory result.

## Research-required

| ID | Work item | Current state | Completion evidence |
|---|---|---|---|
| R1 | Literature comparability closure | v4 audit complete; no Category A comparator; unresolved bibliographic/method fields remain `NR` | Owner-reviewed v4 matrix and a manuscript bibliography whose cited claims link to verified evidence locations |
| R2 | Final claims approval | v1 audit complete; owner approval pending | Signed/recorded approval of permitted wording and prohibited upgrades |
| R3 | Limitations and threats to validity | pending synthesis | Manuscript section covering proxy labels, simulated data, one split, uncertainty, missing external validation, and selection boundaries |
| R4 | Validation-only ablation synthesis | pending; no new model run authorized | Table that clearly labels P0/P1, detector, LSTM-screen, and Phase 5 studies as validation-only |
| R5 | Paper tables and figures | pending | Figures/tables generated only from committed reports, with source paths and hashes |
| R6 | Reproducibility package | pending | Environment lock/manifest, governed artifact acquisition instructions, checksums, and a clean-clone verification record |
| R7 | Manuscript preparation | pending | Draft whose every quantitative sentence maps to the final claims audit |

## Implementation-required

### I1. Faithful PCA sensor-level reconstruction attribution

Implement native contributions for the frozen PCA detector without refitting or changing scores. Apply the frozen feature scaler, reconstruct the 63 standardized features through the frozen PCA, and compute each squared residual. Because the feature order is 21 means, 21 standard deviations, and 21 end-minus-start slopes, sensor `i` receives residual indices `i`, `21+i`, and `42+i`. Define the additive sensor contribution as the sum of those three squared residuals divided by 63; the 21 sensor contributions must sum to the current raw PCA mean-squared reconstruction score within a declared numerical tolerance.

Required contracts: exact score reconciliation; stable sensor and feature-group ordering; non-negative finite contributions; zero-residual behavior; single-feature/single-sensor perturbations; batch/single consistency; serialization reload consistency; and no change to calibrated score, mode threshold, EWMA, persistence, or alert decision. Call this **PCA reconstruction contribution**, not SHAP and not causal root-cause diagnosis.

### I2. Explanation validation

Validate completeness, sensitivity to controlled synthetic perturbations, rank stability under serialization, and alignment between feature-group and sensor aggregation. Document that correlated standardized summary features limit causal interpretation. Optional SHAP work requires the actual algorithm, a documented scalar target, realistic perturbations, and measured fidelity; it is not needed for the native attribution milestone.

### I3. Frozen preprocessing-to-alert inference pipeline

Build one read-only inference service function that loads and hash-checks the registered P1/K=6 preprocessor, PCA model/calibrator bundle, threshold table, and frozen policy config. It must validate and chronologically order a declared engine cycle frame; apply the frozen P1 transform; build engine-local `[30,21]` windows; assign endpoint-cycle operating mode; create `[63]` summary features; compute raw and calibrated PCA scores; apply the registered per-mode q=0.995 threshold, EWMA alpha 0.20 initialization/reset semantics, and persistence 8; and return window identity, endpoint mode, score, threshold, alert state, and validated contributions.

No online recalibration, score fusion, threshold selection, model fitting, or fallback to a different policy is permitted in this pipeline.

### I4. Interface, visualization, and resilience

| ID | Deliverable | Required behavior |
|---|---|---|
| I4.1 | CLI inference interface | Explicit input/output paths, dry-run/schema check, version/config/hash display, nonzero failure codes |
| I4.2 | Optional API wrapper | Thin wrapper around the same service function; no duplicated scientific logic |
| I4.3 | Engine timeline visualization | Scores, thresholds, alerts, proxy-free cycle axis, and contribution drill-down; no implied physical onset |
| I4.4 | Model/config loading | Fail closed on missing or mismatched hashes and incompatible schema/version |
| I4.5 | Input validation | Reject missing/duplicate cycles, engine mixing, non-finite values, wrong sensor order, invalid settings, and insufficient history |
| I4.6 | Error handling | Structured user-facing errors without partial evidence writes or silent fallback |
| I4.7 | Integration tests | Synthetic end-to-end parity with individual package functions, engine reset/isolation, mode changes, and deterministic replay |
| I4.8 | Demonstration workflow | Synthetic or explicitly authorized non-test example; no internal or official-test data bundled |

## Optional or future research

| Study | Boundary |
|---|---|
| PCA-LSTM fusion | A completely new pre-registered study; cannot reuse the confirmatory split for selection or revise the frozen result |
| Improved early-warning objective | New validation and confirmatory design with explicit missed-engine costs |
| Alternative onset proxies | Sensitivity study reported separately from the existing three endpoint proxies |
| External datasets | New provenance, preprocessing, task, and comparability contract |
| Official NASA test/RUL analysis | Different task definition and protocol; never relabel as the current anomaly-confirmatory result |
| Online recalibration | Requires healthy-update gating, drift safeguards, rollback, and prospective evaluation |
| Deployment monitoring | Requires input/score drift, alert-rate, calibration-integrity, and artifact-hash monitoring |

## Recommended sequence

1. Implement I1 and I2 with synthetic contracts and no project-data experiment.
2. Implement I3 with frozen artifact loading and deterministic parity tests.
3. Add I4 CLI, errors, visualization, integration tests, and a synthetic demonstration.
4. Finish R2-R7 from committed evidence; do not rerun or reinterpret the confirmatory result.
