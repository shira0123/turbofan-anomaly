# Table 1. Dataset and experimental-protocol summary

Counts are committed split/protocol facts. The manifest name `test` is reported in the manuscript as internal held-out; the separate official NASA test was not accessed.

<!-- canonical-sha256: cbe4485f8f5e81e0838bbac56bb4066005cfe7cf40e0d8dff97f3264b844d739 -->

| Partition | Manifest name | Engines | Cycle rows | Length-30 windows | Role | Fitting allowed | Evidence status |
|---|---|---|---|---|---|---|---|
| Training | train | 156 | 32107 | 27583 | Fit preprocessing, detectors, calibrators, and training-reference thresholds | Yes—only registered training populations | Development/fitting |
| Validation | validation | 52 | 10873 | 9365 | Select K, models, and alert policy under registered proxies | No learned-state fitting | Validation/model selection |
| Internal held-out | test | 52 | 10779 | 9271 | First valid frozen confirmatory evaluation | No refit, recalibration, reselection, or fusion | Completed internal held-out |
| Official NASA test | external/deferred | NR | NR | NR | Separately preregistered future external evaluation | Outside completed study | Not accessed; deferred |
