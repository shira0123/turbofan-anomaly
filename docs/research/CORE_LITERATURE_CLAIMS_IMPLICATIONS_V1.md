# Core Literature Claims Implications V1

This is a proposed manuscript-synthesis aid. It does not modify or supersede `FINAL_CLAIMS_AUDIT.md`, `final_claims_audit.json`, any protocol, or any confirmatory result.

## Claims supported for later synthesis

- The manuscript may describe the frozen pipeline as an engine-disjoint, condition-aware, healthy-only reconstruction study evaluated with explicit proxy labels and persistent event semantics.
- Literature supports the methodological importance of operating-condition normalization, reconstruction-based monitoring, dynamic/error postprocessing, persistence/event evaluation, and sensor-wise reconstruction-residual decomposition.
- The strongest partial comparator (`LIT-013`) supports discussing closely related FD002 unsupervised LSTM-autoencoder work, provided its within-engine split, final-10% proxy, adaptive threshold, and five-window persistence are stated.
- The frozen PCA policy met the endpoint FAR objective on all three internal held-out proxies; aggregate median delay was 25 cycles and missed the 12-cycle aspiration. This statement derives only from the committed confirmatory authority.
- PCA sensor attribution is observational reconstruction-error decomposition, not physical fault localization or causal diagnosis.

## Claims that remain prohibited

- State of the art, superiority over published methods, first-ever status, or literature outperformance.
- Official NASA-test performance, observed physical fault onset, production readiness, operational false-alarm rates, or real-aircraft generalization.
- Direct comparison of RUL RMSE/NASA score, window F1, laboratory detection rate, or point-adjusted metrics with the project's endpoint FAR, coverage, delay, PR-AUC, or ROC-AUC.
- Claims that the calibrated LSTM ensemble is the selected primary detector or that score fusion/online recalibration was evaluated.
- Physical localization claims based on PCA reconstruction attribution.

## Required comparability sentence

> No directly protocol-equivalent published comparator was identified in the manuscript-grade core literature set.

## Literature limitations to disclose

The closest studies differ in at least one material dimension: C-MAPSS subset, engine separation, proxy onset, use of anomalous data for threshold selection, official-test terminal-RUL evaluation, operating-condition treatment, metric aggregation, point adjustment, or alert-event semantics. `NR` fields must remain unresolved rather than inferred. `LIT-019` was replaced by preregistered reserve `LIT-051` because complete legal full text was unavailable, not because of its result.

## Official-test implication

The literature supports a future preregistered secondary official-test RUL-proxy evaluation with the already frozen detector. Such a study would test external trajectory generalization but would not create physical-onset labels or a directly comparable literature benchmark. It requires separate authorization before local official-test access.
