# Core Literature Comparability V1

**Frozen project policy:** `pca_reconstruction__per_mode__quantile_0.995__ewma_alpha_0.20__persistence_8`

> No directly protocol-equivalent published comparator was identified in the manuscript-grade core literature set.

Category A requires FD002 anomaly/degradation detection, an engine-disjoint or equivalent held-out design, unsupervised/one-class/healthy-only training, a compatible onset definition and metric, and clearly reported held-out results. No core paper satisfies all requirements.

## Category totals

| A | B | C | D | Direct comparisons |
|---:|---:|---:|---:|---:|
| 0 | 2 | 11 | 7 | 0 |

## Frozen internal held-out evidence

| Proxy | FAR/1,000 | FAR % | Coverage % | Median delay | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Final 10% | 32.440 | 3.2440 | 51.92 | 12 | 0.60267 | 0.94762 |
| Final 20% | 9.443 | 0.9443 | 78.85 | 25 | 0.80974 | 0.92673 |
| Final 30% | 5.153 | 0.5153 | 84.62 | 42.5 | 0.82745 | 0.86758 |

These proxy-labelled values are internal held-out results. They are not official NASA-test, observed physical-onset, production, or field-performance results. The FAR objective was met for all proxies; the aggregate 25-cycle median delay missed the ≤12-cycle aspiration.

## Paper-level decision

| ID | Category | Closest alignment | Decisive mismatch | Direct? |
|---|:---:|---|---|:---:|
| LIT-010 | B | Closest FD002 anomaly/degradation context | FD002 aligns, but task, labels, split identity, threshold/event semantics, and metrics do not. | no |
| LIT-013 | B | Strongest partial unsupervised FD002 anomaly comparator | Same FD002 and anomaly intent, but non-engine-disjoint within-trajectory split, different proxy, threshold, persistence, and point metrics prohibit direct comparison. | no |
| LIT-007 | C | Healthy-only reconstruction precedent with engine-disjoint evaluation | Engine-disjoint anomaly evaluation is useful context, but FD004 has two faults and labels/metrics/alert semantics differ. | no |
| LIT-008 | C | One-class calibration and learned-onset precedent | Change-point objective and model-derived reference are not equivalent to this project's proxy endpoint alerts. | no |
| LIT-009 | C | Operating-condition and learned-change-point context | Uses FD002 official test, but evaluates last-cycle RUL regression rather than anomaly alerts over all observed cycles. | no |
| LIT-012 | C | Physics-inspired temporal reconstruction comparison | Engine split is useful, but subset, 60/40 onset, threshold supervision, and point metrics differ. | no |
| LIT-014 | D | Supports residualization before LSTM reconstruction | Real-engine relevance is high but dataset, faults, units, labels, and metrics are not protocol-equivalent. | no |
| LIT-017 | D | Supports condition-aware normalization before reconstruction | Methodological analogue only; no C-MAPSS or matching alert protocol. | no |
| LIT-018 | C | FD002 regime-scaling and official-test RUL context | FD002 aligns, but supervised last-cycle RUL RMSE/score is a different target and evaluation unit. | no |
| LIT-021 | C | Supports learned regime-aware baselining | Relevant preprocessing, but not an FD002 anomaly detector evaluation. | no |
| LIT-006 | C | Foundational unsupervised LSTM reconstruction health index | Official-test RUL results are contextual and cannot be compared with FD002 proxy anomaly metrics. | no |
| LIT-003 | C | Defines benchmark-comparison cautions | A RUL benchmark review; no protocol-equivalent FD002 anomaly result. | no |
| LIT-004 | C | Supports official-test protocol interpretation | Review evidence establishes protocol pitfalls, not directly comparable performance. | no |
| LIT-001 | C | Explains synthetic degradation and unknown-onset boundary | Foundational simulator evidence cannot serve as a detector comparator. | no |
| LIT-005 | D | Foundational LSTM reconstruction method | Generic method paper without FD002 evaluation. | no |
| LIT-026 | D | Supports dynamic thresholds and event grouping | Spacecraft telemetry event detection is methodological context only. | no |
| LIT-034 | D | Supports event-aware metrics and importance of score postprocessing | General benchmark evidence; metrics are not transferable as direct FD002 comparisons. | no |
| LIT-036 | D | Justifies avoiding point adjustment and trivial-baseline inflation | No FD002 experiment; supports only evaluation-design claims. | no |
| LIT-055 | D | Direct precedent for observational sensor-wise reconstruction attribution | Sensor contribution method is relevant; numerical results are not comparable with FD002 alerts. | no |
| LIT-051 | C | Reserve replacement preserves aero-engine LSTM-autoencoder relevance | Aero-engine anomaly intent aligns, but hardware, data, labels, split, and metrics are different. | no |

## Strongest partial comparator

`LIT-013` is the strongest genuinely comparable paper because it evaluates unsupervised reconstruction-based early-fault detection on FD002 and reports precision, recall, specificity, and F1. It remains Category B: its windows are partitioned within the same engine, the final-10% label is a different heuristic, and its adaptive threshold and five-window persistence are not the frozen per-mode quantile/EWMA/persistence-8 policy. A side-by-side numerical performance claim is therefore prohibited.

## Metric discipline

RUL RMSE/NASA score, point-level precision/recall/F1, laboratory detection rate, and project endpoint FAR/coverage/delay/PR-AUC/ROC-AUC are retained as distinct quantities. Validation and test values, subsets, aggregation units, and proxy labels are never merged.
