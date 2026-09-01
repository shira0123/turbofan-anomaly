# Literature Evidence Matrix v4

**Audit date:** 2026-09-01
**Immutable source:** `docs/research/Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx`
**Source SHA-256:** `ae173e281fbcbccae7da91920980f4d208a908d2f1a6a6dcfb54af5ebdf05ac3`

This derivative audits all 100 unique v3 records under a stricter publication-evidence rule. It does not edit or supersede the v3 authority. Exact numerical values are retained only after verified access to the containing full text, authoritative HTML, or author manuscript. `NR` means not reported or not verified at the evidence level needed for the field; it is not a zero.

## Audit summary

| Measure | Count |
|---|---:|
| Unique records | 100 |
| Full-text-equivalent records | 69 |
| Abstract-only records | 27 |
| Metadata-only records | 4 |
| Category A / B / C / D | 0 / 2 / 23 / 75 |
| Direct numerical comparators | 0 |
| Duplicate or invalid records removed | 0 |

## Comparison categories

- **A:** FD002 anomaly/degradation detection with substantially compatible engine-disjoint evaluation, healthy-only/one-class training, label semantics, metric, and held-out scope. Only A permits direct numerical comparison.
- **B:** FD002 but a material protocol mismatch (label, split, task, alert semantics, supervision, or reporting). Values require a visible non-equivalence warning.
- **C:** C-MAPSS or turbofan context with another subset/task/unit. No superiority comparison.
- **D:** foundational or methodological evidence. No FD002 performance comparison.

## Audited register

The complete schema and long-form fields are in [`LITERATURE_EVIDENCE_MATRIX_V4.json`](LITERATURE_EVIDENCE_MATRIX_V4.json) and [`LITERATURE_EVIDENCE_MATRIX_V4.csv`](LITERATURE_EVIDENCE_MATRIX_V4.csv).

| ID | Year | Category | Access | Dataset/subset | Numerical values | Paper |
|---|---:|:---:|---|---|---|---|
| LIT-001 | 2008 | C | `full_text_verified` | C-MAPSS simulator (not a benchmark subset result) | NR | [Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation](https://ieeexplore.ieee.org/document/4711414) |
| LIT-002 | 2026 | C | `metadata_only` | FD001; FD002; FD003; FD004 | NR | [C-MAPSS Jet Engine Simulated Data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data) |
| LIT-003 | 2014 | C | `full_text_verified` | C-MAPSS | NR | [Performance Benchmarking and Analysis of Prognostic Methods for CMAPSS Datasets](https://papers.phmsociety.org/index.php/ijphm/article/view/2236) |
| LIT-004 | 2014 | C | `full_text_verified` | C-MAPSS | NR | [Review and Analysis of Algorithmic Approaches Developed for Prognostics on CMAPSS Data](https://ntrs.nasa.gov/api/citations/20150007677/downloads/20150007677.pdf) |
| LIT-005 | 2016 | D | `full_text_verified` | Multivariate industrial sequences | NR | [LSTM-based Encoder-Decoder for Multi-sensor Anomaly Detection](https://arxiv.org/abs/1607.00148) |
| LIT-006 | 2016 | C | `full_text_verified` | C-MAPSS | NR | [Multi-Sensor Prognostics using an Unsupervised Health Index based on LSTM Encoder-Decoder](https://arxiv.org/abs/1608.06154) |
| LIT-007 | 2020 | C | `full_text_verified` | FD004 (identified by 249 engines, six conditions, two fault modes) | verified | [Autoencoder-based Semi-Supervised Anomaly Detection in Turbofan Engines](https://thesai.org/Publications/ViewPaper?Code=IJACSA&Issue=11&SerialNo=5&Volume=11) |
| LIT-008 | 2019 | C | `full_text_verified` | C-MAPSS | NR | [A One-Class Support Vector Machine Calibration Method for Time Series Change Point Detection](https://arxiv.org/abs/1902.06361) |
| LIT-009 | 2024 | C | `full_text_verified` | Six-condition C-MAPSS | NR | [A Change Point Detection Integrated Remaining Useful Life Estimation Model under Variable Operating Conditions](https://arxiv.org/abs/2401.04351) |
| LIT-010 | 2024 | B | `full_text_verified` | FD002 | NR | [Anomaly Detection and Remaining Useful Life Prediction for Turbofan Engines with a Key Point-Based Approach to Secure Health Management](https://www.mdpi.com/1424-8220/24/24/8022) |
| LIT-011 | 2025 | C | `abstract_only` | FD001; FD003 | NR | [Aero-engines Anomaly Detection using an Unsupervised Fisher Autoencoder](https://arxiv.org/abs/2502.05428) |
| LIT-012 | 2025 | C | `authoritative_html_full_text_verified` | FD001; FD003 | verified | [Anomaly Detection in Complex Dynamical Systems using TDC-AE](https://arxiv.org/html/2502.19307v3) |
| LIT-013 | 2026 | B | `author_manuscript_verified` | FD001; FD002; FD003; FD004 | verified | [Early Fault Detection on CMAPSS with Unsupervised LSTM Autoencoders](https://arxiv.org/abs/2601.10269) |
| LIT-014 | 2025 | D | `full_text_verified` | Real jet-engine test data plus simulation context | NR | [RAVEN: Unsupervised Anomaly Detection in Multivariate Time Series through Residual Modeling and Autoencoder Reconstruction](https://papers.phmsociety.org/index.php/phmap/article/view/4647) |
| LIT-015 | 2026 | C | `abstract_only` | FD001 | NR | [Autoencoder-Based Anomaly Detection for Turbofan Engine Sensors Data](https://everant.org/index.php/etj/article/view/2452) |
| LIT-016 | 2022 | D | `abstract_only` | Industrial degradation monitoring | NR | [Anomaly Detection in Asset Degradation Process Using Variational Autoencoder](https://www.mdpi.com/1424-8220/22/1/291) |
| LIT-017 | 2024 | D | `full_text_verified` | Gas-turbine vibration | NR | [Gas Turbine Anomaly Detection under Time-Varying Operation Conditions Based on Spectra Alignment and Self-Adaptive Normalization](https://www.mdpi.com/1424-8220/24/3/941) |
| LIT-018 | 2023 | C | `full_text_verified` | C-MAPSS | NR | [Multiform Informed Machine Learning Based on Piecewise and Weibull for Engine RUL Prediction](https://www.mdpi.com/1424-8220/23/12/5669) |
| LIT-019 | 2026 | C | `full_text_verified` | FD002 | NR | [Condition-Aware AI for Predictive Maintenance: Dual-Attention CNN-GRU with Per-Regime Scaling](https://www.sciencedirect.com/science/article/pii/S0957417426004951) |
| LIT-020 | 2023 | C | `full_text_verified` | N-CMAPSS | NR | [Domain Adaptation via Alignment of Operation Profile for Remaining Useful Lifetime Prediction](https://arxiv.org/abs/2302.01704) |
| LIT-021 | 2021 | C | `full_text_verified` | Dynamic operating regimes including C-MAPSS context | NR | [A Self-Organizing Map and a Normalizing Multi-Layer Perceptron Approach to Baselining in Prognostics under Dynamic Regimes](https://doi.org/10.1016/j.neucom.2021.05.031) |
| LIT-022 | 2023 | D | `full_text_verified` | Industrial multivariate systems | NR | [A Comparison of Residual-based Methods on Fault Detection](https://papers.phmsociety.org/index.php/phmconf/article/view/3444) |
| LIT-023 | 2008 | D | `abstract_only` | General tabular anomaly detection | NR | [Isolation Forest](https://ieeexplore.ieee.org/document/4781136) |
| LIT-024 | 2000 | D | `abstract_only` | General anomaly detection | NR | [LOF: Identifying Density-Based Local Outliers](https://dl.acm.org/doi/10.1145/342009.335388) |
| LIT-025 | 2001 | D | `abstract_only` | General one-class learning | NR | [Estimating the Support of a High-Dimensional Distribution](https://doi.org/10.1162/089976601750264965) |
| LIT-026 | 2018 | D | `full_text_verified` | NASA spacecraft telemetry | NR | [Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding](https://dl.acm.org/doi/10.1145/3219819.3219845) |
| LIT-027 | 2017 | D | `full_text_verified` | Streaming time series | NR | [Anomaly Detection in Streams with Extreme Value Theory](https://dl.acm.org/doi/10.1145/3097983.3098144) |
| LIT-028 | 2019 | D | `full_text_verified` | Multivariate time series | NR | [Robust Anomaly Detection for Multivariate Time Series through Stochastic Recurrent Neural Network](https://dl.acm.org/doi/10.1145/3292500.3330672) |
| LIT-029 | 2020 | D | `full_text_verified` | Multivariate time series | NR | [USAD: UnSupervised Anomaly Detection on Multivariate Time Series](https://dl.acm.org/doi/10.1145/3394486.3403392) |
| LIT-030 | 2020 | D | `full_text_verified` | Multivariate time series | NR | [Multivariate Time-series Anomaly Detection via Graph Attention Network](https://arxiv.org/abs/2009.02040) |
| LIT-031 | 2022 | D | `full_text_verified` | Multivariate time series | NR | [TranAD: Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data](https://arxiv.org/abs/2201.07284) |
| LIT-032 | 2022 | D | `full_text_verified` | Multivariate time series | NR | [Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy](https://openreview.net/forum?id=LzQQ89U1qm_) |
| LIT-033 | 2019 | D | `full_text_verified` | General anomaly detection | NR | [Memorizing Normality to Detect Anomaly: Memory-augmented Deep Autoencoder](https://arxiv.org/abs/1904.02639) |
| LIT-034 | 2022 | D | `full_text_verified` | Multiple multivariate benchmarks | NR | [An Evaluation of Anomaly Detection and Diagnosis in Multivariate Time Series](https://pubmed.ncbi.nlm.nih.gov/34464278/) |
| LIT-035 | 2018 | D | `full_text_verified` | Range-based time-series anomalies | NR | [Precision and Recall for Time Series](https://papers.nips.cc/paper/7462-precision-and-recall-for-time-series) |
| LIT-036 | 2022 | D | `full_text_verified` | Time-series anomaly benchmarks | NR | [Towards a Rigorous Evaluation of Time-Series Anomaly Detection](https://ojs.aaai.org/index.php/AAAI/article/view/20680) |
| LIT-037 | 2022 | D | `full_text_verified` | Time-series anomaly benchmarks | NR | [Volume Under the Surface: A New Accuracy Evaluation Measure for Time-Series Anomaly Detection](https://dl.acm.org/doi/10.14778/3551793.3551830) |
| LIT-038 | 2022 | D | `full_text_verified` | Large multi-domain benchmark | NR | [Anomaly Detection in Time Series: A Comprehensive Evaluation](https://timeeval.github.io/evaluation-paper/) |
| LIT-039 | 2023 | D | `full_text_verified` | Popular anomaly benchmarks | NR | [Current Time Series Anomaly Detection Benchmarks are Flawed and are Creating the Illusion of Progress](https://arxiv.org/abs/2009.13807) |
| LIT-040 | 2023 | D | `full_text_verified` | Time-series anomaly metrics | NR | [Navigating the Metric Maze: A Taxonomy of Evaluation Metrics for Anomaly Detection in Time Series](https://arxiv.org/abs/2303.01272) |
| LIT-041 | 2017 | D | `full_text_verified` | General supervised models | NR | [A Unified Approach to Interpreting Model Predictions](https://proceedings.neurips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions.pdf) |
| LIT-042 | 2023 | D | `full_text_verified` | Explainable anomaly detection | NR | [A Survey on Explainable Anomaly Detection](https://dl.acm.org/doi/10.1145/3609333) |
| LIT-043 | 2019 | D | `full_text_verified` | Manufacturing multivariate systems | NR | [Anomaly Detection and Diagnosis in Manufacturing Systems](https://papers.phmsociety.org/index.php/phmconf/article/view/815) |
| LIT-044 | 2022 | D | `full_text_verified` | Temporal ML models | NR | [ReX: A Framework for Incorporating Temporal Information in Model-Agnostic Local Explanation Techniques](https://arxiv.org/abs/2209.03798) |
| LIT-045 | 2013 | D | `full_text_verified` | General anomaly detection | NR | [Outlier Ensembles: An Introduction](https://dl.acm.org/doi/10.1145/2481244.2481252) |
| LIT-046 | 2015 | D | `full_text_verified` | General anomaly detection | NR | [Theoretical Foundations and Algorithms for Outlier Ensembles](https://dl.acm.org/doi/10.1145/2830544.2830549) |
| LIT-047 | 2012 | C | `abstract_only` | C-MAPSS | NR | [A Multiple Classifier System for Prognostics of Aircraft Engines](https://ieeexplore.ieee.org/document/6197000/) |
| LIT-048 | 2022 | D | `full_text_verified` | Streaming datasets with concept drift | NR | [Adaptive Model Pooling for Online Deep Anomaly Detection from a Complex Evolving Data Stream](https://arxiv.org/abs/2206.04792) |
| LIT-049 | 2023 | D | `full_text_verified` | Streaming imbalanced datasets | NR | [Autoencoder-based Anomaly Detection in Streaming Data with Incremental Learning and Concept Drift Adaptation](https://arxiv.org/abs/2305.08977) |
| LIT-050 | 2024 | D | `full_text_verified` | K-means benchmarks | NR | [The Impact of Neglecting Feature Scaling in K-means Clustering](https://pmc.ncbi.nlm.nih.gov/articles/PMC11623793/) |
| LIT-051 | 2024 | C | `full_text_verified` | Aero-engine multivariate data | NR | [Aero-Engine Fault Detection with an LSTM Auto-Encoder and Self-Attention Mechanism](https://www.mdpi.com/2075-1702/12/12/879) |
| LIT-052 | 2026 | C | `full_text_verified` | C-MAPSS | NR | [Bifurcated Remaining Useful Life Prediction: A Hybrid Prognostic Framework](https://www.papers.phmsociety.org/index.php/phme/article/view/4903) |
| LIT-053 | 2007 | C | `metadata_only` | C-MAPSS simulator | NR | [User's Guide for the Commercial Modular Aero-Propulsion System Simulation (C-MAPSS)](https://ntrs.nasa.gov/citations/20070034949) |
| LIT-054 | 2021 | C | `full_text_verified` | N-CMAPSS | NR | [Aircraft Engine Run-to-Failure Dataset under Real Flight Conditions for Prognostics and Diagnostics](https://www.mdpi.com/2306-5729/6/1/5) |
| LIT-055 | 2016 | D | `full_text_verified` | Aircraft electromechanical actuator; multiple operating conditions | NR | [Anomaly Detection and Fault Disambiguation in Large Flight Data: A Multi-modal Deep Auto-encoder Approach](https://papers.phmsociety.org/index.php/phmconf/article/view/2549) |
| LIT-056 | 2019 | C | `full_text_verified` | C-MAPSS dynamic model; healthy plus four fault conditions | NR | [Hybrid Deep Fault Detection and Isolation: Combining Deep Neural Networks and System Performance Models](https://papers.phmsociety.org/index.php/ijphm/article/view/2621) |
| LIT-057 | 2019 | C | `full_text_verified` | C-MAPSS TEDS and PHM2008 | NR | [Operating Condition-Invariant Neural Network-based Prognostics Methods Applied on Turbofan Aircraft Engines](https://papers.phmsociety.org/index.php/phmconf/article/view/786) |
| LIT-058 | 2023 | C | `full_text_verified` | N-CMAPSS | NR | [Data-Driven Prognostics and Diagnostics of Industrial Machinery: A Turbofan Engine Case Study](https://papers.phmsociety.org/index.php/phmap/article/view/3690) |
| LIT-059 | 2018 | D | `full_text_verified` | General high-dimensional anomaly benchmarks | NR | [Deep Autoencoding Gaussian Mixture Model for Unsupervised Anomaly Detection](https://openreview.net/forum?id=BJJLHbb0-) |
| LIT-060 | 2018 | D | `abstract_only` | General one-class anomaly detection | NR | [Deep One-Class Classification](https://proceedings.mlr.press/v80/ruff18a) |
| LIT-061 | 2019 | D | `abstract_only` | SWaT and WADI cyber-physical systems | NR | [MAD-GAN: Multivariate Anomaly Detection for Time Series Data with Generative Adversarial Networks](https://arxiv.org/abs/1901.04997) |
| LIT-062 | 2019 | D | `full_text_verified` | Multivariate industrial time series | NR | [A Deep Neural Network for Unsupervised Anomaly Detection and Diagnosis in Multivariate Time Series Data](https://ojs.aaai.org/index.php/AAAI/article/view/3942) |
| LIT-063 | 2021 | D | `full_text_verified` | High-dimensional sensor time series | NR | [Graph Neural Network-Based Anomaly Detection in Multivariate Time Series](https://ojs.aaai.org/index.php/AAAI/article/view/16523) |
| LIT-064 | 2020 | D | `abstract_only` | General time-series anomaly benchmarks | NR | [Timeseries Anomaly Detection using Temporal Hierarchical One-Class Network](https://proceedings.neurips.cc/paper/2020/hash/97e401a02082021fd24957f852e0e475-Abstract.html) |
| LIT-065 | 2021 | D | `abstract_only` | Multivariate time-series benchmarks | NR | [Multivariate Time Series Anomaly Detection and Interpretation Using Hierarchical Inter-Metric and Temporal Embedding](https://dl.acm.org/doi/10.1145/3447548.3467075) |
| LIT-066 | 2020 | D | `full_text_verified` | Univariate time-series benchmarks | NR | [Time Series Anomaly Detection Using Generative Adversarial Networks](https://arxiv.org/abs/2009.07769) |
| LIT-067 | 2018 | D | `abstract_only` | Seasonal web KPIs | NR | [Unsupervised Anomaly Detection via Variational Auto-Encoder for Seasonal KPIs in Web Applications](https://dl.acm.org/doi/10.1145/3178876.3185996) |
| LIT-068 | 2020 | D | `full_text_verified` | General semi-supervised anomaly detection | NR | [Deep Semi-Supervised Anomaly Detection](https://openreview.net/forum?id=HkgH0TEYwH) |
| LIT-069 | 2022 | D | `full_text_verified` | Tabular anomaly benchmarks | NR | [LUNAR: Unifying Local Outlier Detection Methods via Graph Neural Networks](https://ojs.aaai.org/index.php/AAAI/article/view/20629) |
| LIT-070 | 2023 | D | `full_text_verified` | Multivariate time-series benchmarks | NR | [Detecting Multivariate Time Series Anomalies with Zero Known Label](https://ojs.aaai.org/index.php/AAAI/article/view/25623) |
| LIT-071 | 2021 | D | `full_text_verified` | Time-series anomaly benchmarks | NR | [Time Series Anomaly Detection with Multiresolution Ensemble Decoding](https://ojs.aaai.org/index.php/AAAI/article/view/17152) |
| LIT-072 | 2023 | D | `abstract_only` | Time-series anomaly benchmarks | NR | [DCdetector: Dual Attention Contrastive Representation Learning for Time Series Anomaly Detection](https://dl.acm.org/doi/10.1145/3580305.3599295) |
| LIT-073 | 2024 | D | `full_text_verified` | Industrial-scale time-series anomaly evaluation | NR | [TimeSeriesBench: An Industrial-Grade Benchmark for Time Series Anomaly Detection Models](https://arxiv.org/abs/2402.10802) |
| LIT-074 | 2022 | D | `abstract_only` | Large univariate TSAD benchmark suite | NR | [TSB-UAD: An End-to-End Benchmark Suite for Univariate Time-Series Anomaly Detection](https://dl.acm.org/doi/10.14778/3529337.3529354) |
| LIT-075 | 2022 | D | `metadata_only` | Reproducible TSAD experimentation | NR | [TimeEval: A Benchmarking Toolkit for Time Series Anomaly Detection Algorithms](https://timeeval.github.io/evaluation-paper/) |
| LIT-076 | 2015 | D | `abstract_only` | Streaming univariate time series | NR | [Evaluating Real-time Anomaly Detection Algorithms: The Numenta Anomaly Benchmark](https://arxiv.org/abs/1510.03336) |
| LIT-077 | 2022 | D | `abstract_only` | Event/range anomaly evaluation | NR | [Local Evaluation of Time Series Anomaly Detection Algorithms](https://dl.acm.org/doi/10.1145/3534678.3539339) |
| LIT-078 | 2024 | D | `abstract_only` | Time-series anomaly intervals | NR | [PATE: Proximity-Aware Time Series Anomaly Evaluation](https://dl.acm.org/doi/10.1145/3637528.3671971) |
| LIT-079 | 2022 | D | `abstract_only` | Time-series anomaly metrics | NR | [Do You Know Existing Accuracy Metrics Overrate Time-Series Anomaly Detections?](https://dl.acm.org/doi/10.1145/3477314.3507024) |
| LIT-080 | 2024 | D | `full_text_verified` | Unsupervised TSAD research practice | NR | [Position: Quo Vadis, Unsupervised Time Series Anomaly Detection?](https://arxiv.org/abs/2405.02678) |
| LIT-081 | 2012 | D | `abstract_only` | General offline change-point detection | NR | [Optimal Detection of Changepoints With a Linear Computational Cost](https://www.tandfonline.com/doi/full/10.1080/01621459.2012.737745) |
| LIT-082 | 2007 | D | `abstract_only` | Sequential probabilistic change detection | NR | [Bayesian Online Changepoint Detection](https://arxiv.org/abs/0710.3742) |
| LIT-083 | 2020 | D | `full_text_verified` | Multivariate offline change-point detection | NR | [Selective Review of Offline Change Point Detection Methods](https://www.sciencedirect.com/science/article/pii/S0165168419303494) |
| LIT-084 | 2013 | D | `abstract_only` | General time series | NR | [Change-Point Detection in Time-Series Data by Relative Density-Ratio Estimation](https://arxiv.org/abs/1203.0453) |
| LIT-085 | 2012 | D | `full_text_verified` | General multivariate sequences | NR | [Kernel Change-Point Detection](https://hal.science/hal-00671174v1/document) |
| LIT-086 | 1959 | D | `abstract_only` | Statistical process monitoring | NR | [Control Chart Tests Based on Geometric Moving Averages](https://www.tandfonline.com/doi/abs/10.1080/00401706.1959.10489860) |
| LIT-087 | 1954 | D | `metadata_only` | Sequential quality control | NR | [Continuous Inspection Schemes](https://academic.oup.com/biomet/article-abstract/41/1-2/100/456627) |
| LIT-088 | 2007 | D | `abstract_only` | Streaming concept drift | NR | [Learning from Time-Changing Data with Adaptive Windowing](https://epubs.siam.org/doi/10.1137/1.9781611972771.42) |
| LIT-089 | 2014 | D | `abstract_only` | Adaptive learning under drift | NR | [A Survey on Concept Drift Adaptation](https://dl.acm.org/doi/10.1145/2523813) |
| LIT-090 | 2016 | D | `abstract_only` | Model-agnostic local explanation | NR | [Why Should I Trust You?: Explaining the Predictions of Any Classifier](https://dl.acm.org/doi/10.1145/2939672.2939778) |
| LIT-091 | 2017 | D | `full_text_verified` | Deep neural networks | NR | [Axiomatic Attribution for Deep Networks](https://proceedings.mlr.press/v70/sundararajan17a.html) |
| LIT-092 | 2017 | D | `full_text_verified` | Deep neural networks | NR | [Learning Important Features Through Propagating Activation Differences](https://proceedings.mlr.press/v70/shrikumar17a.html) |
| LIT-093 | 2021 | D | `full_text_verified` | Recurrent sequence models | NR | [TimeSHAP: Explaining Recurrent Models through Sequence Perturbations](https://dl.acm.org/doi/10.1145/3447548.3467166) |
| LIT-094 | 2021 | D | `full_text_verified` | Autoencoder anomaly detection | NR | [Explaining Anomalies Detected by Autoencoders Using SHAP](https://dl.acm.org/doi/10.1016/j.eswa.2021.115736) |
| LIT-095 | 2005 | D | `abstract_only` | High-dimensional outlier detection | NR | [Feature Bagging for Outlier Detection](https://dl.acm.org/doi/10.1145/1081870.1081891) |
| LIT-096 | 2019 | D | `full_text_verified` | General unsupervised outlier detection | NR | [LSCP: Locally Selective Combination in Parallel Outlier Ensembles](https://epubs.siam.org/doi/10.1137/1.9781611975673.66) |
| LIT-097 | 2021 | D | `full_text_verified` | Large heterogeneous outlier ensembles | NR | [SUOD: Accelerating Large-Scale Unsupervised Heterogeneous Outlier Detection](https://proceedings.mlsys.org/paper_files/paper/2021/file/37385144cac01dff38247ab11c119e3c-Paper.pdf) |
| LIT-098 | 2011 | D | `full_text_verified` | General outlier scoring | NR | [Interpreting and Unifying Outlier Scores](https://epubs.siam.org/doi/10.1137/1.9781611972818.2) |
| LIT-099 | 2021 | D | `full_text_verified` | Image anomaly detection | NR | [Explainable Deep One-Class Classification](https://openreview.net/forum?id=A5VV3UyIQz) |
| LIT-100 | 2016 | D | `abstract_only` | Unsupervised outlier detection benchmarks | NR | [On the Evaluation of Unsupervised Outlier Detection: Measures, Datasets, and an Empirical Study](https://dl.acm.org/doi/10.1007/s10618-015-0444-8) |

## Numeric-use boundary

The three numerically extracted records are LIT-007, LIT-012, and LIT-013. LIT-007 and LIT-012 are Category C; LIT-013 is Category B. None is Category A, so none supports a claim that this project is numerically superior. All 27 abstract-only and four metadata-only records have `NR` in the numerical fields.
