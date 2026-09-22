# Manuscript V1 captions

## Figure 1. Implemented FD002 condition-aware anomaly-alert architecture

Training-only fitting and validation selection are separated from the frozen primary path. P1/K=6 fits its operating-setting scaler and K-Means using training-engine rows and its per-mode sensor scalers using early-life training rows. Engine-local 30-cycle × 21-sensor windows feed 63 ordered mean, population-standard-deviation, and endpoint-minus-start features to PCA; the LSTM comparator instead consumes the full sequence. In the frozen primary path, raw PCA reconstruction MSE is mapped through the training empirical CDF, smoothed with EWMA α=0.20, compared strictly with the frozen q=0.995 threshold for the endpoint mode, and passed through persistence 8 before event extraction. PCA sensor attribution is an additive reconstruction-error contribution in normalized summary-feature space, not SHAP, causality, or physical fault localization. The LSTM ensemble is an unfused comparator; PCA–LSTM fusion was not implemented.

## Figure 2. Experimental protocol and evaluation boundaries

The deterministic FD002 split assigns complete engines to 156 training, 52 validation, and 52 internal held-out engines with zero overlap. Learned preprocessing, detector, calibration, and threshold state uses registered training populations only; validation selects K, model candidates, and the alert policy. At the pre-held-out policy freeze (project governance Gate 4), the complete configuration was locked before internal held-out access: P1/K=6 preprocessing, 30-cycle windows and 63 PCA summaries, PCA scoring, training-only empirical-CDF calibration, endpoint-mode assignment, six per-mode q=0.995 thresholds, EWMA 0.20, persistence 8, reset rules, proxy definitions, event/metric semantics, and the unfused LSTM comparator. The completed first valid held-out run allowed no refit, recalibration, reselection, online update, or fusion. NASA’s separate official test protocol was not accessed and remains outside the completed study.

## Figure 3. Frozen PCA internal held-out operational results

Endpoint false-alert rate (FAR), engine detection coverage, and median detection delay for final-10%, final-20%, and final-30% normalized-life endpoint proxies on 52 internal held-out engines. FAR is false-positive active endpoints divided by proxy-healthy endpoints; the dashed 6% line is the registered endpoint-FAR objective. Coverage is detected engines divided by 52. Delay is measured from proxy onset to the first valid post-onset event and is summarized among detected engines; missed engines remain represented in coverage. The dashed 12-cycle line is the aggregate delay aspiration, not a separately registered per-proxy pass/fail rule. The registered aggregate delay is the median of the three proxy-specific medians (12, 25, and 42.5 cycles), equal to 25 cycles. No confidence intervals or error bars were registered. These are proxy-labelled internal held-out results, not official NASA-test or physical fault-onset performance.

## Figure 4. Frozen PCA threshold-free ranking by onset proxy

PR-AUC and ROC-AUC of frozen PCA calibrated scores under final-10%, final-20%, and final-30% normalized-life endpoint proxies in the internal held-out partition (9,271 window endpoints from 52 engines). Metrics pool included window endpoints within each proxy and are threshold-free ranking measures, not accuracy. No ROC/PR curves, confidence intervals, or error bars are inferred.

## Figure 5. Validation/model-selection ranking evidence

Mean validation PR-AUC and ROC-AUC across the three registered endpoint proxies for five P1/K=6 score sources on the same 52-engine validation split. Values are validation/model-selection evidence, not internal held-out performance. LOF and One-Class SVM lead the registered ranking comparison; PCA was frozen later because it won the separately preregistered operational alert-policy objective. The LSTM value is the arithmetic mean of window-ID-aligned calibrated scores from three fixed-epoch seeds. No PCA–LSTM fusion or uncertainty interval was evaluated.

## Table 1. Dataset and experimental-protocol summary

Engine, cycle-row, and length-30-window counts and the permitted role of each partition. The split manifest’s `test` label denotes the internal held-out partition; it is not NASA’s separate official test set. Official-test evaluation was not accessed and remains deferred.

## Table 2. Frozen primary policy and verified settings

Registered split, P1/K=6 preprocessing, window/feature construction, PCA scoring, empirical-CDF calibration, per-mode thresholds, EWMA, persistence, state-reset, event, attribution, and comparator/fusion boundaries. Operating modes are context clusters rather than causal physical regimes, and PCA contributions are local normalized-feature-space reconstruction-error decompositions rather than physical localization.

## Table 3. Frozen internal held-out primary result

Frozen PCA results under three normalized-life endpoint proxies. FAR/1,000 and FAR percentage use proxy-healthy endpoints as the denominator; coverage uses all 52 engines. Delay medians use detected engines only, with misses exposed through coverage. Display values are rounded as declared while the CSV preserves source precision. All three FAR values met the registered objective; the 25-cycle aggregate median-of-proxy-medians delay missed the 12-cycle aspiration. Results are not official NASA-test or observed physical-onset performance.

## Table 4. Focused literature comparison

Relevance-selected Category B partial comparators and Category C contextual studies, followed by this study’s three frozen proxy rows. Native literature metrics retain their original task and units. `NR` means not reported; “not comparable” means the dataset/task, split, onset definition, denominator, aggregation, or alert semantics do not align. Specificity is not converted into project-compatible FAR. No Category A comparator was identified, so the table does not support a numerical ranking or superiority claim.
