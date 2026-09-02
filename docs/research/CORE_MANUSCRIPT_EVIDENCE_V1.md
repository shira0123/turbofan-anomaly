# Core Manuscript Evidence V1

This focused derivative records complete-methods inspection for 20 core papers selected under the preregistered protocol. It does not imply that all 100 matrix papers received this depth of extraction.

Protocol: `configs/research/fd002-core-literature-extraction-protocol-v1.json` (raw SHA-256 `04528f3a8a289b9896bf27f7885c1edaf16e3890804a1f730eef326caedad71f`). Registered in commit `9136263` before new numerical extraction.

> No directly protocol-equivalent published comparator was identified in the manuscript-grade core literature set.

## Scope and replacement

The initial set contained `LIT-019`. Its publisher metadata and abstract were accessible, but a legal complete manuscript exposing the full methodology, results, and limitations was not located. In accordance with the fixed reserve order, `LIT-051` replaced it. No replacement was selected based on results.

## Frozen project metrics

Project values below are copied from `configs/evaluation/fd002-confirmatory-results-v1.json`; no project data were opened and no metric was recalculated.

| Proxy | FAR/1,000 | FAR % | Coverage % | Median delay | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Final 10% | 32.440 | 3.2440 | 51.92 | 12 | 0.60267 | 0.94762 |
| Final 20% | 9.443 | 0.9443 | 78.85 | 25 | 0.80974 | 0.92673 |
| Final 30% | 5.153 | 0.5153 | 84.62 | 42.5 | 0.82745 | 0.86758 |

Aggregate median held-out delay is 25 cycles. All three FAR objectives were met; the aggregate ≤12-cycle delay aspiration was not met. These are internal held-out proxy-labelled results, not official NASA-test, physical-onset, or field results.

## Core-paper register

| ID | Year | Dataset/subset | Task | Learning | Access | Category | Direct? |
|---|---:|---|---|---|---|:---:|:---:|
| LIT-010 | 2024 | NASA C-MAPSS / FD002 | key-point anomaly/degradation analysis and RUL planning | analytical/statistical; not healthy-only learning | publisher_full_text_verified | B | no |
| LIT-013 | 2026 | NASA C-MAPSS / FD001, FD002, FD003, FD004 | early fault detection | unsupervised healthy-only reconstruction | author_manuscript_verified | B | no |
| LIT-007 | 2020 | NASA C-MAPSS / FD004 | anomaly detection | semi-supervised healthy-only autoencoder | publisher_full_text_verified | C | no |
| LIT-008 | 2019 | NASA C-MAPSS / FD004 | change-point detection | one-class unsupervised with heuristic calibration | arxiv_full_text_verified | C | no |
| LIT-009 | 2024 | NASA C-MAPSS / FD001-FD004; emphasis FD002/FD004 | change-point detection integrated with RUL estimation | unsupervised change point plus supervised LSTM RUL | arxiv_full_text_verified | C | no |
| LIT-012 | 2025 | NASA C-MAPSS / FD001 and FD003 | anomaly detection | unsupervised autoencoder representation with proxy labels for evaluation | arxiv_full_text_verified | C | no |
| LIT-014 | 2025 | real jet-engine test-cell time series / not C-MAPSS | unsupervised anomaly detection | unsupervised healthy-only | publisher_full_text_verified | D | no |
| LIT-017 | 2024 | real gas-turbine vibration spectra / not C-MAPSS | anomaly detection | unsupervised reconstruction | publisher_full_text_verified | D | no |
| LIT-018 | 2023 | NASA C-MAPSS / FD001-FD004; FD002/FD004 emphasized | remaining useful life prediction | supervised RUL with informed loss | publisher_full_text_verified | C | no |
| LIT-021 | 2021 | C-MAPSS turbofan simulator and dynamic-regime case studies / C-MAPSS/PHM prognostics; exact FD00x mapping varies by experiment | baselining for prognostics | unsupervised regime discovery plus supervised normalization | institutional_repository_verified | C | no |
| LIT-006 | 2016 | NASA C-MAPSS turbofan plus milling and industrial pulverizer / single-condition 100-train/100-test C-MAPSS set (FD001-equivalent) | health-index construction and RUL estimation | unsupervised healthy reconstruction followed by similarity-based RUL | arxiv_full_text_verified | C | no |
| LIT-003 | 2014 | NASA C-MAPSS benchmark family / all C-MAPSS/PHM08 datasets | benchmarking and review | methodological review | publisher_full_text_verified | C | no |
| LIT-004 | 2014 | NASA C-MAPSS benchmark family / all C-MAPSS datasets | prognostic-method review | methodological review | institutional_repository_verified | C | no |
| LIT-001 | 2008 | C-MAPSS simulator-generated engine trajectories / dataset-generation foundation rather than FD001-FD004 evaluation | damage-propagation simulation | physics/simulation model | institutional_repository_verified | C | no |
| LIT-005 | 2016 | five public/industrial multivariate datasets / not C-MAPSS FD002 | multisensor anomaly detection | unsupervised/semi-supervised normal-only reconstruction | arxiv_full_text_verified | D | no |
| LIT-026 | 2018 | NASA SMAP and MSL telemetry / not C-MAPSS | spacecraft telemetry anomaly detection | sequence prediction plus unsupervised dynamic threshold | arxiv_full_text_verified | D | no |
| LIT-034 | 2022 | multivariate cyber-physical-system benchmarks / not C-MAPSS | anomaly detection and diagnosis evaluation | unsupervised and semi-supervised methods | arxiv_full_text_verified | D | no |
| LIT-036 | 2022 | time-series anomaly benchmarks / not C-MAPSS | evaluation methodology | method-independent evaluation | publisher_full_text_verified | D | no |
| LIT-055 | 2016 | NASA electromechanical-actuator flight/test data / not C-MAPSS | anomaly detection and fault disambiguation | unsupervised nominal-data autoencoder | publisher_full_text_verified | D | no |
| LIT-051 | 2024 | real piston aero-engine ECU time series / not C-MAPSS | aero-engine fault detection | unsupervised normal-only reconstruction | publisher_full_text_verified | C | no |

## Verified numerical evidence

Every value below comes from an inspected full text. None is directly comparable with the frozen project result.

| Value ID | Paper | Subset | Metric | Value | Scope | Location |
|---|---|---|---|---:|---|---|
| LIT-013-V01 | LIT-013 | FD001 | precision | 0.196 | test_proxy | p. 9, VI Results, Table 3, row FD001, column Precision |
| LIT-013-V02 | LIT-013 | FD001 | recall | 0.981 | test_proxy | p. 9, VI Results, Table 3, row FD001, column Recall (Sensitivity) |
| LIT-013-V03 | LIT-013 | FD001 | specificity | 0.966 | test_proxy | p. 9, VI Results, Table 3, row FD001, column Specificity |
| LIT-013-V04 | LIT-013 | FD001 | f1 | 0.327 | test_proxy | p. 9, VI Results, Table 3, row FD001, column F1-score |
| LIT-013-V05 | LIT-013 | FD001 | anomaly_fraction | 0.008 | test_proxy | p. 9, VI Results, Table 3, row FD001, column Anomaly% |
| LIT-013-V06 | LIT-013 | FD002 | precision | 0.374 | test_proxy | p. 9, VI Results, Table 3, row FD002, column Precision |
| LIT-013-V07 | LIT-013 | FD002 | recall | 0.799 | test_proxy | p. 9, VI Results, Table 3, row FD002, column Recall (Sensitivity) |
| LIT-013-V08 | LIT-013 | FD002 | specificity | 0.982 | test_proxy | p. 9, VI Results, Table 3, row FD002, column Specificity |
| LIT-013-V09 | LIT-013 | FD002 | f1 | 0.51 | test_proxy | p. 9, VI Results, Table 3, row FD002, column F1-score |
| LIT-013-V10 | LIT-013 | FD002 | anomaly_fraction | 0.013 | test_proxy | p. 9, VI Results, Table 3, row FD002, column Anomaly% |
| LIT-013-V11 | LIT-013 | FD003 | precision | 0.241 | test_proxy | p. 9, VI Results, Table 3, row FD003, column Precision |
| LIT-013-V12 | LIT-013 | FD003 | recall | 1.0 | test_proxy | p. 9, VI Results, Table 3, row FD003, column Recall (Sensitivity) |
| LIT-013-V13 | LIT-013 | FD003 | specificity | 0.963 | test_proxy | p. 9, VI Results, Table 3, row FD003, column Specificity |
| LIT-013-V14 | LIT-013 | FD003 | f1 | 0.388 | test_proxy | p. 9, VI Results, Table 3, row FD003, column F1-score |
| LIT-013-V15 | LIT-013 | FD003 | anomaly_fraction | 0.012 | test_proxy | p. 9, VI Results, Table 3, row FD003, column Anomaly% |
| LIT-013-V16 | LIT-013 | FD004 | precision | 0.336 | test_proxy | p. 9, VI Results, Table 3, row FD004, column Precision |
| LIT-013-V17 | LIT-013 | FD004 | recall | 0.725 | test_proxy | p. 9, VI Results, Table 3, row FD004, column Recall (Sensitivity) |
| LIT-013-V18 | LIT-013 | FD004 | specificity | 0.985 | test_proxy | p. 9, VI Results, Table 3, row FD004, column Specificity |
| LIT-013-V19 | LIT-013 | FD004 | f1 | 0.456 | test_proxy | p. 9, VI Results, Table 3, row FD004, column F1-score |
| LIT-013-V20 | LIT-013 | FD004 | anomaly_fraction | 0.011 | test_proxy | p. 9, VI Results, Table 3, row FD004, column Anomaly% |
| LIT-012-V01 | LIT-012 | FD001 | accuracy | 0.9649 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column Accuracy |
| LIT-012-V02 | LIT-012 | FD001 | precision | 0.9595 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column Precision |
| LIT-012-V03 | LIT-012 | FD001 | recall | 0.9518 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column Recall |
| LIT-012-V04 | LIT-012 | FD001 | f1 | 0.9556 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column F1 |
| LIT-012-V05 | LIT-012 | FD001 | correct_detection_rate | 1.0 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column CDR |
| LIT-012-V06 | LIT-012 | FD003 | accuracy | 0.9484 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column Accuracy |
| LIT-012-V07 | LIT-012 | FD003 | precision | 0.9381 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column Precision |
| LIT-012-V08 | LIT-012 | FD003 | recall | 0.9316 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column Recall |
| LIT-012-V09 | LIT-012 | FD003 | f1 | 0.9349 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column F1 |
| LIT-012-V10 | LIT-012 | FD003 | correct_detection_rate | 1.0 | test_proxy | p. 7, IV-B C-MAPSS, Table II, row TDC-AE, column CDR |
| LIT-007-V01 | LIT-007 | FD004 | f1 | 0.892 | test_proxy | p. 47, IV Results, Table VI, row without feature removal, column F1-score |
| LIT-007-V02 | LIT-007 | FD004 | precision | 0.896 | test_proxy | p. 47, IV Results, Table VI, row without feature removal, column Precision |
| LIT-007-V03 | LIT-007 | FD004 | recall | 0.724 | test_proxy | p. 47, IV Results, Table VI, row without feature removal, column Recall |
| LIT-006-V01 | LIT-006 | FD001-equivalent C-MAPSS | timeliness_score | 256 | official_test_rul | p. 7, 6.2.2 Results, Table 1, row LR-ED2, column S |
| LIT-006-V02 | LIT-006 | FD001-equivalent C-MAPSS | accuracy | 0.67 | official_test_rul | p. 7, 6.2.2 Results, Table 1, row LR-ED2, column A(%) |
| LIT-006-V03 | LIT-006 | FD001-equivalent C-MAPSS | mae_cycles | 10 | official_test_rul | p. 7, 6.2.2 Results, Table 1, row LR-ED2, column MAE |
| LIT-006-V04 | LIT-006 | FD001-equivalent C-MAPSS | mse_cycles_squared | 164 | official_test_rul | p. 7, 6.2.2 Results, Table 1, row LR-ED2, column MSE |
| LIT-006-V05 | LIT-006 | FD001-equivalent C-MAPSS | mape_1 | 0.18 | official_test_rul | p. 7, 6.2.2 Results, Table 1, row LR-ED2, column MAPE1(%) |
| LIT-006-V06 | LIT-006 | FD001-equivalent C-MAPSS | mape_2 | 0.05 | official_test_rul | p. 7, 6.2.2 Results, Table 1, row LR-ED2, column MAPE2(%) |
| LIT-006-V07 | LIT-006 | FD001-equivalent C-MAPSS | false_positive_rate | 0.13 | official_test_rul | p. 7, 6.2.2 Results, Table 1, row LR-ED2, column FPR(%) |
| LIT-006-V08 | LIT-006 | FD001-equivalent C-MAPSS | false_negative_rate | 0.2 | official_test_rul | p. 7, 6.2.2 Results, Table 1, row LR-ED2, column FNR(%) |
| LIT-055-V01 | LIT-055 | NASA electromechanical-actuator scenarios | fault_detection_rate | 0.978 | test | p. 1, Abstract; results sections, Abstract and scenario results, row deep autoencoder, column detection rate |
| LIT-055-V02 | LIT-055 | NASA electromechanical-actuator scenarios | false_alarms | 0 | test | p. 1, Abstract; results sections, Abstract and scenario results, row deep autoencoder, column false alarms |

## Paper-level extraction

### LIT-010 — Anomaly Detection and Remaining Useful Life Prediction for Turbofan Engines with a Key Point-Based Approach to Secure Health Management

**Identity.** Yuntao Duan; Tao Zhang; Dunhuang Shi. 2024. Sensors 24(24), 8022. DOI/stable identity: `10.3390/s24248022` / `OpenAlex:W4405458612`. Source: https://mdpi-res.com/d_attachment/sensors/sensors-24-08022/article_deploy/sensors-24-08022.pdf?version=1734343852 (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `bf0d6aa9698b435f58ced8186844acbcc4ad38e767c430a2353b64f7219a3b44`; `version_of_record`).

**Dataset and task.** NASA C-MAPSS; subset `FD002`; engines `260`. Task: key-point anomaly/degradation analysis and RUL planning; target: two lifecycle key points and remaining-life planning; status: analytical/statistical; not healthy-only learning. Healthy definition: NR; method transforms complete trajectories. Onset: two key points obtained by self-convolution, halving, and derivatives; not mapped to this project's normalized-life proxies. RUL: key-point-derived remaining-life construction. Window/evaluation: full trajectory / cycle and engine.

**Method.** Split: FD002 lifecycle analysis; the paper's 'test set' identity is not explicit enough to equate with NASA official test Engine-disjoint: `NR`; same-engine window crossing: `NR`. Preprocessing/scaling: feature fusion, self-convolution, half operation, derivative operation / NR. Condition treatment: FD002 operating conditions are present but no endpoint-mode six-regime policy matching this project Clustering: NR. Model: non-neural key-point method. Calibration/threshold/smoothing/persistence: NR / key-point rules / NR / NR. Explanation: key-point positions. NASA-file declaration: `{"train_FD002": true, "test_FD002": "NR", "RUL_FD002": "NR"}`.

**Use and limits.** Closest FD002 anomaly/degradation context Citation role: related-work discussion of FD002 key-point alternatives. Authors' limits: future work is needed for broader application and more complex conditions Protocol audit: No compatible engine-disjoint proxy-alert evaluation, FAR, coverage, persistence, or delay semantics Category **B**; direct comparison: **no**. Caveat: FD002 aligns, but task, labels, split identity, threshold/event semantics, and metrics do not.

### LIT-013 — Early Fault Detection on CMAPSS with Unsupervised LSTM Autoencoders

**Identity.** Pablo Sanchez Gallego; Karen Tatiana Reyes Mina; Bianca Elena Radu; Eugenio Jose Fernandez Vicente. 2026. arXiv preprint / Universidad de Alcala author manuscript. DOI/stable identity: `10.48550/arXiv.2601.10269` / `arXiv:2601.10269`. Source: https://ebuah.uah.es/xmlui/bitstream/handle/10017/68237/early_sanchez_UAH_IA3_2026.pdf?isAllowed=y&sequence=3 (accessed 2026-09-03; `author_manuscript_verified`; SHA-256 `df38ad3e78089207ceabee3c1f502dc8757ea44d67b3c74d4bb1663a18a7948c`; `institutional_author_manuscript`).

**Dataset and task.** NASA C-MAPSS; subset `FD001, FD002, FD003, FD004`; engines `100/260/100/249 run-to-failure engines`. Task: early fault detection; target: window anomaly label; status: unsupervised healthy-only reconstruction. Healthy definition: first 85% of each trajectory, with 20% of healthy windows used for validation. Onset: final 10% of each trajectory is anomalous; middle 5% is excluded. RUL: not a RUL regression target. Window/evaluation: sequence windows; exact length reported in manuscript architecture section / window.

**Method.** Split: within-trajectory 85% baseline, 5% exclusion, 10% degraded test; random healthy windows form validation Engine-disjoint: `False`; same-engine window crossing: `True`. Preprocessing/scaling: regression-based operating-condition normalization before sequence construction / regression residual normalization. Condition treatment: operating settings regressed out; residual effects remain in FD002/FD004 Clustering: no endpoint K=6 clustering. Model: LSTM autoencoder with four-dimensional latent representation. Calibration/threshold/smoothing/persistence: threshold derived from held-out healthy windows / adaptive reconstruction-error threshold / none beyond persistence / five consecutive over-threshold windows. Explanation: reconstruction error; no sensor-level decomposition. NASA-file declaration: `{"train_FD002": true, "test_FD002": false, "RUL_FD002": false}`.

**Use and limits.** Strongest partial unsupervised FD002 anomaly comparator Citation role: motivation and bounded comparison of unsupervised LSTM reconstruction. Authors' limits: 85/15 boundary is heuristic; load changes and glitches cause false positives; residual condition effects remain; simulator-to-flight gap Protocol audit: Same-engine windows cross development partitions, anomaly proxy differs, and official held-out engines are not used Category **B**; direct comparison: **no**. Caveat: Same FD002 and anomaly intent, but non-engine-disjoint within-trajectory split, different proxy, threshold, persistence, and point metrics prohibit direct comparison.

### LIT-007 — Autoencoder based Semi-Supervised Anomaly Detection in Turbofan Engines

**Identity.** Ali Al Bataineh; Aakif Mairaj; Devinder Kaur. 2020. International Journal of Advanced Computer Science and Applications 11(11). DOI/stable identity: `10.14569/IJACSA.2020.0111105` / `IJACSA:2020.0111105`. Source: https://thesai.org/Downloads/Volume11No11/Paper_5-Autoencoder_based_Semi_Supervised_Anomaly_Detection.pdf (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `ddf4a5084bb5874a55a518d5909db0cd353a5ec30ef18c74035f76ef6ba49155`; `version_of_record`).

**Dataset and task.** NASA C-MAPSS; subset `FD004`; engines `249`. Task: anomaly detection; target: normal versus anomalous cycle; status: semi-supervised healthy-only autoencoder. Healthy definition: first 60% of each selected trajectory treated as normal. Onset: last 5% treated as anomalous; intervening cycles excluded. RUL: not used. Window/evaluation: single-cycle feature vector / cycle.

**Method.** Split: 220 engines train, 20 validation, 19 test from FD004 run-to-failure trajectories Engine-disjoint: `True`; same-engine window crossing: `False`. Preprocessing/scaling: optional redundant-feature removal / feature scaling reported; exact train-only fit scope is not fully explicit. Condition treatment: six-condition FD004 retained without endpoint-mode thresholds Clustering: none. Model: feed-forward autoencoder selected by Bayesian optimization. Calibration/threshold/smoothing/persistence: validation used for architecture selection / reconstruction-error decision threshold / none / point classification. Explanation: global reconstruction error. NASA-file declaration: `{"train_FD004": true, "test_FD004": false, "RUL_FD004": false}`.

**Use and limits.** Healthy-only reconstruction precedent with engine-disjoint evaluation Citation role: contextual anomaly-method comparison. Authors' limits: single simulated subset and proxy labels Protocol audit: FD004 rather than FD002; no alert-event, delay, coverage, or FAR-per-1000 semantics Category **C**; direct comparison: **no**. Caveat: Engine-disjoint anomaly evaluation is useful context, but FD004 has two faults and labels/metrics/alert semantics differ.

### LIT-008 — A One-Class Support Vector Machine Calibration Method for Time Series Change Point Detection

**Identity.** Baihong Jin; Yuxin Chen; Dan Li; Kameshwar Poolla; Alberto Sangiovanni-Vincentelli. 2019. IEEE ICASSP / arXiv. DOI/stable identity: `10.48550/arXiv.1902.06361` / `arXiv:1902.06361`. Source: https://arxiv.org/pdf/1902.06361 (accessed 2026-09-03; `arxiv_full_text_verified`; SHA-256 `df0f01f87243a490395efc5e71f57563cda3db4dac1f886324f4c514e5b721de`; `arxiv_author_version`).

**Dataset and task.** NASA C-MAPSS; subset `FD004`; engines `249`. Task: change-point detection; target: engine-specific degradation transition; status: one-class unsupervised with heuristic calibration. Healthy definition: hypothesized first 50%-100% normal segment per training engine. Onset: transition region benchmarked against WTTE-RNN uncertainty behavior. RUL: RUL available to WTTE-RNN reference, not predicted by OC-SVM. Window/evaluation: single cycles / engine change point.

**Method.** Split: 20 randomly selected engines train; remaining 229 test Engine-disjoint: `True`; same-engine window crossing: `False`. Preprocessing/scaling: 21 sensor readings; RBF representation / NR. Condition treatment: FD004 six conditions are pooled; no per-mode normalization Clustering: none. Model: RBF OC-SVM with differential-evolution calibration. Calibration/threshold/smoothing/persistence: joint search over gamma and engine-specific normal fraction with nu fixed at 0.05 / OC-SVM decision plus minimum cross-entropy change point / implicit persistence: latest permanent threshold breach in reference interpretation / one change point per engine. Explanation: none. NASA-file declaration: `{"train_FD004": true, "test_FD004": false, "RUL_FD004": false}`.

**Use and limits.** One-class calibration and learned-onset precedent Citation role: context for onset ambiguity and classical controls. Authors' limits: authors call for testing other heuristic optimizers Protocol audit: Pseudo-ground truth is another model, subset is FD004, and no point/event false-alert metrics are reported Category **C**; direct comparison: **no**. Caveat: Change-point objective and model-derived reference are not equivalent to this project's proxy endpoint alerts.

### LIT-009 — A Change Point Detection Integrated Remaining Useful Life Estimation Model under Variable Operating Conditions

**Identity.** Anushiya Arunan; Yan Qin; Xiaoli Li; Chau Yuen. 2024. Control Engineering Practice 144, 105840. DOI/stable identity: `10.1016/j.conengprac.2023.105840` / `arXiv:2401.04351`. Source: https://arxiv.org/pdf/2401.04351 (accessed 2026-09-03; `arxiv_full_text_verified`; SHA-256 `4da3c61605c235ed643363cf79cc7e2e63b61e5665ba702f84e195cb1a62ffbf`; `accepted_manuscript_arxiv`).

**Dataset and task.** NASA C-MAPSS; subset `FD001-FD004; emphasis FD002/FD004`; engines `train/test counts follow canonical subsets`. Task: change-point detection integrated with RUL estimation; target: official-test last-cycle RUL; status: unsupervised change point plus supervised LSTM RUL. Healthy definition: normal-operation segment selected from long-lived training engines. Onset: earlier of persistent T2 and Q control-limit breaches. RUL: piecewise linear after engine-specific change point; official test capped at 130 cycles. Window/evaluation: sliding sequence, L selected by dataset / engine terminal RUL for official test; cycle-level change point on complete train trajectories.

**Method.** Split: training engines support change-point model and RUL training; official test engines evaluate RUL Engine-disjoint: `True`; same-engine window crossing: `False`. Preprocessing/scaling: sensor exclusions; canonical variate analysis temporal features / change-point-informed piecewise standardization. Condition treatment: explicitly targets variable operating conditions Clustering: no K=6 endpoint clustering. Model: CVA monitoring statistics plus LSTM RUL regressor. Calibration/threshold/smoothing/persistence: 99% confidence control limits and hyperparameter search on training/development data / T2/Q control limits / persistent permanent breach / earlier permanent breach selected as event. Explanation: monitoring-statistic trajectories. NASA-file declaration: `{"train_FD002": true, "test_FD002": true, "RUL_FD002": true}`.

**Use and limits.** Operating-condition and learned-change-point context Citation role: official-test protocol and onset discussion. Authors' limits: linear post-change RUL assumption and fixed 130-cycle cap for test labels Protocol audit: RUL endpoint results do not evaluate alert FAR, coverage, or delay; onset is model-derived Category **C**; direct comparison: **no**. Caveat: Uses FD002 official test, but evaluates last-cycle RUL regression rather than anomaly alerts over all observed cycles.

### LIT-012 — Anomaly Detection in Complex Dynamical Systems: A Systematic Framework Using Embedding Theory and Physics-Inspired Consistency

**Identity.** Michael Somma; Thomas Gallien; Branka Stojanovic. 2025. arXiv preprint. DOI/stable identity: `10.48550/arXiv.2502.19307` / `arXiv:2502.19307v3`. Source: https://arxiv.org/pdf/2502.19307v3 (accessed 2026-09-03; `arxiv_full_text_verified`; SHA-256 `0476b7d4fb1ceb5ce5c1d2cc04c20f2beb31dd928e6be8ebf5f13cb8bb647dad`; `arxiv_v3`).

**Dataset and task.** NASA C-MAPSS; subset `FD001 and FD003`; engines `200`. Task: anomaly detection; target: normal versus anomalous cycle; status: unsupervised autoencoder representation with proxy labels for evaluation. Healthy definition: first 60% of each run-to-failure trajectory. Onset: final 40% of trajectory. RUL: not used. Window/evaluation: embedded state-derivative sample / cycle.

**Method.** Split: 80/20 engine-disjoint outer split; 90/10 training-engine development split Engine-disjoint: `True`; same-engine window crossing: `False`. Preprocessing/scaling: state-derivative embedding / reported normalization. Condition treatment: single-condition subsets only Clustering: none. Model: Temporal Differential Consistency Autoencoder. Calibration/threshold/smoothing/persistence: threshold uses anomalous portion of training trajectories / reconstruction score threshold optimized with proxy labels / none / point classification. Explanation: latent temporal-consistency/reconstruction behavior. NASA-file declaration: `{"train_FD001_FD003": true, "official_test": false, "RUL_files": false}`.

**Use and limits.** Physics-inspired temporal reconstruction comparison Citation role: contextual efficient-autoencoder result. Authors' limits: limited to FD001/FD003 and heuristic 60/40 labels Protocol audit: Threshold uses proxy-anomalous training data and subsets/labels differ Category **C**; direct comparison: **no**. Caveat: Engine split is useful, but subset, 60/40 onset, threshold supervision, and point metrics differ.

### LIT-014 — RAVEN: Unsupervised Anomaly Detection in Multivariate Jet Engine Time Series using Residual Learning on Real Test Data

**Identity.** Nouf Almesafri; Mohamed Ragab; Salama AlMheiri; Zahi Mohamed; Abdulla Alseiari. 2025. PHM Society Asia-Pacific Conference 5(1). DOI/stable identity: `10.36001/phmap.2025.v5i1.4647` / `PHMAP:4647`. Source: https://papers.phmsociety.org/index.php/phmap/article/download/4647/phmap_25_4647 (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `a48be532271c17727ef1157bd84451c2cc086150c7201a9ea178317993ea2330`; `version_of_record`).

**Dataset and task.** real jet-engine test-cell time series; subset `not C-MAPSS`; engines `NR`. Task: unsupervised anomaly detection; target: anomalous event under real test conditions; status: unsupervised healthy-only. Healthy definition: nominal real-engine periods. Onset: test-defined anomalous periods; exact physical onset provenance is experiment-specific. RUL: not used. Window/evaluation: multivariate sequences / cycle/time point and event.

**Method.** Split: real test programs split into nominal training and evaluation sequences Engine-disjoint: `NR`; same-engine window crossing: `False`. Preprocessing/scaling: regression residualization against operating variables / residual normalization. Condition treatment: operating-regime effects removed by regression Clustering: none. Model: residual model plus deep LSTM autoencoder. Calibration/threshold/smoothing/persistence: nominal reconstruction-error distribution / reported reconstruction-error threshold / NR / event-level interpretation described. Explanation: reconstruction residual patterns. NASA-file declaration: `{"nasa_cmapss_files": false}`.

**Use and limits.** Supports residualization before LSTM reconstruction Citation role: methodological evidence for operating-effect removal. Authors' limits: single real-engine test campaign and limited fault diversity Protocol audit: Different hardware/data/labels; exact split and event metrics do not match FD002 proxies Category **D**; direct comparison: **no**. Caveat: Real-engine relevance is high but dataset, faults, units, labels, and metrics are not protocol-equivalent.

### LIT-017 — Gas Turbine Anomaly Detection under Time-Varying Operation Conditions Based on Spectra Alignment and Self-Adaptive Normalization

**Identity.** Dongyan Miao; Kun Feng; Yuan Xiao; Zhouzheng Li; Jinji Gao. 2024. Sensors 24(3), 941. DOI/stable identity: `10.3390/s24030941` / `PMCID:PMC10856833`. Source: https://mdpi-res.com/d_attachment/sensors/sensors-24-00941/article_deploy/sensors-24-00941.pdf (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `74dce23628e85d7405ed60ed77ef8621877e49a6dd20b576995d02adcccba2f9`; `version_of_record`).

**Dataset and task.** real gas-turbine vibration spectra; subset `not C-MAPSS`; engines `one real turbine test campaign`. Task: anomaly detection; target: foreign-object-damage anomaly index; status: unsupervised reconstruction. Healthy definition: normal spectra across speeds. Onset: experiment fault interval. RUL: not used. Window/evaluation: spectrum sample / spectrum/time point.

**Method.** Split: normal training/validation and FOD evaluation sequences Engine-disjoint: `NR`; same-engine window crossing: `False`. Preprocessing/scaling: rotational-speed spectral alignment and adaptive amplitude normalization / self-adaptive global normalization. Condition treatment: speed-aligned spectra and category-adjusted anomaly index Clustering: k-means on rotational speed when manual modes unavailable. Model: degressive-beta variational autoencoder. Calibration/threshold/smoothing/persistence: per-category validation MSE mean/std / multi-category anomaly index / none / point-level anomaly sequence. Explanation: spectrum/reconstruction behavior. NASA-file declaration: `{"nasa_cmapss_files": false}`.

**Use and limits.** Supports condition-aware normalization before reconstruction Citation role: methodological operating-condition citation. Authors' limits: rotational speed is not a complete operating-condition descriptor; broader faults needed Protocol audit: Different sensing modality, physical system, labels, and metrics Category **D**; direct comparison: **no**. Caveat: Methodological analogue only; no C-MAPSS or matching alert protocol.

### LIT-018 — Multiform Informed Machine Learning Based on Piecewise and Weibull for Engine Remaining Useful Life Prediction

**Identity.** Shuang Zhou; Yunan Yao; Aihua Liu; Fan Wang; Lu Chen; Ruolan Xiong. 2023. Sensors 23(12), 5669. DOI/stable identity: `10.3390/s23125669` / `PMCID:PMC10302399`. Source: https://mdpi-res.com/d_attachment/sensors/sensors-23-05669/article_deploy/sensors-23-05669-v2.pdf?version=1687139904 (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `dee9760c4e0b28f5a53ddfcf7271ac76a1a872b4436887f00773c736df224fc5`; `version_of_record_updated`).

**Dataset and task.** NASA C-MAPSS; subset `FD001-FD004; FD002/FD004 emphasized`; engines `canonical train/test engine counts`. Task: remaining useful life prediction; target: official-test terminal RUL; status: supervised RUL with informed loss. Healthy definition: not applicable. Onset: piecewise RUL knee is imposed/selected rather than observed fault onset. RUL: piecewise capped RUL plus Weibull-informed loss. Window/evaluation: reported sequence construction / engine terminal RUL.

**Method.** Split: canonical train/test split; experiments repeated 15 times Engine-disjoint: `True`; same-engine window crossing: `False`. Preprocessing/scaling: sensor filtering and sequence construction / k-means operating-condition grouping followed by per-condition normalization. Condition treatment: explicit multi-condition normalization Clustering: k-means. Model: neural RUL regressor with Piecewise and Weibull knowledge. Calibration/threshold/smoothing/persistence: model/hyperparameter selection reported / not an anomaly threshold / none / last-cycle RUL evaluation. Explanation: model/loss interpretability, not anomaly attribution. NASA-file declaration: `{"train_FD002": true, "test_FD002": true, "RUL_FD002": true}`.

**Use and limits.** FD002 regime-scaling and official-test RUL context Citation role: official-test methodological assessment. Authors' limits: domain assumptions may not transfer; knowledge parameters require care Protocol audit: RUL task and terminal evaluation cannot be compared to anomaly FAR/coverage/delay Category **C**; direct comparison: **no**. Caveat: FD002 aligns, but supervised last-cycle RUL RMSE/score is a different target and evaluation unit.

### LIT-021 — A Self-Organizing Map and a Normalizing Multi-Layer Perceptron Approach to Baselining in Prognostics under Dynamic Regimes

**Identity.** Marcia Lourenco Baptista; Elsa M. P. Henriques; Kai Goebel. 2021. Neurocomputing 456, 268-287. DOI/stable identity: `10.1016/j.neucom.2021.05.031` / `TU Delft uuid:734ff2a9-fd15-4a8c-bacf-764453717bf9`. Source: https://repository.tudelft.nl/file/File_8b0f3f08-774f-4c5b-b491-0535f3de5aff (accessed 2026-09-03; `institutional_repository_verified`; SHA-256 `22443b875a18c5cfe765a18c5287d7718c68565503ce58fb1ba27e99ce9bd1e2`; `final_published_version_repository_copy`).

**Dataset and task.** C-MAPSS turbofan simulator and dynamic-regime case studies; subset `C-MAPSS/PHM prognostics; exact FD00x mapping varies by experiment`; engines `NR`. Task: baselining for prognostics; target: condition-normalized sensor trajectories; status: unsupervised regime discovery plus supervised normalization. Healthy definition: healthy baseline used to learn regimes/normalizer. Onset: not defined. RUL: not central. Window/evaluation: single cycles / cycle and downstream prognostic indicator.

**Method.** Split: training/hold-out structure reported by case study Engine-disjoint: `NR`; same-engine window crossing: `False`. Preprocessing/scaling: self-organizing map then normalizing multilayer perceptron / learned normalizing MLP. Condition treatment: explicit dynamic-regime baselining Clustering: self-organizing map without pre-specifying number of regimes. Model: SOM plus MLP. Calibration/threshold/smoothing/persistence: hold-out baselining comparison / not applicable / none / not applicable. Explanation: normalized sensor traces. NASA-file declaration: `{"exact_nasa_files": "NR"}`.

**Use and limits.** Supports learned regime-aware baselining Citation role: methodological preprocessing citation. Authors' limits: dataset-specific baselining quality and integration remain to be validated downstream Protocol audit: Exact subset/files and anomaly metrics are absent Category **C**; direct comparison: **no**. Caveat: Relevant preprocessing, but not an FD002 anomaly detector evaluation.

### LIT-006 — Multi-Sensor Prognostics using an Unsupervised Health Index based on LSTM Encoder-Decoder

**Identity.** Pankaj Malhotra; Vishnu TV; Anusha Ramakrishnan; Gaurangi Anand; Lovekesh Vig; Puneet Agarwal; Gautam Shroff. 2016. arXiv / PHM. DOI/stable identity: `10.48550/arXiv.1608.06154` / `arXiv:1608.06154`. Source: https://arxiv.org/pdf/1608.06154 (accessed 2026-09-03; `arxiv_full_text_verified`; SHA-256 `b62a8b848e235e9e82b35860c8261b5b1355933f387ab5d97505a56c31412008`; `arxiv_author_version`).

**Dataset and task.** NASA C-MAPSS turbofan plus milling and industrial pulverizer; subset `single-condition 100-train/100-test C-MAPSS set (FD001-equivalent)`; engines `100 train and 100 official test engines`. Task: health-index construction and RUL estimation; target: official-test terminal RUL; status: unsupervised healthy reconstruction followed by similarity-based RUL. Healthy definition: healthy subsequences from run-to-failure training instances. Onset: continuous reconstruction-error health index; no binary onset. RUL: trajectory-similarity terminal RUL. Window/evaluation: 20 cycles / engine terminal RUL.

**Method.** Split: 80 training engines fit, 20 training engines tune via truncation; 100 official test engines evaluate Engine-disjoint: `True`; same-engine window crossing: `False`. Preprocessing/scaling: PCA to three derived sensors and sequence reconstruction / reported normalization. Condition treatment: single-condition C-MAPSS; multiple regimes handled separately only as an extension Clustering: not for C-MAPSS case. Model: LSTM encoder-decoder plus linear health-index mapping and trajectory matching. Calibration/threshold/smoothing/persistence: grid search on 20 training engines / not an anomaly threshold / health-index curve matching / terminal RUL. Explanation: reconstruction error as health index. NASA-file declaration: `{"train_FD001": true, "test_FD001": true, "RUL_FD001": true, "FD002": false}`.

**Use and limits.** Foundational unsupervised LSTM reconstruction health index Citation role: reconstruction-method foundation. Authors' limits: HI varies substantially among engines at equal normalized age Protocol audit: FD001-equivalent RUL endpoint study, not FD002 alert evaluation Category **C**; direct comparison: **no**. Caveat: Official-test RUL results are contextual and cannot be compared with FD002 proxy anomaly metrics.

### LIT-003 — Performance Benchmarking and Analysis of Prognostic Methods for CMAPSS Datasets

**Identity.** Emmanuel Ramasso; Abhinav Saxena. 2014. International Journal of Prognostics and Health Management 5(2). DOI/stable identity: `10.36001/ijphm.2014.v5i2.2236` / `IJPHM:2236`. Source: https://papers.phmsociety.org/index.php/ijphm/article/download/2236/1223 (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `25c158e4a97fcacc797c49a0f1b23a242d13f3a55d5699ee8ca5d72d10001305`; `version_of_record`).

**Dataset and task.** NASA C-MAPSS benchmark family; subset `all C-MAPSS/PHM08 datasets`; engines `benchmark review`. Task: benchmarking and review; target: RUL/prognostic performance; status: methodological review. Healthy definition: not applicable. Onset: discusses health-state segmentation but defines no universal anomaly onset. RUL: reviews RUL conventions. Window/evaluation: various / engine-level prognostic score.

**Method.** Split: review of more than 70 publications and challenge baselines Engine-disjoint: `various`; same-engine window crossing: `various`. Preprocessing/scaling: reviews feature extraction/selection and health indices / various. Condition treatment: highlights operating-condition variability Clustering: various. Model: multiple prognostic models. Calibration/threshold/smoothing/persistence: various / not applicable / various / various. Explanation: various. NASA-file declaration: `{"train_files": "reviewed", "official_test_files": "reviewed", "RUL_files": "reviewed"}`.

**Use and limits.** Defines benchmark-comparison cautions Citation role: dataset/evaluation foundation. Authors' limits: benchmark comparability remained difficult because protocols and datasets were inconsistently used Protocol audit: Review values are not a new directly comparable anomaly experiment Category **C**; direct comparison: **no**. Caveat: A RUL benchmark review; no protocol-equivalent FD002 anomaly result.

### LIT-004 — Review and Analysis of Algorithmic Approaches Developed for Prognostics on CMAPSS Dataset

**Identity.** Emmanuel Ramasso; Abhinav Saxena. 2014. Annual Conference of the PHM Society / NASA report. DOI/stable identity: `NR` / `NASA NTRS:20150007677`. Source: https://ntrs.nasa.gov/api/citations/20150007677/downloads/20150007677.pdf (accessed 2026-09-03; `institutional_repository_verified`; SHA-256 `5b42232526e3f3ffb7167a712f609c5ebc49b58d58d4536929ec18ffbc466c74`; `nasa_public_manuscript`).

**Dataset and task.** NASA C-MAPSS benchmark family; subset `all C-MAPSS datasets`; engines `review`. Task: prognostic-method review; target: RUL and health-state estimation; status: methodological review. Healthy definition: not applicable. Onset: no common onset. RUL: reviews piecewise and complete-trajectory RUL conventions. Window/evaluation: various / various.

**Method.** Split: review and workflow guidance Engine-disjoint: `various`; same-engine window crossing: `various`. Preprocessing/scaling: reviews preprocessing and feature steps / various. Condition treatment: operating-condition assessment identified as a key step Clustering: various. Model: multiple. Calibration/threshold/smoothing/persistence: various / not applicable / various / various. Explanation: various. NASA-file declaration: `{"train_files": "reviewed", "official_test_files": "reviewed", "RUL_files": "reviewed"}`.

**Use and limits.** Supports official-test protocol interpretation Citation role: dataset and evaluation foundation. Authors' limits: few studies used official test consistently; comparison remained difficult Protocol audit: Review is contextual, not a new detector evaluation Category **C**; direct comparison: **no**. Caveat: Review evidence establishes protocol pitfalls, not directly comparable performance.

### LIT-001 — Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation

**Identity.** Abhinav Saxena; Kai Goebel; Don Simon; Neil Eklund. 2008. International Conference on Prognostics and Health Management. DOI/stable identity: `10.1109/PHM.2008.4711414` / `NASA NTRS:20090029214`. Source: https://ntrs.nasa.gov/api/citations/20090029214/downloads/20090029214.pdf (accessed 2026-09-03; `institutional_repository_verified`; SHA-256 `65c61129bf2ab89ff2d97aa8ae7371136dc3bb386a885c1bce358142c9a315ad`; `nasa_author_manuscript`).

**Dataset and task.** C-MAPSS simulator-generated engine trajectories; subset `dataset-generation foundation rather than FD001-FD004 evaluation`; engines `simulated fleets`. Task: damage-propagation simulation; target: run-to-failure sensor trajectories; status: physics/simulation model. Healthy definition: pre-fault operating period before randomized degradation injection. Onset: randomly selected deterioration start under exponential flow/efficiency loss. RUL: failure when health index reaches zero. Window/evaluation: cycle / cycle and simulated engine.

**Method.** Split: simulation scenarios Engine-disjoint: `not applicable`; same-engine window crossing: `False`. Preprocessing/scaling: thermodynamic response surfaces and stochastic degradation parameters / not applicable. Condition treatment: flight/operating conditions are simulator inputs Clustering: not applicable. Model: C-MAPSS simulation. Calibration/threshold/smoothing/persistence: not applicable / failure criteria / not applicable / run to failure. Explanation: health-index margins. NASA-file declaration: `{"released_FD002_files": false}`.

**Use and limits.** Explains synthetic degradation and unknown-onset boundary Citation role: C-MAPSS foundation. Authors' limits: simulation realism is bounded by chosen fault/degradation laws Protocol audit: Foundation only; not an evaluated anomaly detector Category **C**; direct comparison: **no**. Caveat: Foundational simulator evidence cannot serve as a detector comparator.

### LIT-005 — LSTM-based Encoder-Decoder for Multi-sensor Anomaly Detection

**Identity.** Pankaj Malhotra; Anusha Ramakrishnan; Gaurangi Anand; Lovekesh Vig; Puneet Agarwal; Gautam Shroff. 2016. ICML Anomaly Detection Workshop / arXiv. DOI/stable identity: `10.48550/arXiv.1607.00148` / `arXiv:1607.00148`. Source: https://arxiv.org/pdf/1607.00148 (accessed 2026-09-03; `arxiv_full_text_verified`; SHA-256 `d4c506d82061d0eb532a7c172682c7c8c1803705a8dbd9561fc8980927d9b3cd`; `arxiv_author_version`).

**Dataset and task.** five public/industrial multivariate datasets; subset `not C-MAPSS FD002`; engines `varies`. Task: multisensor anomaly detection; target: anomalous sequences; status: unsupervised/semi-supervised normal-only reconstruction. Healthy definition: normal sequences. Onset: dataset labels/events. RUL: not used. Window/evaluation: 30-500 depending dataset / time point/sequence.

**Method.** Split: dataset-specific normal training and labeled evaluation Engine-disjoint: `varies`; same-engine window crossing: `False`. Preprocessing/scaling: sequence standardization / training-data scaling. Condition treatment: unobserved exogenous conditions motivate robust reconstruction Clustering: none. Model: LSTM encoder-decoder. Calibration/threshold/smoothing/persistence: normal reconstruction-error distribution / Gaussian error model / likelihood threshold / NR / sequence anomaly. Explanation: multivariate reconstruction errors. NASA-file declaration: `{"nasa_cmapss_files": false}`.

**Use and limits.** Foundational LSTM reconstruction method Citation role: method foundation. Authors' limits: threshold assumptions and dataset-specific labels Protocol audit: No FD002, regime treatment, or matching event metrics Category **D**; direct comparison: **no**. Caveat: Generic method paper without FD002 evaluation.

### LIT-026 — Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding

**Identity.** Kyle Hundman; Valentino Constantinou; Christopher Laporte; Ian Colwell; Tom Soderstrom. 2018. ACM SIGKDD. DOI/stable identity: `10.1145/3219819.3219845` / `arXiv:1802.04431`. Source: https://arxiv.org/pdf/1802.04431 (accessed 2026-09-03; `arxiv_full_text_verified`; SHA-256 `bd5e2eb0706d2278eec1874dd32700fbd0d929e9c7208ed33c28ae5ace305836`; `arxiv_author_version`).

**Dataset and task.** NASA SMAP and MSL telemetry; subset `not C-MAPSS`; engines `expert-labeled telemetry channels`. Task: spacecraft telemetry anomaly detection; target: expert-labeled anomaly sequences; status: sequence prediction plus unsupervised dynamic threshold. Healthy definition: nominal-predominant telemetry. Onset: expert-labeled events. RUL: not used. Window/evaluation: prediction history and trailing error windows / channel time point/event.

**Method.** Split: mission telemetry train/test partitions Engine-disjoint: `NR`; same-engine window crossing: `False`. Preprocessing/scaling: channel-wise normalization and LSTM prediction / channel scaling. Condition treatment: channel-specific behavior; not operating regimes Clustering: none. Model: LSTM forecaster. Calibration/threshold/smoothing/persistence: nonparametric trailing-error threshold optimization / dynamic error threshold / error smoothing / grouped anomalous sequences with pruning/false-positive mitigation. Explanation: channel-wise errors. NASA-file declaration: `{"nasa_cmapss_files": false}`.

**Use and limits.** Supports dynamic thresholds and event grouping Citation role: alert-postprocessing foundation. Authors' limits: labels are incomplete and telemetry characteristics differ by channel Protocol audit: Different domain, labels, prediction model, and event semantics Category **D**; direct comparison: **no**. Caveat: Spacecraft telemetry event detection is methodological context only.

### LIT-034 — An Evaluation of Anomaly Detection and Diagnosis in Multivariate Time Series

**Identity.** Astha Garg; Wenyu Zhang; Jules Samaran; Savitha Ramasamy; Chuan-Sheng Foo. 2022. IEEE Transactions on Neural Networks and Learning Systems 33(6), 2508-2517. DOI/stable identity: `10.1109/TNNLS.2021.3105827` / `arXiv:2109.11428`. Source: https://arxiv.org/pdf/2109.11428 (accessed 2026-09-03; `arxiv_full_text_verified`; SHA-256 `5f199eef5306d1853d726c69e064207c1b6e056e7c549f84512d878618798715`; `arxiv_author_version`).

**Dataset and task.** multivariate cyber-physical-system benchmarks; subset `not C-MAPSS`; engines `multiple benchmark datasets`. Task: anomaly detection and diagnosis evaluation; target: point and event anomalies; status: unsupervised and semi-supervised methods. Healthy definition: dataset-specific normal training. Onset: dataset labels. RUL: not used. Window/evaluation: model-specific / point and event.

**Method.** Split: published benchmark splits Engine-disjoint: `varies`; same-engine window crossing: `False`. Preprocessing/scaling: ten models crossed with four scoring functions / dataset-specific. Condition treatment: not operating-regime focused Clustering: none. Model: ten reconstruction/prediction models. Calibration/threshold/smoothing/persistence: four error-scoring functions / static and dynamic scores / dynamic scoring / event-aware composite F-score. Explanation: channel-wise diagnosis via error. NASA-file declaration: `{"nasa_cmapss_files": false}`.

**Use and limits.** Supports event-aware metrics and importance of score postprocessing Citation role: evaluation-method foundation. Authors' limits: benchmark labels and metrics have known biases Protocol audit: No FD002 or matched proxy/event definitions Category **D**; direct comparison: **no**. Caveat: General benchmark evidence; metrics are not transferable as direct FD002 comparisons.

### LIT-036 — Towards a Rigorous Evaluation of Time-Series Anomaly Detection

**Identity.** Siwon Kim; Kukjin Choi; Hyun-Soo Choi; Byunghan Lee; Sungroh Yoon. 2022. Proceedings of AAAI 36(7), 7194-7201. DOI/stable identity: `10.1609/aaai.v36i7.20680` / `AAAI:20680`. Source: https://ojs.aaai.org/index.php/AAAI/article/download/20680/20439 (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `153966cc6b9ccf4d19e20a71430e865aaa540858db605f8aa88e28c4e062b8bb`; `version_of_record`).

**Dataset and task.** time-series anomaly benchmarks; subset `not C-MAPSS`; engines `multiple datasets`. Task: evaluation methodology; target: point/range anomaly labels; status: method-independent evaluation. Healthy definition: not applicable. Onset: dataset labels. RUL: not used. Window/evaluation: varies / point/range.

**Method.** Split: benchmark protocols Engine-disjoint: `varies`; same-engine window crossing: `False`. Preprocessing/scaling: evaluation protocol analysis / not applicable. Condition treatment: not operating-regime focused Clustering: none. Model: trained and untrained detector baselines. Calibration/threshold/smoothing/persistence: not applicable / thresholding as used by compared methods / not applicable / point adjustment examined. Explanation: not applicable. NASA-file declaration: `{"nasa_cmapss_files": false}`.

**Use and limits.** Justifies avoiding point adjustment and trivial-baseline inflation Citation role: evaluation-validity foundation. Authors' limits: scope limited to benchmark protocols studied Protocol audit: Demonstrates point adjustment inflation; no FD002 result Category **D**; direct comparison: **no**. Caveat: No FD002 experiment; supports only evaluation-design claims.

### LIT-055 — Anomaly Detection and Fault Disambiguation in Large Flight Data: A Multi-modal Deep Auto-encoder Approach

**Identity.** Kishore K. Reddy; Soumalya Sarkar; Vivek Venugopalan; Michael Giering. 2016. Annual Conference of the PHM Society 8(1). DOI/stable identity: `10.36001/phmconf.2016.v8i1.2549` / `PHMCONF:2549`. Source: https://papers.phmsociety.org/index.php/phmconf/article/download/2549/1509 (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `8641666caffbcaadc6db4152f3509260f9a96757b05f8dd510925786d695886a`; `version_of_record`).

**Dataset and task.** NASA electromechanical-actuator flight/test data; subset `not C-MAPSS`; engines `laboratory scenarios across operating conditions`. Task: anomaly detection and fault disambiguation; target: fault scenario; status: unsupervised nominal-data autoencoder. Healthy definition: nominal operating scenarios. Onset: injected/experimental faults. RUL: not used. Window/evaluation: raw time-series segments / sample/event.

**Method.** Split: nominal training and laboratory validation across conditions Engine-disjoint: `NR`; same-engine window crossing: `False`. Preprocessing/scaling: raw multisensor sequences / reported normalization. Condition treatment: multiple operating conditions represented in nominal training Clustering: none. Model: multi-modal deep autoencoder. Calibration/threshold/smoothing/persistence: nominal reconstruction behavior / reconstruction error / NR / fault scenarios. Explanation: individual-sensor reconstruction-error decomposition. NASA-file declaration: `{"nasa_cmapss_files": false}`.

**Use and limits.** Direct precedent for observational sensor-wise reconstruction attribution Citation role: explainability-method foundation. Authors' limits: two fault scenarios and laboratory setting limit breadth Protocol audit: Different system, labels, and detection-rate metric Category **D**; direct comparison: **no**. Caveat: Sensor contribution method is relevant; numerical results are not comparable with FD002 alerts.

### LIT-051 — Aero-Engine Fault Detection with an LSTM Auto-Encoder Combined with a Self-Attention Mechanism

**Identity.** Wenyou Du; Jingyi Zhang; Guanglei Meng; Haoran Zhang. 2024. Machines 12(12), 879. DOI/stable identity: `10.3390/machines12120879` / `Machines:12:879`. Source: https://mdpi-res.com/d_attachment/machines/machines-12-00879/article_deploy/machines-12-00879.pdf (accessed 2026-09-03; `publisher_full_text_verified`; SHA-256 `e9d65906d8716bb8bc396da0c9bb24e8f5c7642a6a2c040ea1d835b9f78bd493`; `version_of_record`).

**Dataset and task.** real piston aero-engine ECU time series; subset `not C-MAPSS`; engines `two-hour flight-status records; exact engine count NR`. Task: aero-engine fault detection; target: fault versus normal sequence; status: unsupervised normal-only reconstruction. Healthy definition: normal ECU operating data. Onset: experimental fault labels. RUL: not used. Window/evaluation: time-series windows; exact length in Section 3 / window/time point.

**Method.** Split: normal training and fault evaluation; exact engine-disjoint status NR Engine-disjoint: `NR`; same-engine window crossing: `NR`. Preprocessing/scaling: dynamic multivariate sequence preprocessing / reported normalization. Condition treatment: multiple operating modes represented; self-attention models coupling Clustering: none. Model: LSTM autoencoder with self-attention. Calibration/threshold/smoothing/persistence: normal reconstruction distribution / window reconstruction-error threshold / NR / point/window fault decisions. Explanation: attention plus reconstruction errors; attention is not causal attribution. NASA-file declaration: `{"nasa_cmapss_files": false}`.

**Use and limits.** Reserve replacement preserves aero-engine LSTM-autoencoder relevance Citation role: methodological fault-detection context. Authors' limits: single piston-engine dataset and limited fault cases Protocol audit: Not turbofan C-MAPSS; split and metrics differ Category **C**; direct comparison: **no**. Caveat: Aero-engine anomaly intent aligns, but hardware, data, labels, split, and metrics are different.

## Unresolved evidence

`36` paper-field pairs remain `NR`, each listed with a reason in the JSON derivative. `NR` is retained whenever the inspected manuscript did not unambiguously report the detail; no value was inferred from the temporary environment.

## Boundaries

No local held-out or official NASA-test data were opened. No model was fit, tuned, recalibrated, fused, or reselected. PDFs remain only under `C:/tmp/turbofan-core-literature-v1` and are not repository artifacts.
