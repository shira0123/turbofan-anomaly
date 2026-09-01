# Literature-to-Project Metric Comparison

**Frozen project policy:** `pca_reconstruction__per_mode__quantile_0.995__ewma_alpha_0.20__persistence_8`
**Project metric authority:** `configs/evaluation/fd002-confirmatory-results-v1.json`
**Primary report authority:** `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/result.json`

> No directly protocol-equivalent published comparator was identified in the verified literature set.

This is a result of applying the registered comparability criteria, not a claim that no comparable work exists. Category B numbers below are visibly non-equivalent. Category C and D sources are context only. No averages, rankings, or cross-paper metric conversions were made.

## Frozen project results

| Endpoint proxy | FAR/1,000 | FAR percentage | Engine coverage | Median delay | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Final 10% | 32.440 | 3.2440% | 51.92% | 12 | 0.60267 | 0.94762 |
| Final 20% | 9.443 | 0.9443% | 78.85% | 25 | 0.80974 | 0.92673 |
| Final 30% | 5.153 | 0.5153% | 84.62% | 42.5 | 0.82745 | 0.86758 |

Aggregate median held-out delay was **25 cycles**, so the aggregate `<=12`-cycle aspiration was not achieved. All three endpoint FAR percentages were below 6%; only the final-10% proxy had median delay exactly 12 cycles. Coverage and delay are proxy-sensitive. These are proxy-labelled internal held-out results, not official NASA-test results, physical fault-onset results, or operational estimates.

## Frozen LSTM comparator

| Endpoint proxy | FAR/1,000 | Engine coverage | Median delay |
|---|---:|---:|---:|
| Final 10% | 52.883 | 55.77% | 10 |
| Final 20% | 19.309 | 86.54% | 24 |
| Final 30% | 12.799 | 92.31% | 41 |

The LSTM ensemble is the pre-registered, unfused comparator. It was not selected after held-out access and does not replace the frozen PCA primary policy.

## Closest verified published evidence

| Paper | Dataset/subset | Task | Split | Label definition | Model | Metric | Published value | Our mathematically matching value | Category | Direct comparison? | Evidence location | Caveat |
|---|---|---|---|---|---|---|---:|---:|:---:|:---:|---|---|
| Sanchez et al. (2026) | FD002 | anomaly detection | within-trajectory 85/15; healthy-window validation | final 10% degraded | LSTM autoencoder | Precision | 0.374 | 0.7065337763 | B | No | Author manuscript, Table 3, pp. 9-11 | Same metric and proxy fraction, but materially different split, preprocessing, threshold, persistence, and alert semantics; do not rank. |
| Sanchez et al. (2026) | FD002 | anomaly detection | within-trajectory 85/15; healthy-window validation | final 10% degraded | LSTM autoencoder | Recall | 0.799 | 0.5789473684 | B | No | Author manuscript, Table 3, pp. 9-11 | Same warning. |
| Sanchez et al. (2026) | FD002 | anomaly detection | within-trajectory 85/15; healthy-window validation | final 10% degraded | LSTM autoencoder | Specificity | 0.982 | 0.9675602889 | B | No | Author manuscript, Table 3, pp. 9-11 | Same warning. |
| Sanchez et al. (2026) | FD002 | anomaly detection | within-trajectory 85/15; healthy-window validation | final 10% degraded | LSTM autoencoder | F1 | 0.510 | 0.6364089776 | B | No | Author manuscript, Table 3, pp. 9-11 | Same warning. |
| Al Bataineh et al. (2020) | FD004 | anomaly detection | 220/20/19 engines | first 60% normal; last 5% anomalous | feed-forward autoencoder | F1 / precision / recall | 0.892 / 0.896 / 0.724 | NR | C | No | IJACSA Table VI, p. 47 | Different subset, label, model, and tuning protocol. |
| Mousavi et al. (2025) | FD001; FD003 | anomaly detection | random engine-disjoint 80/20 | first 60% normal; last 40% anomalous | TDC-AE | F1 | 95.56% / 93.49% | NR | C | No | arXiv HTML v3, Table II | Different subsets, label, threshold optimization, and metrics scale. |

The machine-readable table includes all 100 audited records, including `NR` rows that document why a numerical comparison is not authorized.
