# Final Claims Audit

**Audit ID:** `fd002-final-claims-audit-v1`
**Audit date:** 2026-09-01
**Metric authority:** `configs/evaluation/fd002-confirmatory-results-v1.json`
**Literature authority:** `docs/research/LITERATURE_EVIDENCE_MATRIX_V4.json`

## Strongest defensible contribution statement

A governed, condition-aware, engine-disjoint FD002 anomaly-alert pipeline that froze preprocessing, detector, calibration, and alert policy before internal held-out access and transparently reports proxy-sensitive FAR, coverage, and delay with independent reproduction.

This is a research-governance and system-integration contribution. It is not a claim that PCA, K-Means, per-regime scaling, EWMA, persistence, or the LSTM autoencoder is a new algorithm.

## Status summary

| Classification | Count |
|---|---:|
| `supported_confirmatory` | 8 |
| `supported_validation_only` | 2 |
| `supported_implementation` | 3 |
| `partially_supported` | 1 |
| `not_supported` | 2 |
| `future_work` | 0 |
| `prohibited_wording` | 1 |

## Audited claims

The detailed limitations and prohibited wording for every row are preserved in [`final_claims_audit.json`](final_claims_audit.json).

| ID | Topic | Evidence classification | Permitted paper wording |
|---|---|---|---|
| FCA-001 | engine-disjoint evaluation | `supported_confirmatory` | A deterministic engine-disjoint split was used, with 156 training, 52 validation, and 52 internal held-out engines. |
| FCA-002 | P1/K=6 preprocessing | `supported_implementation` | P1/K=6 scales sensors with training-fitted, operating-mode-aware state and assigns endpoint mode from registered cycle context. |
| FCA-003 | multiple detector comparison | `supported_validation_only` | PCA, LOF, One-Class SVM, Isolation Forest, and an LSTM autoencoder were compared on registered validation proxies. |
| FCA-004 | three-seed LSTM ensemble | `supported_confirmatory` | The pre-registered three-seed LSTM ensemble was evaluated without score or decision fusion. |
| FCA-005 | frozen alert-policy grid | `supported_validation_only` | The frozen validation study evaluated 1,280 registered alert candidates across five proxy policies. |
| FCA-006 | endpoint FAR target | `supported_confirmatory` | Endpoint FAR was 3.2440%, 0.9443%, and 0.5153% for final-10%, final-20%, and final-30% proxies, respectively. |
| FCA-007 | delay aspiration | `supported_confirmatory` | Aggregate median held-out delay was 25 cycles; only final-10% had median delay exactly 12 cycles. |
| FCA-008 | proxy sensitivity | `supported_confirmatory` | Results are proxy-sensitive: PCA coverage ranged from 51.92% to 84.62% and median delay from 12 to 42.5 cycles. |
| FCA-009 | PCA held-out trade-off | `supported_confirmatory` | The PCA policy generalized from validation selection to a lower-FAR but lower-coverage and later-alert internal held-out profile than the frozen LSTM comparator. |
| FCA-010 | LSTM complementarity | `partially_supported` | The LSTM had higher coverage and slightly earlier median alerts, but also higher FAR, on each registered endpoint proxy. |
| FCA-011 | no post-test reselection | `supported_confirmatory` | The first valid confirmatory run used the pre-registered frozen PCA primary and unfused LSTM comparator without reselection. |
| FCA-012 | official NASA test boundary | `supported_confirmatory` | No official NASA-test result is reported. |
| FCA-013 | fault-onset annotations | `supported_implementation` | The study evaluates final-10%, final-20%, and final-30% normalized-life proxy onsets. |
| FCA-014 | reproducible prototype | `supported_implementation` | The work is a reproducible research prototype within its registered local artifact and environment boundaries. |
| FCA-015 | explainability status | `not_supported` | Explainability is planned; no current output should be called SHAP or causal fault attribution. |
| FCA-016 | API and deployment status | `not_supported` | A governed inference interface remains implementation work. |
| FCA-017 | novelty and superiority language | `prohibited_wording` | The defensible contribution is a governed, condition-aware, engine-disjoint FD002 anomaly-alert pipeline with frozen pre-test choices and transparent proxy-sensitive results. |

## Non-negotiable wording boundaries

- Say **internal held-out proxy result**, never official NASA-test, physical-onset, operational, or production performance.
- Report FAR together with proxy, coverage, and delay; do not reduce the result to an accuracy headline.
- State that the aggregate delay aspiration was missed.
- Describe the LSTM as the frozen unfused comparator, not the selected primary model.
- Do not claim explainability or an API exists. Native PCA contribution attribution remains unimplemented.
- Do not use `first`, `state of the art`, `superior`, or `outperforms` language.

## Major limitations

The project uses one simulated FD002 fleet split; proxy onsets rather than observed physical fault onset; one internal confirmatory partition without external or official-test evaluation; incomplete engine-level uncertainty; no protocol-equivalent Category A published comparator; local/ignored raw data and model artifacts; no lockfile; and no validated explanations, inference API, deployment monitoring, or real-aircraft validation.
