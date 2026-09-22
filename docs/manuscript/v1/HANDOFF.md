# Manuscript V1 handoff

## Current stage

The evidence foundation and detailed outline are complete. The full manuscript, diagrams, plots, and final tables have not been created. The next task is to generate the planned figures, diagrams, and tables from committed aggregate authorities only.

Repository branch: `research/manuscript-v1`.

Verified base commit: `8e3dd9d16a42dad815395e541645afceb8617bbf`. At preparation time, fetched `origin/main`, `origin/research/phase5-validation`, the pre-existing local manuscript branch, and starting `HEAD` all resolved to this commit.

## Protected boundaries

- Do not open raw or derived training, validation, internal held-out, or official NASA-test datasets.
- Do not load model artifacts or run inference.
- Do not fit, train, tune, recalibrate, select thresholds, fuse detectors, or rerun confirmatory/scientific workflows.
- Do not recompute metrics from score traces.
- Do not modify existing protocols, reports, evidence matrices, or result authorities.
- Do not install, remove, or upgrade dependencies.
- The official NASA-test secondary evaluation remains deferred.

Figures and tables must read only committed aggregate configs/reports and must not invent curves, intervals, error bars, traces, or values.

## Completed outputs

- `docs/manuscript/v1/README.md`
- `docs/manuscript/v1/EVIDENCE_MAP.md`
- `docs/manuscript/v1/OUTLINE.md`
- `docs/manuscript/v1/FIGURE_TABLE_PLAN.md`
- `docs/manuscript/v1/OPEN_QUESTIONS.md`
- `docs/manuscript/v1/HANDOFF.md`

## Primary source authorities

### Frozen internal held-out result

- `configs/evaluation/fd002-confirmatory-results-v1.json`
- `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json`
- `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/result.json`
- Aggregate `detector_policy_metrics.csv`, `ranking_metrics.csv`, and `summary.json` in the same report directory

### Development and selection

- `configs/splits/fd002-primary-v1.json`
- `configs/preprocessing/fd002-preprocessing-selection-v1.json`
- `configs/baselines/fd002-classical-baselines-v1.json`
- `configs/lstm/fd002-lstm-final-refit-results-v1.json`
- `configs/alerting/fd002-alert-policy-study-protocol-v2.json`
- `configs/alerting/fd002-alert-policy-study-results-v1.json`
- Current implementation under `src/turbofan_anomaly/`

### Claims and literature

- `docs/research/FINAL_CLAIMS_AUDIT.md` and `final_claims_audit.json`
- `docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json`
- `docs/research/CORE_LITERATURE_COMPARABILITY_V1.md` and `core_literature_comparability_v1.json`
- `docs/research/CORE_LITERATURE_CLAIMS_IMPLICATIONS_V1.md`
- `docs/research/CORE_LITERATURE_SOURCE_VERIFICATION_V1.md`
- `docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib`
- `docs/research/ARTIFACT_MANIFEST.md`

### Later implementation authorities

- `configs/inference/fd002-frozen-inference-protocol-v1.json`
- `reports/inference_validation_v1/validation_regression.json`
- `docs/research/PCA_SENSOR_ATTRIBUTION_METHOD_V1.md`
- `src/turbofan_anomaly/inference/pipeline.py`
- `src/turbofan_anomaly/explainability/pca_attribution.py`

## Key verified facts

- Engine split: 156 train / 52 validation / 52 internal held-out; zero engine overlap.
- Healthy fitting: windows ending within the first 30% of training-engine life; other windows are unlabeled.
- P1/K=6: operating-setting scaler and K-Means use all training rows; per-mode sensor scalers use early-life training rows.
- Windows: 30 cycles × 21 sensors, stride 1.
- PCA input: 63 ordered summary features, not a flattened 630-value grid.
- Feature order: 21 means, 21 population SDs (`ddof=0`), 21 endpoint-minus-start differences.
- PCA raw score: mean squared reconstruction residual across standardized 63 features.
- Runtime order: frozen calibration → EWMA → current endpoint-mode strict threshold → persistence → events.
- State resets at engine boundaries or endpoint gaps, not mode changes.
- Attribution is an exact additive per-sensor PCA residual decomposition in normalized summary-feature space; it is non-causal and not SHAP.
- PCA was selected under the registered operational alert objective, not because it led validation ranking PR-AUC.
- The evaluated LSTM ensemble averages three aligned calibrated seed scores; PCA–LSTM fusion was not evaluated.

## Frozen primary values

| Proxy | FAR/1,000 | FAR % | Coverage | Median delay | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Final 10% | 32.440 | 3.2440% | 51.92% | 12 | 0.60267 | 0.94762 |
| Final 20% | 9.443 | 0.9443% | 78.85% | 25 | 0.80974 | 0.92673 |
| Final 30% | 5.153 | 0.5153% | 84.62% | 42.5 | 0.82745 | 0.86758 |

FAR is false-positive active endpoints divided by proxy-healthy endpoints. The aggregate delay is the median of the three proxy-specific medians: 25 cycles, not a pooled median. All three FAR values met the registered objective; aggregate delay missed the 12-cycle aspiration.

These are proxy-labelled internal held-out results, not official NASA-test results or physical fault-onset validation.

## Literature facts

- 20 verified core papers.
- 43 precisely located numerical values.
- Comparability A/B/C/D = 0/2/11/7.
- Zero directly protocol-equivalent numerical comparators.
- `LIT-013` / BibTeX key `core013` is the strongest partial comparator, but direct numerical comparison is prohibited.
- All literature FAR cells in the planned comparison table must be `NR—not comparable` unless a matching denominator, labels, split, and alert semantics are registered; none currently is.

## Documentation conflicts already resolved

Some guide sections and FCA-015/FCA-016 predate the later frozen inference/attribution implementation. Follow registered configs and current code. The supported correction is narrow: batch transform-only inference and local additive PCA reconstruction attribution exist. SHAP, causality, physical localization, streaming, online recalibration, and production deployment do not.

Before final manuscript approval, the author should authorize a new claims-audit version or addendum rather than editing the existing audit.

## Next action

1. Obtain author decisions on title, venue, author metadata, and placement of delivery/attribution material.
2. Generate Figure 1 (architecture) and Figure 2 (experimental protocol) as editable vectors.
3. Generate the three-panel FAR/coverage/delay figure and optional PR-AUC/ROC-AUC figure from aggregate committed values.
4. Generate the frozen result, metric-definition, and literature-comparability tables.
5. Validate all paths, citation keys, units, captions, and values against `EVIDENCE_MAP.md` before drafting full prose.

Do not write the full manuscript until those assets and publication choices are reviewed.
