# Manuscript V1 figure and table plan

## Production rules

- Generate no figures or tables during this evidence-foundation task.
- Use editable SVG (or venue-compatible TikZ) for conceptual diagrams.
- Use deterministic scripts for numerical plots and tables, reading only committed aggregate authorities.
- Preserve source precision internally; round only at presentation time using one recorded formatting rule.
- Do not read score traces, model artifacts, raw/derived datasets, or local ignored artifacts.
- Do not invent curves, confidence intervals, error bars, uncertainty bands, example trajectories, or numerical annotations.
- Do not use AI-generated graphics for numerical scientific figures.
- Every caption must say whether evidence is validation-only, internal held-out, or methodological.

## Figure 1 — Pipeline architecture diagram

**Working title:** Frozen condition-aware anomaly-alert architecture.

**Form:** Editable vector block diagram, landscape if needed. Keep distinct from the experimental-protocol diagram.

**Blocks:** cycle rows → P1/K=6 transform → engine-local `[30,21]` windows → 63 ordered summary features → feature scaling/PCA reconstruction → raw MSE → training empirical-CDF calibration → EWMA → current endpoint-mode threshold → persistence → events and local sensor contributions.

**Source authorities:**

- `src/turbofan_anomaly/data/preprocessing.py`, `RegimeSensorPreprocessor`
- `src/turbofan_anomaly/data/windows.py`, `build_window_array` and `summary_features`
- `src/turbofan_anomaly/models/classical.py`, `ClassicalAnomalyModel`
- `src/turbofan_anomaly/alerting/calibration.py`, `EmpiricalCDFCalibrator`
- `src/turbofan_anomaly/alerting/persistence.py`, `apply_alert_policy`
- `src/turbofan_anomaly/explainability/pca_attribution.py`, `attribute_pca_reconstruction`
- `configs/inference/fd002-frozen-inference-protocol-v1.json`

**Units/labels:** dimensions `[rows,26]`, `[windows,30,21]`, `[windows,63]`, and one score per endpoint; EWMA alpha 0.20; persistence 8; per-mode q=0.995.

**Intended message:** The frozen primary is a sequence-to-summary PCA alert pipeline with training-fitted state and explicit temporal decision logic.

**Limitations to show or state:** PCA does not reconstruct a flattened `30×21` grid. Sensor contributions are normalized-feature-space reconstruction residuals, not physical fault localization. Diagram is architecture, not performance evidence.

## Figure 2 — Experimental-protocol and evidence-flow diagram

**Working title:** Engine-disjoint development, policy freeze, and confirmatory evaluation protocol.

**Form:** Editable vector flow diagram with three partition lanes and freeze gates.

**Content:**

- 260 run-to-failure engines → 156 train / 52 validation / 52 internal held-out.
- Training lane: fit preprocessing, detector, calibrators, thresholds.
- Validation lane: K/model/alert-policy selection and proxy sensitivity.
- Gate 4 freeze: P1/K=6 + PCA + calibration + six thresholds + EWMA/persistence.
- Internal held-out lane: first valid transform/score/evaluate run, accepted regardless of metric values.
- Separate dashed future lane: official NASA test, deferred and not accessed.

**Source authorities:** `configs/splits/fd002-primary-v1.json`; `configs/alerting/fd002-alert-policy-study-protocol-v2.json`; `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json`; `DECISION_LOG.md`, Gate 4 and confirmatory entries.

**Units/labels:** engines, cycle rows, windows, evidence classes; no performance y-axis.

**Intended message:** Whole-engine separation and freeze timing prevent held-out feedback into fitting or policy selection.

**Limitations:** One fixed split; validation selection remains proxy-dependent; the diagram must not imply external validation.

## Figure 3 — Three-panel frozen operational results

**Working title:** Frozen PCA internal held-out alert behavior under three normalized-life endpoint proxies.

**Form:** Three aligned panels with the same categorical x-axis: final 10%, final 20%, final 30%.

### Panel A: endpoint FAR

- Values: 32.440, 9.443, 5.153.
- Unit: false-positive alerted endpoints per 1,000 proxy-healthy endpoints.
- Optional reference line: 60 per 1,000 (registered 6% objective), labeled as an objective—not a confidence boundary.

### Panel B: engine coverage

- Values: 51.92%, 78.85%, 84.62%.
- Unit: detected engines / 52 × 100.
- Optional count labels: 27/52, 41/52, 44/52.

### Panel C: median delay

- Values: 12, 25, 42.5 cycles.
- Unit: cycles after proxy onset among detected engines.
- Optional reference line: 12 cycles, labeled as the aspiration.
- Caption note: missed engines are excluded from delay medians and shown through coverage.

**Source authority:** `configs/evaluation/fd002-confirmatory-results-v1.json`, `primary_endpoint_results`; exact counts from PCA endpoint rows in `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/detector_policy_metrics.csv`.

**Intended message:** FAR met its objective across proxies, while coverage and delay varied substantially with proxy onset.

**Limitations:** No error bars or confidence intervals are registered. Categories are proxy definitions, not repeated trials or chronological time points. Do not connect them as a physical degradation curve unless the visual grammar makes the categorical nature unambiguous. Prefer bars or points without interpolating lines.

## Figure 4 — Frozen ranking metrics by proxy

**Working title:** Threshold-free ranking metrics for the frozen PCA primary.

**Form:** Separate two-panel or grouped-point figure for PR-AUC and ROC-AUC. Do not combine them with FAR, coverage, or delay on a dual axis.

**Values:**

| Proxy | PR-AUC | ROC-AUC |
|---|---:|---:|
| Final 10% | 0.60267 | 0.94762 |
| Final 20% | 0.80974 | 0.92673 |
| Final 30% | 0.82745 | 0.86758 |

**Source authority:** `configs/evaluation/fd002-confirmatory-results-v1.json`, `primary_endpoint_results`; exact values in `ranking_metrics.csv` PCA endpoint rows.

**Intended message:** Ranking conclusions also depend on the proxy and metric; PR-AUC and ROC-AUC move differently as prevalence and onset definition change.

**Limitations:** These are pooled-window metrics without engine-bootstrap uncertainty. They are not accuracy, operational threshold performance, or three points from a continuous curve. Include only if venue space permits.

## Figure 5 — Validation-only model comparison (conditional)

**Eligibility decision:** Comparable committed values exist for five frozen P1/K=6 score sources on the same 52-engine validation set and the same mean-over-three-endpoint-proxies definition. The figure is therefore permissible but optional.

**Form:** Paired dot plot or two small panels for mean validation PR-AUC and mean validation ROC-AUC.

| Score source | Mean PR-AUC | Mean ROC-AUC |
|---|---:|---:|
| LOF | 0.84969513 | 0.96436313 |
| One-Class SVM | 0.83280767 | 0.96437111 |
| LSTM calibrated ensemble | 0.82212053 | 0.95128915 |
| Isolation Forest | 0.78916934 | 0.95592104 |
| PCA reconstruction | 0.77240729 | 0.92503450 |

**Source authority:** `configs/alerting/fd002-alert-policy-study-results-v1.json`, `score_reproduction`; classical cross-check in `reports/baselines_v2/selected_models.csv`; LSTM cross-check in `configs/lstm/fd002-lstm-final-refit-results-v1.json`, `ensemble`.

**Intended message:** PCA did not lead validation ranking; it became primary only under the later registered alert-policy objective.

**Limitations:** Validation-only model selection evidence; no engine-bootstrap intervals. Do not put these means in the confirmatory result figure or imply held-out performance. Model families differ, although the final comparison used the same eligible-window count and validation proxy definitions.

## Table 1 — Dataset, partitions, and fitting roles

**Rows:** training, validation, internal held-out.

**Columns:** engines, cycle rows, length-30 windows, permitted role, learned state, proxy use.

**Source:** split manifest; guide §2.2; confirmatory result `population`.

**Units:** counts.

**Intended message:** Clarify whole-engine separation and prevent “test” ambiguity.

**Limitations:** Call the manifest's `test` partition internal held-out; reserve “official NASA test” for the deferred external files.

## Table 2 — Frozen methodology contract

**Rows:** split, healthy eligibility, P1 fitting, windowing, 63 features, PCA, calibration, endpoint mode, threshold, EWMA, persistence, reset, event, attribution.

**Columns:** frozen value/definition, fitted on, selected on, exact authority.

**Source:** paths and symbols listed in `EVIDENCE_MAP.md`.

**Units:** mixed; spell them out per row.

**Intended message:** Make leakage boundaries and exact computational semantics reviewable.

**Limitations:** This is a contract table, not a component-novelty claim.

## Table 3 — Frozen internal held-out primary result

**Columns:** endpoint proxy; FP/healthy endpoints; FAR/1,000; FAR %; detected/engines; coverage %; median delay cycles; PR-AUC; ROC-AUC.

**Rows:** final 10%, final 20%, final 30%.

**Source:** confirmatory result config plus aggregate `detector_policy_metrics.csv` and `ranking_metrics.csv`.

**Units:** explicitly in headers.

**Intended message:** Report the full FAR–coverage–delay trade-off, including the project's FAR.

**Caption requirements:** Internal held-out proxy-labelled PCA results; not official NASA-test or physical-onset performance. FAR objective met for all proxies; aggregate median-of-proxy-medians delay 25 cycles missed the 12-cycle aspiration.

**Limitations:** No confidence intervals; delay excludes missed engines, whose counts remain in coverage.

## Table 4 — Metric definitions and denominators

**Rows:** FAR/1,000 endpoints, FAR %, false-alert events/1,000, engines with healthy false alert, coverage, missed-engine rate, delay, aggregate delay, PR-AUC, ROC-AUC.

**Columns:** numerator, denominator/calculation, evaluation unit, aggregation, treatment of misses, proxy onset, code symbol.

**Source:** `src/turbofan_anomaly/evaluation/alerts.py`, `evaluation/proxies.py`, `evaluation/ranking.py`; confirmatory protocol metric list.

**Intended message:** Prevent metric-name drift and false denominator claims.

**Limitations:** No operating-hour denominator exists; the FAR percentage is not a percentage of healthy engines.

## Table 5 — Literature comparability table

**Rows:** 20 core papers plus one clearly separated “This study” block with three proxy rows.

**Literature columns:** citation key; dataset/subset; task; split/engine separation; learning status; onset/label; alert semantics; reported metric(s); FAR compatibility; category; decisive caveat.

**Project columns:** proxy; FAR/1,000 and FAR %; coverage; median delay; PR-AUC; ROC-AUC; internal held-out boundary.

**Source:** `docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json`; `core_literature_comparability_v1.json`; registered BibTeX; confirmatory results.

**FAR rule:** Every literature row currently receives `NR—not comparable`, with a concise reason such as denominator/label/split/event mismatch. LIT-013 specificity must not be converted into FAR. Project rows report their implemented FAR.

**Intended message:** Locate the study in the literature without ranking incompatible quantities.

**Limitations:** A/B/C/D = 0/2/11/7; no Category A or direct numerical comparison. RUL RMSE/NASA score, point F1, specificity, and laboratory detection rate remain in their original units and are not aligned with project alert metrics.

## Optional appendix table — Citation and evidence locator

**Rows:** all 20 core paper IDs.

**Columns:** BibTeX key, manuscript role, exact JSON paper record, numerical value IDs and page/table locations, comparability category.

**Source:** the citation map in `EVIDENCE_MAP.md`.

**Intended message:** Auditability for reviewers and future revisions.

**Limitations:** This is a provenance aid and may be supplementary material rather than main-text content.

## Rendering and validation plan for the next task

1. Write a small script that reads only the two committed aggregate confirmatory CSVs and the result config, then asserts all displayed rounded values against the config.
2. Write a separate validation-figure script that reads the registered alert result config, not window-level validation score files.
3. Render SVG and PDF with fixed fonts, color-blind-safe palette, and direct unit labels.
4. Keep the architecture and protocol source diagrams editable.
5. Generate Markdown and LaTeX tables from one structured in-memory representation.
6. Run a static audit that all figure/table source paths and citation keys exist.
7. Inspect the rendered outputs visually before manuscript insertion.
