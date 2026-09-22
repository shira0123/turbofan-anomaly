# Manuscript V1 handoff

## Current stage

The evidence foundation, detailed outline, five figures, two editable diagram sources, four cross-format tables, self-contained captions, reproducible build scripts, and artifact provenance are complete. The full manuscript has not been written. The next task is full manuscript synthesis from the verified foundation and generated assets, with registered citation keys and claim boundaries preserved.

Repository branch: `research/manuscript-v1`.

Artifact-generation starting commit: `4bcab1d13a1d44dccbedb0cecd7aa99ddea7ade1`. No remote reference was fetched or changed during artifact generation.

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
- `docs/manuscript/v1/figures/`: five SVG figures and five matching 300-dpi PNG previews
- `docs/manuscript/v1/figure_sources/figure_specs.json`: shared deterministic vector/raster specification
- `docs/manuscript/v1/figure_sources/system_architecture.dot`
- `docs/manuscript/v1/figure_sources/experimental_protocol.dot`
- `docs/manuscript/v1/tables/`: four tables, each in CSV, Markdown, and LaTeX
- `docs/manuscript/v1/CAPTIONS.md`
- `docs/manuscript/v1/BUILD.md`
- `docs/manuscript/v1/ARTIFACT_PROVENANCE.json`
- `scripts/manuscript/generate_manuscript_v1_assets.py`
- `scripts/manuscript/render_manuscript_v1_previews.ps1`
- `scripts/manuscript/verify_manuscript_v1_assets.py`

Regenerate and verify from the repository root:

```powershell
python scripts/manuscript/generate_manuscript_v1_assets.py --repo-root .
python scripts/manuscript/verify_manuscript_v1_assets.py --repo-root .
```

The verifier confirms exact registered values; CSV/Markdown/LaTeX consistency; eight selected literature citation keys; five well-formed SVG/PNG pairs; 300-dpi PNG metadata; allowlisted source hashes; and generated-artifact hashes. All five previews were visually inspected. Graphviz, Matplotlib, an SVG converter, and a LaTeX engine were unavailable, so DOT and LaTeX sources were retained without tool-specific rendering/compilation. No dependency was installed.

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

1. Resolve title, venue, author metadata, and delivery/attribution placement decisions recorded in `OPEN_QUESTIONS.md`.
2. Draft the full manuscript in Markdown from `OUTLINE.md`, inserting the generated figures/tables and citing only registered keys from `MANUSCRIPT_CORE_CITATIONS_V1.bib`.
3. Verify every numerical and methodological sentence against `EVIDENCE_MAP.md` and `ARTIFACT_PROVENANCE.json`.
4. After author review, create a venue-specific LaTeX manuscript without changing claim scope or silently converting incompatible literature metrics.

Do not create or revise the claims-audit addendum as part of artifact generation. Preserve the proxy-labelled internal held-out and deferred official-test boundaries during manuscript synthesis.
