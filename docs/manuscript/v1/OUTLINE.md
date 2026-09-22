# Manuscript V1 detailed outline

## Front matter TODOs

- **Authors:** TODO—author-provided names and order.
- **Affiliations:** TODO—author-provided institutional names and addresses.
- **Corresponding author:** TODO—name and verified contact details.
- **Target venue and article type:** TODO—required before LaTeX formatting, length allocation, and final section naming.
- **Keywords:** provisional: turbofan anomaly detection; condition-aware preprocessing; one-class learning; PCA reconstruction; persistent alerts; C-MAPSS FD002; leakage-controlled evaluation.

## Working title options

1. **Context-Aware Anomaly Alerting for C-MAPSS FD002: A Leakage-Controlled, Engine-Disjoint Evaluation**
2. **Operating-Condition-Aware PCA Alerting on FD002: Frozen-Policy Internal Held-Out Evidence**
3. **From Operating Regimes to Persistent Alerts: A Governed FD002 Anomaly-Detection Study**

Preferred working title: option 1. It names the research treatment and evaluation discipline without implying algorithmic novelty, official NASA-test performance, or production readiness.

## Abstract

Plan a structured or single-paragraph abstract, depending on the venue, with five functions:

1. **Context:** legitimate FD002 operating-condition changes can resemble degradation in sensor space.
2. **Objective:** evaluate an operating-condition-aware, healthy-only anomaly-alert pipeline under engine-disjoint development and a frozen internal held-out protocol.
3. **Methods:** 156/52/52 engine split; P1/K=6 preprocessing; 30-cycle, 21-sensor windows; 63-feature PCA reconstruction; training-only empirical-CDF calibration; frozen per-mode q=0.995 thresholds; EWMA 0.20; persistence 8; final-10/20/30% normalized-life endpoint proxies.
4. **Results:** report the three proxy rows together—FAR/1,000 and FAR %, coverage, median delay, PR-AUC, and ROC-AUC. State that all FAR objectives were met, while the median-of-proxy-medians delay was 25 cycles and missed the 12-cycle aspiration.
5. **Boundary/conclusion:** results are proxy-sensitive internal held-out evidence, not official NASA-test or physical-onset validation; the main contribution is governed integration and transparent metric semantics, not a new PCA/K-Means/EWMA algorithm.

Do not write the abstract as “85% accuracy.” Do not lead with the most favorable proxy alone.

## 1. Introduction, related work, and contributions

### 1.1 Problem motivation

- Explain the central ambiguity: sensor change can reflect operating condition, degradation, or noise.
- Motivate context-aware normalization as the research treatment and global normalization as the control.
- Explain why an alert system needs ranking, threshold, temporal smoothing, persistence, event, and engine metrics—not only a window ranking score.
- Introduce FD002 as a multi-condition, single-fault-mode simulated run-to-failure benchmark while stating its lack of physical per-cycle onset labels.
- Cite C-MAPSS foundation and evaluation cautions: `core001`, `core003`, `core004`.

### 1.2 Related work

Organize related work by function rather than by claiming a league table:

- **Reconstruction and health-index methods:** `core005`, `core006`, `core007`, `core012`, `core051`.
- **Closest FD002 anomaly/degradation studies:** `core010`, `core013`. Name `core013` as the strongest partial comparator but immediately state the within-engine split, onset, threshold, persistence, and metric mismatches.
- **Operating-condition treatment and regime-aware baselining:** `core014`, `core017`, `core018`, `core021`.
- **Change points, score calibration, dynamic thresholds, and event semantics:** `core008`, `core009`, `core026`.
- **Rigorous time-series anomaly evaluation:** `core034`, `core036`.
- **Observational reconstruction attribution:** `core055`.

Conclude this subsection with the required sentence: “No directly protocol-equivalent published comparator was identified in the manuscript-grade core literature set.” Do not infer a compatible FAR from reported specificity, point F1, RUL error, or laboratory detection rate.

### 1.3 Research objective and evidence classes

- Present the original objective as an aspiration: determine whether operating-condition-aware preprocessing improves anomaly ranking and later alert behavior under a leakage-controlled comparison.
- Distinguish the operational FAR target and delay aspiration from statistical hypothesis tests.
- Define development, validation selection, frozen internal held-out, and future external evidence.
- State that the official NASA-test secondary evaluation is deferred.

### 1.4 Contributions

Use bounded contribution language:

1. A deterministic engine-disjoint FD002 study design with explicit early-life fit assumptions and late-life evaluation proxies.
2. A condition-aware P1/K=6 preprocessing pipeline that separates operating-setting clustering from healthy-only sensor scaling.
3. A governed detector-to-alert comparison across classical and LSTM score sources, with all fitting and policy selection completed before internal held-out access.
4. Transparent endpoint-, event-, and engine-level metric definitions that jointly report FAR, coverage, and delay under three onset proxies.
5. A frozen, hash-checked batch delivery path and exact PCA reconstruction-error contribution decomposition, described strictly as implementation capability rather than new performance evidence.

Explicitly state what is not contributed: a new anomaly algorithm, causal fault localization, physical-onset labels, production validation, or literature superiority.

## 2. Dataset and experimental protocol

### 2.1 FD002 data and study boundary

- Describe the 26-column cycle schema: engine, cycle, three operating settings, 21 sensors.
- Explain run-to-failure trajectories and the absence of physical onset annotations.
- Distinguish the run-to-failure source used for the internal split from NASA's separate truncated official test files.
- State that official-test files were not accessed in the confirmatory study.

### 2.2 Engine-disjoint split

- Present the deterministic 60/20/20 assignment: 156 training, 52 validation, 52 internal held-out engines.
- Explain maximum-cycle rank quintile stratification, seed 42, secondary seed 43, and zero engine overlap.
- Give cycle/window counts: 32,107/27,583 train; 10,873/9,365 validation; 10,779/9,271 internal held-out.
- Explain that overlapping windows are correlated and uncertainty cannot treat windows as independent engines.

### 2.3 Healthy-training eligibility versus evaluation proxies

- Define eligible fitting windows as those ending within the first 30% of a training engine's observed life.
- State that later training windows are unlabeled, not known anomalies.
- Define endpoint proxy onset as `floor(L × (1-q)) + 1` for q in 0.10, 0.20, and 0.30.
- Explain endpoint and full-window semantics; retain full-window results as validation sensitivity evidence rather than confirmatory headline results.
- Emphasize that proxy choice changes class balance and operational interpretation.

### 2.4 Governance and freeze sequence

- Trace the gates: split → preprocessing selection → detector/LSTM validation → alert-policy validation → Gate 4 freeze → first valid internal held-out run.
- State that the held-out result was accepted regardless of values and that no post-access refit, recalibration, threshold change, candidate search, online adaptation, or fusion occurred.
- Refer to the separate experimental-protocol diagram planned in `FIGURE_TABLE_PLAN.md`.

## 3. Proposed methodology

The section heading follows the requested manuscript structure. In the paper text, avoid implying that each component is newly proposed; call it the **studied pipeline** or **frozen methodology** where appropriate.

### 3.1 P0 and P1/K=6 preprocessing

- P0: one sensor scaler fitted on early-life training rows.
- P1: standardize three operating settings using all training-engine rows; fit six-cluster K-Means using training rows; assign each row a canonical mode; fit per-mode sensor scalers on eligible early-life training rows; use a global eligible-training fallback for sparse modes.
- Explain K=6 validation selection over K=4/K=8, with its evidence and non-causal cluster-label caveat.
- Clarify that P1 is preprocessing, not the LSTM.

### 3.2 Window construction and model-specific inputs

- Slide 30-cycle windows with stride 1 within each engine over 21 transformed sensors.
- LSTM input: the full `[30,21]` sequence.
- Classical input: 63 ordered summary features—21 means, 21 population SDs (`ddof=0`), and 21 endpoint-minus-start slopes.
- State explicitly that PCA does not flatten or reconstruct the `30×21` grid.
- Explain endpoint-mode assignment by exact `(engine, end_cycle)` lookup.

### 3.3 Candidate detectors and validation-stage comparison

- Classical families: PCA, LOF, One-Class SVM, and Isolation Forest under P0 and P1/K=6.
- Deep comparator: balanced 64×16 one-layer LSTM autoencoder; convergence seeds 43–45, locked epoch 54; per-seed training-only empirical CDFs.
- LSTM ensemble: arithmetic mean of aligned calibrated scores from the three seeds.
- Model-selection ranking objective: mean validation PR-AUC across three endpoint proxies, then mean ROC-AUC and candidate ID.
- Preserve the negative result that the LSTM ensemble did not exceed LOF/OCSVM in validation ranking.

### 3.4 Frozen PCA reconstruction score and calibration

- P1/K=6 PCA uses `n_components=0.90` after validation selection.
- Fit a feature `StandardScaler` and PCA on the 5,037 eligible training summary vectors.
- Define raw score as mean squared residual between standardized 63-feature vector and its PCA reconstruction.
- Define empirical-CDF calibration from eligible training scores and caution that it is a percentile, not a failure probability.

### 3.5 Frozen thresholds and temporal alert state

- Fit six q=0.995 thresholds to calibrated eligible-training scores, using `method="higher"` and endpoint mode context.
- Runtime order: calibrated score → EWMA alpha 0.20 → strict comparison with the current endpoint-mode threshold → consecutive-violation counter → active alert at count 8.
- State initialization and resets: first score initializes a segment; reset across engines or endpoint gaps; no reset on mode change; no backdating.
- Define contiguous active alert events.

### 3.6 Local sensor attribution and delivery boundary

- Define the exact contribution for each sensor as its mean/std/slope squared standardized residuals summed and divided by 63.
- State the completeness property: 21 contributions sum to raw PCA MSE.
- Label it local, observational, normalized-feature-space model fidelity; not SHAP, physical localization, root cause, or causality.
- Describe the hash-checked transform-only batch implementation as a delivery capability; streaming remains pending.
- Decide with the author whether this subsection belongs in the main text or an implementation appendix.

## 4. Performance evaluation

### 4.1 Evaluation populations

- Training fit: 5,037 eligible windows, 156 engines.
- Validation selection: 9,365 windows, 52 engines.
- Confirmatory internal held-out: 9,271 windows, 52 engines.
- Describe all results with split and proxy labels attached.

### 4.2 Ranking metrics

- Define PR-AUC and ROC-AUC over window endpoint labels and calibrated scores.
- State that both are threshold-free pooled-window ranking metrics and neither is accuracy.
- Report each proxy separately.

### 4.3 Endpoint FAR

- Define FAR/1,000 as `FP active endpoints / proxy-healthy endpoints × 1,000`.
- Define FAR % as the same ratio ×100.
- Distinguish it from false-alert events per 1,000 healthy endpoints and the percentage of engines with any healthy false alert.
- State that no rate per engine-hour or operating hour was implemented.

### 4.4 Engine coverage and missed detections

- Define valid detection as the first event whose start is at or after proxy onset.
- Define coverage as detected engines / 52 and missed rate as its complement.
- Explain why a crossing event is not counted as valid post-onset detection.

### 4.5 Delay and lead

- Define per-engine first-alert delay and lead cycles.
- State that proxy-specific delay medians use detected engines only; missed engines are retained in coverage/missed-rate denominators.
- Define the reported aggregate 25 cycles as the median of the three proxy-specific medians (12, 25, 42.5), not a pooled median.
- State that persistence delay is included.

### 4.6 Validation selection objective

- Describe the feasibility screen of no more than 60 FP endpoints per 1,000 healthy endpoints under the worst of the three endpoint proxies.
- Describe the lexicographic objective: minimum coverage, mean coverage, false-alert events, false-alert engines, delay, lead, candidate ID.
- Explain why this operational objective selected PCA although LOF led ranking PR-AUC.

### 4.7 Literature comparison protocol

- Define A/B/C/D comparability and report 0/2/11/7.
- Separate literature results from methodology support.
- Use `NR—not comparable` for FAR when denominator, labels, split, and alert semantics do not match; this applies to every core paper.
- Do not rank unlike metrics or mix RUL regression with alert performance.

## 5. Results and discussion

### 5.1 Validation-stage detector findings

- Present the five P1 score sources' mean validation PR-AUC and ROC-AUC only in a clearly labeled validation figure/table.
- Report that LOF and OCSVM led mean PR-AUC; the LSTM ensemble improved on its individual seeds but did not lead the registered ranking comparison.
- Preserve the zero-alert/zero-detection LOF and Isolation Forest alert-policy results as negative operational findings.
- Explain that PCA became primary under the later operational alert-policy objective, not the earlier ranking objective.

### 5.2 Frozen internal held-out PCA result

- Present the complete three-row frozen result table:
  - Final 10%: FAR/1,000 32.440; FAR 3.2440%; coverage 51.92%; median delay 12; PR-AUC 0.60267; ROC-AUC 0.94762.
  - Final 20%: FAR/1,000 9.443; FAR 0.9443%; coverage 78.85%; median delay 25; PR-AUC 0.80974; ROC-AUC 0.92673.
  - Final 30%: FAR/1,000 5.153; FAR 0.5153%; coverage 84.62%; median delay 42.5; PR-AUC 0.82745; ROC-AUC 0.86758.
- Accompany rounded values with numerator/denominator counts where space permits.
- State that the FAR objective was achieved across all proxies, whereas aggregate delay was 25 cycles and missed the ≤12-cycle aspiration.

### 5.3 Proxy sensitivity and trade-offs

- Discuss the pattern without calling one proxy more correct: later onset definitions reduce the pre-onset region in which endpoint false positives can occur, increase the post-onset detection opportunity, and change class balance.
- Note the observed combination of falling FAR, rising coverage, later median delay, rising PR-AUC, and falling ROC-AUC across the three proxies.
- Do not offer a causal explanation not tested by the protocol.
- Use this variation to argue for reporting multiple explicit proxy assumptions rather than one headline number.

### 5.4 PCA and frozen LSTM comparator

- If included, report the registered held-out trade-off only with the audit-approved wording: PCA had lower FAR but lower coverage and later median alerts than the LSTM comparator on each endpoint proxy.
- Do not label either model globally superior.
- Do not infer fusion benefit from pairwise complementarity; no score or decision fusion was evaluated.

### 5.5 Comparison with literature

- State that no Category A comparator exists in the core set.
- Discuss LIT-013 (`core013`) as the closest partial comparator with explicit protocol mismatch.
- Use the remaining studies to locate methodological choices—condition normalization, reconstruction, thresholds, event metrics, and attribution—not to construct an incompatible numerical ranking.
- Include project FAR in the project rows; use `NR—not comparable` for literature FAR and give the mismatch reason.

### 5.6 Strengths

- Whole-engine separation and recorded split identities.
- Training-only learned state and frozen pre-access choices.
- Separation of fitting assumptions from evaluation proxies.
- Negative-result retention and exact metric denominators.
- First-valid-run acceptance and independent verification.
- Reproducible code/protocol linkage and narrow attribution completeness.

### 5.7 Limitations and threats to validity

- One simulated FD002 fleet and one fixed split.
- Proxy onsets rather than physical onset annotations.
- One internal confirmatory partition; no official NASA-test or external dataset result.
- Pooled-window PR-AUC/ROC-AUC and no engine-bootstrap uncertainty.
- Missed detections excluded from delay medians but exposed through coverage.
- No protocol-equivalent literature comparator.
- No evaluated fusion, causal explanation, physical localization, online recalibration, streaming state, or field deployment.
- Raw data/model artifacts remain local/ignored and there is no dependency lockfile.

## 6. Conclusion and future work

### 6.1 Conclusion

- Restate the governed system contribution, not component novelty.
- Summarize the proxy-dependent held-out result as a set, not a cherry-picked value.
- State both outcomes: FAR target met for all three proxies; 25-cycle aggregate delay aspiration missed.
- Reassert internal held-out proxy and non-production boundaries.

### 6.2 Future work

- Engine-level bootstrap uncertainty and failure analysis under a new preregistered protocol.
- Separate official NASA-test trajectory-generalization study with the already frozen detector; it would remain an RUL/proxy evaluation, not physical-onset validation.
- External datasets or real-engine validation.
- Any fusion study only under new registration, with no alteration of the frozen result.
- Streaming state serialization and monitoring only after separate implementation/evaluation governance.
- Attribution stability and domain validation without upgrading it to causal localization.

## References

- Use only verified keys from `docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib` for the core literature.
- Preserve the 20 registered identities and keys listed in `EVIDENCE_MAP.md`.
- Add dataset/software citations only after author review and exact source verification; do not invent metadata.
- Format references only after the venue is selected.

## Alignment with the project guide

This outline follows the guide's conceptual sequence while using the user-requested manuscript headings:

| Guide content | Manuscript destination |
|---|---|
| Problem, FD002 contents, and evidence language (§§1–3) | Introduction; Dataset and experimental protocol |
| Validated pipeline, shapes, and module contracts (§§4–7) | Proposed methodology |
| P0/P1 contrast, healthy fitting, reconstruction, metrics, and alert state (§§8–12) | Proposed methodology; Performance evaluation |
| Verified findings and evidence boundaries (§13) | Results and discussion |
| Incomplete items, safety boundaries, and frozen delivery layer (§§14, 22–23) | Limitations; Conclusion and future work |

Where the guide contains historical wording, this outline follows its own stated precedence rule: current registered configs, implementation, tests, and result authorities outrank stale prose. Specifically, Phase 5 and confirmatory evaluation are complete; PCA attribution and batch inference are implemented; only their bounded evidence claims are carried forward.
