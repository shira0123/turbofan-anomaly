# Manuscript V1 evidence map

## Status vocabulary

- **Supported—confirmatory:** registered first valid internal held-out result.
- **Supported—validation:** registered validation-only selection or diagnostic evidence.
- **Supported—implementation:** current registered protocol plus implementation/test contract; not a new performance result.
- **Qualified:** support exists only with the stated caveat.
- **Not tested:** no governed evidence supports the claim.
- **Prohibited:** conflicts with the registered evidence boundary.

## Claim taxonomy

| Stage | Defensible statement | Exact authority | Status and caveat |
|---|---|---|---|
| Original aspiration | Investigate whether operating-condition-aware normalization reduces legitimate operating-context effects in FD002 anomaly scoring. | `DECISION_LOG.md`, entries dated 2025-07-10 and 2025-07-11 | Historical research motivation, not a retrospectively declared statistical hypothesis and not by itself a supported result. |
| Preregistered operational objectives | Require worst endpoint false-positive rate at or below 60 per 1,000 healthy endpoints (6%) and treat 12 cycles as a median-delay aspiration. | `configs/alerting/fd002-alert-policy-study-protocol-v2.json`, `selection_objective.feasibility` and `selection_objective.median_delay_aspiration_cycles`; `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json`, `evaluation.validation_targets` | Operational targets, not null-hypothesis tests or significance thresholds. |
| Validation-stage selection | Gate 4 selected PCA reconstruction with per-mode q=0.995 thresholds, EWMA 0.20, and persistence 8 under a predeclared lexicographic objective. | `configs/alerting/fd002-alert-policy-study-results-v1.json`, `overall_recommendation`; protocol `selection_objective`; `DECISION_LOG.md`, 2026-08-27 and 2026-08-30 entries | Supported—validation. PCA was not selected because it had the highest ranking PR-AUC. |
| Frozen internal held-out finding | The first valid run retained the frozen PCA primary and an unfused LSTM comparator without refit, recalibration, reselection, online adaptation, or fusion. | `configs/evaluation/fd002-confirmatory-results-v1.json`, `status`, `primary_candidate_id`, `comparator_role`, and boundary booleans; confirmatory `result.json` | Supported—confirmatory. |
| Untested questions | Physical fault-onset validity, official NASA-test generalization, real-aircraft performance, fusion benefit, split-to-split robustness, and engine-level uncertainty remain untested. | `docs/research/final_claims_audit.json`, limitations; `configs/evaluation/fd002-confirmatory-results-v1.json`, `official_nasa_test_accessed`; alert protocol `complementarity.fusion_evaluated` | Not tested. Do not turn them into retrospective hypotheses or implied positive results. |
| Proposed future work | Separately preregistered official-test evaluation, engine-bootstrap uncertainty, failure analysis, and optional fusion may be studied later without changing the frozen result. | `docs/research/CORE_LITERATURE_CLAIMS_IMPLICATIONS_V1.md`, Official-test implication; `docs/research/POST_CONFIRMATORY_IMPLEMENTATION_ROADMAP.md`; `DECISION_LOG.md` | Future work only; the official-test secondary evaluation is deferred. |

## Dataset, partition, and fitting boundaries

| Proposed claim | Exact source location | Status | Required caveat |
|---|---|---|---|
| FD002 source rows contain engine, cycle, three operating settings, and 21 sensors. | `src/turbofan_anomaly/data/io.py`, `FD002_COLUMNS`; `docs/guides/PROJECT_UNDERSTANDING_GUIDE.md`, §2.1 | Supported—implementation | FD002 is simulated run-to-failure data and has no physical per-cycle onset labels. |
| The frozen deterministic split contains 156 train, 52 validation, and 52 internal held-out engines, with 60/20/20 ratios, seed 42, and maximum-cycle rank quintile stratification. | `configs/splits/fd002-primary-v1.json`, `split.ratios`, `split.seed`, `split.counts`, `split.stratification`; `src/turbofan_anomaly/data/splits.py`, `assign_engine_splits` and `validate_assignments` | Supported—confirmatory foundation | One fixed split does not establish split-to-split robustness. The manifest calls the internal held-out partition `test`; the manuscript should call it **internal held-out**. |
| All windows from an engine remain in one partition, with zero engine overlap. | `configs/splits/fd002-primary-v1.json`, explicit `engines` records; `src/turbofan_anomaly/data/splits.py`, `validate_assignments`; `tests/test_engine_splits.py` | Supported—implementation | Overlapping windows within an engine are not independent sampling units. |
| The partition sizes are 32,107/10,873/10,779 cycle rows and 27,583/9,365/9,271 length-30 windows for train/validation/internal held-out. | `docs/guides/PROJECT_UNDERSTANDING_GUIDE.md`, §2.2; held-out population also in `configs/evaluation/fd002-confirmatory-results-v1.json`, `population` | Supported; held-out population is confirmatory | Training and validation counts are foundation facts; held-out values must remain described as registered internal held-out population, not official NASA test. |
| The healthy-training rule admits only windows whose end cycle is at or before `floor(0.30 × max_cycle)` for each training engine. | `configs/baselines/fd002-classical-baselines-v1.json`, `training_policy`; `src/turbofan_anomaly/evaluation/proxies.py`, `training_eligible_windows`; `src/turbofan_anomaly/data/preprocessing.py`, `healthy_training_mask` | Supported—implementation | This is an early-life fitting assumption. Non-eligible windows are unlabeled, not known anomalies. |
| Classical detectors and their feature scaler/calibrator fit on 5,037 eligible windows from 156 training engines; validation contains 9,365 windows from 52 unseen engines. | `reports/baselines_v2/selected_models.csv`, `fit_window_count`, `fit_engine_count`; `configs/baselines/fd002-classical-baselines-v1.json`, `training_policy` and `sequence_shapes` | Supported—validation | These counts do not make validation windows independent; selection metrics pool windows under each proxy. |

## Operating-condition preprocessing and window representation

| Proposed claim | Exact source location | Status | Required caveat |
|---|---|---|---|
| P0 uses one global sensor scaler fitted on early-life training rows. | `src/turbofan_anomaly/data/preprocessing.py`, `GlobalSensorPreprocessor.fit`; `docs/guides/PROJECT_UNDERSTANDING_GUIDE.md`, §7.3 and §8.1 | Supported—implementation | P0 is a control, not the selected primary preprocessing treatment. |
| P1/K=6 standardizes all training-engine operating-setting rows, fits K-Means on the three scaled settings, and uses per-mode sensor scalers fitted only on early-life training rows; rare modes fall back to a global early-life training scaler. | `src/turbofan_anomaly/data/preprocessing.py`, `RegimeSensorPreprocessor.fit`, `predict_modes`, and `transform`; `configs/preprocessing/fd002-preprocessing-selection-v1.json`, `approved_choice` | Supported—implementation | K-Means modes are operating-context cluster IDs, not causal physical regimes. Operating scaler/K-Means use all training rows; sensor scalers use eligible early-life training rows. No validation or held-out row fits state. |
| K=6 was validation-selected over K=4 and K=8, with silhouette 0.9970369527, mean stability ARI 1.0, minimum validation mode fraction 0.1469695576, and zero fallback modes. | `configs/preprocessing/fd002-preprocessing-selection-v1.json`, `rationale`; `reports/preprocessing/model_selection.csv` | Supported—validation | This supports K=6 as a context representation; it does not prove six physical operating regimes. |
| Each engine-local window contains 30 consecutive cycles by 21 sensors, stride 1. | `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json`, `preprocessing.window_shape` and `window_stride`; `src/turbofan_anomaly/data/metadata.py`, `create_window_metadata`; `src/turbofan_anomaly/data/windows.py`, `build_window_array` | Supported—implementation | Windows never cross engine boundaries. |
| Classical models, including PCA, receive 63 summary features rather than a flattened 630-value grid. | `configs/baselines/fd002-classical-baselines-v1.json`, `feature_definition`; `src/turbofan_anomaly/data/windows.py`, `summary_features`; `configs/inference/fd002-frozen-inference-protocol-v1.json`, `pca_score_and_attribution.frozen_feature_representation` | Supported—implementation | Earlier conversational descriptions of PCA reconstructing a `30×21` grid are incorrect. The LSTM, by contrast, receives `[N,30,21]` sequences. |
| Feature order is 21 sensor means, then 21 sensor population standard deviations, then 21 endpoint-minus-start slopes, all in `sensor_1` through `sensor_21` order. | `src/turbofan_anomaly/data/windows.py`, `summary_features`; `src/turbofan_anomaly/data/preprocessing.py`, `SENSOR_COLUMNS`; inference protocol `windowing.sensor_order` and `pca_score_and_attribution.frozen_feature_representation` | Supported—implementation | `numpy.ndarray.std(axis=1)` uses `ddof=0`; the divisor is 30. “Slope” here is endpoint minus start, not a fitted time-regression coefficient. |
| Window operating mode is the P1/K=6 mode at the endpoint cycle, obtained by exact `(engine, end_cycle)` join. | `src/turbofan_anomaly/data/metadata.py`, `assign_endpoint_operating_modes`; alert protocol `metadata_lineage_correction`; confirmatory protocol `preprocessing.window_context_semantics` | Supported—implementation | It is not a majority-window mode, sensor-inferred mode, or reclustered held-out mode. |

## Detector, calibration, threshold, and state semantics

| Proposed claim | Exact source location | Status | Required caveat |
|---|---|---|---|
| The P1 PCA candidate retained 90% explained variance at validation selection. | `reports/baselines_v2/selected_models.csv`, row `p1_k6,pca`, `parameters={"n_components":0.9}`; alert protocol `score_sources[detector_id=pca_reconstruction].parameters` | Supported—validation | This is a registered model choice, not a claim that 90% variance is universally optimal. |
| PCA first standardizes the 63 summary features using eligible training features, reconstructs them through PCA, and scores the mean squared residual across all 63 standardized features. | `src/turbofan_anomaly/models/classical.py`, `ClassicalAnomalyModel.fit` and `_raw_scores_scaled`; inference protocol `pca_score_and_attribution.raw_score_formula` | Supported—implementation | The raw score is in standardized summary-feature space and is not physical sensor error. |
| Detector raw scores are mapped to right-sided empirical-CDF percentiles using only eligible training scores: `count(training_score <= score)/n`. | `src/turbofan_anomaly/alerting/calibration.py`, `EmpiricalCDFCalibrator.fit/transform`; `src/turbofan_anomaly/models/classical.py`, `fit` and `score` | Supported—implementation | The calibrated value is a training-reference percentile, not a fault probability. |
| Frozen PCA thresholds are six per-mode q=0.995 thresholds fitted to calibrated eligible-training scores using NumPy `method="higher"`. | `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json`, `primary.threshold_context` and `primary.thresholds`; alert protocol `grid.threshold_rules`; `src/turbofan_anomaly/alerting/thresholds.py`, `ThresholdRule.fit` and `fit_thresholds` | Supported—confirmatory policy | Threshold state was frozen before internal held-out access and was not refitted. |
| Exact online decision order is: transform-only preprocessing → window/63-feature construction → raw PCA score → frozen empirical-CDF calibration → EWMA of calibrated scores → strict comparison of the smoothed score with the current endpoint-mode threshold → persistence counter → active alert/event extraction. | `src/turbofan_anomaly/inference/pipeline.py`, `FrozenFD002InferencePipeline.infer`; `src/turbofan_anomaly/alerting/persistence.py`, `apply_alert_policy`; confirmatory protocol `primary` | Supported—implementation | Thresholds were fitted before evaluation from unsmoothed calibrated training reference scores; the runtime comparison happens after EWMA. Online recalibration is off. |
| EWMA alpha is 0.20 and persistence is eight consecutive strict violations; alert onset is the eighth violating window without backdating. | Confirmatory protocol `primary.ewma_alpha`, `primary.persistence`, `primary.comparison`; alert protocol `state_contract`; `apply_alert_policy` | Supported—confirmatory policy | Persistence adds delay by design. |
| State resets at a new engine or a nonconsecutive endpoint cycle, initializes EWMA from the first score of the segment, and does not reset on a mode change. | Alert protocol `state_contract`; `src/turbofan_anomaly/alerting/persistence.py`, `apply_alert_policy` | Supported—implementation | Batch inference rejects cycle gaps, while the generic alert state machine also defines a gap reset. The current mode selects the threshold each endpoint. |
| Events are contiguous active endpoints within one engine and consecutive end cycles. | Confirmatory protocol `evaluation.event_definition`; `src/turbofan_anomaly/evaluation/alerts.py`, `extract_alert_events` | Supported—implementation | An event that begins before a proxy onset is not counted as a valid post-onset detection, even if it crosses the onset. |

## Attribution and delivery claims

| Proposed claim | Exact source location | Status | Required caveat |
|---|---|---|---|
| For sensor `s`, local PCA contribution equals the sum of its standardized mean-, standard-deviation-, and slope-feature squared residuals divided by 63. The 21 contributions add to the raw PCA MSE. | `configs/inference/fd002-frozen-inference-protocol-v1.json`, `pca_score_and_attribution`; `src/turbofan_anomaly/explainability/pca_attribution.py`, `attribute_pca_reconstruction`; `docs/research/PCA_SENSOR_ATTRIBUTION_METHOD_V1.md` | Supported—implementation | Observational local model-fidelity decomposition only; not SHAP, causal diagnosis, physical fault localization, or global importance. |
| A hash-checked, transform-only batch interface implements the frozen P1/K=6 → PCA → alert policy. | Inference protocol `delivery`; `src/turbofan_anomaly/inference/loader.py`; `src/turbofan_anomaly/inference/pipeline.py`; `reports/inference_validation_v1/validation_regression.json` | Supported—implementation | Validation-only regression evidence, not new held-out performance. Streaming and online state serialization remain pending. Do not call this production deployment. |
| The final claims audit's “explainability planned” and “inference remains implementation work” statements are superseded only for the narrow implementation described above. | Earlier statements: `docs/research/final_claims_audit.json`, FCA-015/FCA-016. Later authorities: inference protocol, attribution code/method, validation regression, and `docs/research/ARTIFACT_MANIFEST.md`, “Frozen inference and explanation implementation” | Resolved documentation conflict | The protected audit remains unchanged. A versioned claims-audit addendum is advisable before full-manuscript approval. All causal, SHAP, operational, streaming, and production prohibitions remain in force. |

## How PCA became the frozen primary

| Step | Exact evidence | Defensible interpretation |
|---|---|---|
| Classical ranking selection | `reports/baselines_v2/selected_models.csv`; `configs/baselines/fd002-classical-baselines-v1.json`, `selection_rule` | LOF, not PCA, had the highest mean validation PR-AUC among P1 classical models. |
| Final LSTM refit | `configs/lstm/fd002-lstm-final-refit-results-v1.json`, `convergence_best_epochs`, `locked_epoch_count`, and `ensemble` | Three seeds (43–45) were locked to 54 epochs by the preregistered median-best-epoch rule. Their calibrated-score mean beat individual seeds but not LOF/OCSVM on mean validation PR-AUC. |
| Alert-policy grid | `configs/alerting/fd002-alert-policy-study-protocol-v2.json`, `grid` and `selection_objective`; result config `counts` | Five score sources × two threshold contexts × eight rules × four EWMA states × four persistence values produced 1,280 candidates, each evaluated under five proxies (6,400 rows). |
| Operational selection | Protocol `selection_objective.order_among_feasible`; `src/turbofan_anomaly/evaluation/alerts.py`, `_selection_key`; result config `overall_recommendation` | After the endpoint-FAR feasibility screen, the lexicographic objective prioritized minimum and mean engine coverage before event/engine false alerts, delay, lead, and candidate ID. PCA won that registered operational objective. |
| Gate 4 freeze | `DECISION_LOG.md`, 2026-08-30; confirmatory protocol `primary` | The PCA per-mode q=0.995/EWMA 0.20/persistence-8 policy was frozen before internal held-out access. |

## Ensembles and fusion boundary

| Claim | Exact source location | Status and caveat |
|---|---|---|
| The evaluated LSTM ensemble is the arithmetic mean of window-ID-aligned calibrated scores from seeds 43, 44, and 45. | `src/turbofan_anomaly/models/lstm_training.py`, `aligned_calibrated_score_ensemble`; `configs/lstm/fd002-lstm-final-refit-results-v1.json`, `ensemble`; confirmatory protocol `comparator.aggregation` | Supported—validation and confirmatory comparator. It is an ensemble within one model family. |
| The confirmatory LSTM ensemble used its separately frozen per-mode q=0.995/EWMA 0.20/persistence-3 policy. | Confirmatory protocol `comparator` | Supported—confirmatory comparator; not the primary. |
| PCA–LSTM score fusion, decision fusion, stacking, voting, and online fusion were not implemented or evaluated. | Alert protocol `complementarity.fusion_evaluated=false`; alert result `fusion_evaluated=false`; confirmatory result `score_or_decision_fusion=false` | Not tested. Pairwise complementarity tables do not prove fusion benefit or error independence. |

## Confirmatory primary metrics

All rows below concern the frozen PCA primary on 52 engines and 9,271 windows in the internal held-out partition. Values come from committed aggregate reports; no score trace was recomputed.

| Proxy | FP / healthy endpoints | FAR/1,000 | FAR % | Detected / engines | Coverage % | Median delay among detected engines | PR-AUC | ROC-AUC | Exact authority |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Final 10% endpoint | 265 / 8,169 | 32.440 | 3.2440% | 27 / 52 | 51.92% | 12 cycles | 0.60267 | 0.94762 | `configs/evaluation/fd002-confirmatory-results-v1.json`, `primary_endpoint_results[policy_id=normalized_life_last_10pct_endpoint]`; exact counts in `detector_policy_metrics.csv`, PCA row; AUCs in `ranking_metrics.csv`, PCA row |
| Final 20% endpoint | 67 / 7,095 | 9.443 | 0.9443% | 41 / 52 | 78.85% | 25 cycles | 0.80974 | 0.92673 | Same authorities, `normalized_life_last_20pct_endpoint` |
| Final 30% endpoint | 31 / 6,016 | 5.153 | 0.5153% | 44 / 52 | 84.62% | 42.5 cycles | 0.82745 | 0.86758 | Same authorities, `normalized_life_last_30pct_endpoint` |

The FAR objective was achieved for all three proxies. The registered aggregate delay is `median(12, 25, 42.5) = 25` cycles: the median of the three proxy-specific engine-delay medians, not a median pooled across engines or proxies. Authority: `configs/evaluation/fd002-confirmatory-results-v1.json`, `target_attainment.aggregate_median_delay_cycles`; aggregation convention: `src/turbofan_anomaly/evaluation/alerts.py`, `aggregate_candidate_metrics` (`median_policy_median_detection_delay`). The aggregate 25-cycle result did not meet the 12-cycle aspiration.

## Metric definitions and units

| Metric | Implemented numerator / denominator or calculation | Unit and aggregation | Population, misses, and onset | Exact source |
|---|---|---|---|---|
| Endpoint FAR/1,000 | `FP active endpoints / (FP + TN healthy endpoints) × 1,000` | Alerted endpoints per 1,000 proxy-healthy window endpoints, pooled within one proxy | Internal held-out PCA endpoints. Endpoint onset is `floor(L × (1-q)) + 1`. | `src/turbofan_anomaly/evaluation/alerts.py`, `evaluate_alert_policy`, key `false_positive_alerted_endpoints_per_1000_healthy_endpoints`; `src/turbofan_anomaly/evaluation/proxies.py`, `NormalizedLifeOnsetPolicy.apply` |
| Endpoint FAR % | `FP / healthy endpoints × 100`, equal to FAR/1,000 divided by 10 | Percent of proxy-healthy endpoints | Not percent of healthy engines, events, engines, cycles per hour, or operating hours. | `src/turbofan_anomaly/workflows/run_confirmatory_evaluation.py`, assignment to `endpoint_false_alert_rate_percent`; aggregate CSV |
| False-alert events/1,000 | Pre-onset event count / healthy endpoints × 1,000 | Events per 1,000 proxy-healthy endpoints | Event numerator differs from endpoint FP numerator. | `evaluate_alert_policy`, `false_alert_events_per_1000_healthy_endpoints` |
| Engines with any healthy false alert | Engines having at least one event starting before proxy onset / 52 × 100 | Percent of engines | Separate from endpoint FAR. Confirmatory values are 22/52, 8/52, and 4/52 for final 10/20/30%. | `evaluate_alert_policy`, `percent_engines_with_healthy_false_alert`; aggregate CSV |
| Engine detection coverage | Engines with an event whose start is at or after proxy onset / 52 × 100 | Percent of engines | Crossing events are not valid detections. Missed engines remain in the denominator. | `evaluate_alert_policy`, `engine_detection_coverage` and `valid_events` |
| Missed-engine rate | `(52 - detected engines) / 52 × 100` | Percent of engines | Complements coverage. | `evaluate_alert_policy`, `missed_engine_rate` |
| First-alert delay | For each detected engine, `first valid post-onset event start cycle - onset cycle`; report median and IQR | Cycles; median across detected engines within one proxy | Missed engines have missing delay and are excluded from the delay median, but reported separately through coverage/missed rate. Persistence delay is included. | `evaluate_alert_policy`, `first_alert_delay`, `median_first_alert_delay`; alert protocol `metric_contract` |
| Aggregate delay | Median of the three proxy-specific median first-alert delays | Cycles; policy-level aggregation | Not pooled across the detected engines from all proxies. | Confirmatory results `target_attainment`; `aggregate_candidate_metrics` convention |
| PR-AUC | `average_precision_score(proxy labels, calibrated scores)` over included window endpoints | Unitless area; pooled included endpoints within one proxy | Endpoint proxies include all 9,271 windows; full-window proxies exclude ambiguous overlaps. No threshold is chosen by PR-AUC. | `src/turbofan_anomaly/evaluation/ranking.py`, `proxy_ranking_metrics` |
| ROC-AUC | `roc_auc_score(proxy labels, calibrated scores)` over included window endpoints | Unitless area; pooled included endpoints within one proxy | Same population rule as PR-AUC; not accuracy. | `proxy_ranking_metrics` |

## Validation-stage findings available for bounded discussion

| Claim | Exact authority | Status and caveat |
|---|---|---|
| Selected P1 validation mean PR-AUC/ROC-AUC: LOF 0.84969513/0.96436313; OCSVM 0.83280767/0.96437111; LSTM ensemble 0.82212053/0.95128915; Isolation Forest 0.78916934/0.95592104; PCA 0.77240729/0.92503450. | `configs/alerting/fd002-alert-policy-study-results-v1.json`, `score_reproduction`; classical rows also in `reports/baselines_v2/selected_models.csv`; LSTM in final-refit results `ensemble` | Supported—validation. Same 52 validation engines and three endpoint proxies; not held-out performance. Use only as a validation model-comparison figure/table, never mix with confirmatory values. |
| All 12 matched classical parameter pairs improved mean validation PR-AUC under P1 versus P0. | `PROGRESS.md`, classical section; underlying `reports/baselines_v2/model_selection.csv` | Qualified validation finding. It supports carrying P1 forward but is not a causal effect estimate and has no engine-bootstrap uncertainty. |
| LOF and Isolation Forest selected feasible zero-alert policies with zero engine detections in Phase 5. | Alert results `best_policy_per_detector`; `DECISION_LOG.md`, 2026-08-27 | Supported negative validation result. A zero FAR without detection is not desirable superiority. |

## Literature evidence accounting

| Claim | Exact authority | Status and caveat |
|---|---|---|
| The manuscript-grade core contains 20 deeply extracted legal full texts and 43 located numerical values. | `docs/research/core_manuscript_extraction_summary_v1.json`, `selected_count`, `deeply_extracted_count`, `verified_numerical_value_count`; `docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json`, `papers` and `numerical_values` | Verified from committed records. |
| Strict comparability counts are A/B/C/D = 0/2/11/7, with zero direct comparisons. | Extraction summary `category_counts`, `direct_comparison_count`; `docs/research/core_literature_comparability_v1.json`, `rows` and `direct_equivalent_comparator_found`; comparability Markdown category table | Verified. No directly protocol-equivalent published comparator was identified. |
| LIT-013 is the strongest partial comparator but cannot support a side-by-side performance claim. | Comparability Markdown “Strongest partial comparator”; core evidence paper `LIT-013`; comparability row `LIT-013` | Same FD002 anomaly intent, but within-engine window splitting, proxy, threshold, persistence, and point metrics differ. |
| Literature specificity must not be converted into this project's FAR. | `docs/research/CORE_LITERATURE_COMPARABILITY_V1.md`, “Metric discipline”; `CORE_LITERATURE_CLAIMS_IMPLICATIONS_V1.md`, prohibited claims | Denominator, labels, split, and alert semantics do not match. All literature FAR cells in the planned table must be `NR—not comparable` unless an explicitly compatible definition is present; none is registered in the core set. |

## Proposed citation map

Every proposed citation key already exists in `docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib`. The exact evidence location is the stated paper record in `docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json`; any numerical value must additionally cite its `numerical_values[value_id=...]` record and its recorded page/section/table location. “Experimental context” means the paper's results may be described with its own units and caveat, not compared numerically with this project.

| Paper ID | BibTeX key | Proposed use | Evidence type | Exact evidence location |
|---|---|---|---|---|
| LIT-001 | `core001` | C-MAPSS simulation and unknown-onset boundary | Method/dataset foundation | `papers[core_paper_id=LIT-001]`, fields `dataset`, `research_task`, `authors_stated_limitations`, `protocol_identified_limitations`, `manuscript_citation_role` |
| LIT-003 | `core003` | Benchmark-comparison cautions | Method/evaluation foundation | `papers[core_paper_id=LIT-003]`, `methodological_relevance`, `exact_comparability_caveat` |
| LIT-004 | `core004` | Official-test protocol interpretation | Method/evaluation foundation | `papers[core_paper_id=LIT-004]`, `nasa_files_used`, `train_validation_test_split`, `manuscript_citation_role` |
| LIT-005 | `core005` | LSTM encoder-decoder reconstruction foundation | Method foundation | `papers[core_paper_id=LIT-005]`, `model`, `calibration`, `threshold_method`, `manuscript_citation_role` |
| LIT-006 | `core006` | Unsupervised LSTM health-index precedent | Method plus non-comparable experimental context | `papers[core_paper_id=LIT-006]`; values `LIT-006-V01`–`V08`, page 7, §6.2.2, Table 1; all `directly_comparable_with_project=false` |
| LIT-007 | `core007` | Healthy-only reconstruction with engine-disjoint evaluation | Non-comparable experimental context | `papers[core_paper_id=LIT-007]`; values `LIT-007-V01`–`V03`, page 47, §IV, Table VI; FD004 caveat |
| LIT-008 | `core008` | One-class calibration and learned-onset precedent | Method foundation | `papers[core_paper_id=LIT-008]`, `healthy_data_definition`, `anomaly_or_degradation_onset_definition`, `calibration`, `threshold_method` |
| LIT-009 | `core009` | Variable-condition and official-test RUL context | Method/protocol context | `papers[core_paper_id=LIT-009]`, `exact_cmapss_subset`, `nasa_files_used`, `prediction_target`, `exact_comparability_caveat` |
| LIT-010 | `core010` | Related FD002 key-point anomaly/degradation work | Experimental context without extracted comparison number | `papers[core_paper_id=LIT-010]`, all task/split/label/metric fields and `exact_comparability_caveat` |
| LIT-012 | `core012` | Physics-inspired temporal reconstruction | Non-comparable experimental context | `papers[core_paper_id=LIT-012]`; values `LIT-012-V01`–`V10`, page 7, §IV-B, Table II; all non-comparable |
| LIT-013 | `core013` | Closest FD002 unsupervised LSTM-autoencoder study | Strongest partial experimental comparator | `papers[core_paper_id=LIT-013]`; FD002 values `LIT-013-V06`–`V10`, page 9, §VI, Table 3; within-engine split and alert-policy caveat |
| LIT-014 | `core014` | Residualization before LSTM reconstruction | Method foundation | `papers[core_paper_id=LIT-014]`, `preprocessing`, `operating_condition_treatment`, `model`, `methodological_relevance` |
| LIT-017 | `core017` | Condition-aware normalization | Method foundation | `papers[core_paper_id=LIT-017]`, `scaling`, `operating_condition_treatment`, `methodological_relevance` |
| LIT-018 | `core018` | FD002 regime scaling and official-test RUL context | Method/protocol context | `papers[core_paper_id=LIT-018]`, `exact_cmapss_subset`, `nasa_files_used`, `regime_clustering`, `prediction_target` |
| LIT-021 | `core021` | Learned regime-aware baselining | Method foundation | `papers[core_paper_id=LIT-021]`, `operating_condition_treatment`, `regime_clustering`, `methodological_relevance` |
| LIT-026 | `core026` | Dynamic thresholds and event grouping | Method foundation | `papers[core_paper_id=LIT-026]`, `threshold_method`, `smoothing`, `persistence_or_event_semantics` |
| LIT-034 | `core034` | Event-aware anomaly evaluation and score postprocessing | Method/evaluation foundation | `papers[core_paper_id=LIT-034]`, `evaluation_unit`, `threshold_method`, `persistence_or_event_semantics` |
| LIT-036 | `core036` | Rigorous time-series anomaly evaluation and point-adjustment caution | Method/evaluation foundation | `papers[core_paper_id=LIT-036]`, `evaluation_unit`, `protocol_identified_limitations`, `manuscript_citation_role` |
| LIT-051 | `core051` | Aero-engine LSTM-autoencoder fault-detection context | Method plus non-comparable experimental context | `papers[core_paper_id=LIT-051]`, `dataset`, `model`, `exact_comparability_caveat`; reserve replacement documented in extraction summary `replacement` |
| LIT-055 | `core055` | Sensor-wise reconstruction attribution precedent | Method foundation; results non-comparable | `papers[core_paper_id=LIT-055]`, `explanation_method`; values `LIT-055-V01`–`V02`, page 1/recorded results sections; no FD002 alert comparison |

## Prohibited or unsupported manuscript claims

- Do not claim superiority, state of the art, first-ever novelty, production readiness, operational field FAR, or real-aircraft generalization.
- Do not call proxy labels physical fault onset or call PR-AUC/ROC-AUC accuracy.
- Do not call FAR the percentage of healthy engines. The separate engine-level quantity is `percent_engines_with_healthy_false_alert`.
- Do not express FAR per engine or per operating hour; neither denominator is implemented.
- Do not compare RUL RMSE/NASA score, point-level precision/recall/F1, specificity, laboratory detection rate, or point-adjusted metrics directly with endpoint FAR, coverage, delay, PR-AUC, or ROC-AUC.
- Do not infer FAR from a literature specificity value.
- Do not claim PCA reconstructs a `30×21` sensor-time grid.
- Do not claim PCA contribution ranking is SHAP, causal explanation, root-cause identification, or physical fault localization.
- Do not claim the LSTM ensemble was the selected primary or that PCA–LSTM fusion was evaluated.
- Do not call the internal held-out partition the official NASA test set.
