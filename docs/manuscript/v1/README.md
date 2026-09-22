# Manuscript V1 evidence foundation

## Purpose and scope

This directory prepares the evidence foundation and detailed outline for a first manuscript about the FD002 context-aware anomaly-alert study. It does not contain a full manuscript, generated figures, or new scientific results.

The intended paper reports a governed, engine-disjoint study of operating-condition-aware preprocessing and frozen anomaly-alert behavior on an internal held-out partition. The reported endpoint labels are normalized-life proxies. They are not observed physical fault onsets, and the results are not official NASA-test, operational, production, or real-aircraft estimates.

This work is documentation and evidence synthesis only. It must not trigger data access, model loading, inference, refitting, tuning, threshold selection, fusion, confirmatory reruns, or modifications to existing protocols and scientific authorities. The official NASA-test secondary evaluation remains deferred.

## Contents

- `EVIDENCE_MAP.md` maps proposed numerical and methodological claims to exact repository authorities, JSON keys, tables, and code symbols.
- `OUTLINE.md` provides title options and the detailed manuscript structure.
- `FIGURE_TABLE_PLAN.md` defines future editable diagrams, scientific plots, and tables without generating them.
- `OPEN_QUESTIONS.md` separates blockers for manuscript drafting/publication from optional improvements and future studies.
- `HANDOFF.md` gives a self-contained continuation brief for a new session.

## Evidence hierarchy

When descriptions disagree, use this order:

1. Registered execution/result configs and committed aggregate confirmatory reports.
2. Current implementation and tests for exact computational semantics.
3. Registered split, preprocessing, model-selection, alert-policy, inference, and attribution protocols.
4. The final claims audit for publication boundaries, except where a later registered implementation demonstrably supersedes an implementation-status statement.
5. Decision and progress logs.
6. Explanatory guides and top-level summaries.

Historical prose does not override a registered protocol or implementation. In particular, parts of `docs/guides/PROJECT_UNDERSTANDING_GUIDE.md` and the implementation-status rows FCA-015/FCA-016 in `docs/research/final_claims_audit.json` predate the registered frozen PCA attribution and batch inference implementation. The current implementation supports only the narrow claims recorded in `EVIDENCE_MAP.md`: transform-only batch inference and exact local PCA reconstruction-error decomposition in normalized 63-feature space. It does not support SHAP, causal diagnosis, physical fault localization, streaming operation, online recalibration, or production readiness.

## Primary authorities

### Confirmatory result and policy

- `configs/evaluation/fd002-confirmatory-results-v1.json`
- `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json`
- `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/result.json`
- `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/detector_policy_metrics.csv`
- `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/ranking_metrics.csv`
- `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/summary.json`

### Data, preprocessing, model selection, and alerting

- `configs/splits/fd002-primary-v1.json`
- `configs/preprocessing/fd002-preprocessing-selection-v1.json`
- `configs/baselines/fd002-classical-baselines-v1.json`
- `configs/lstm/fd002-lstm-final-refit-results-v1.json`
- `configs/alerting/fd002-alert-policy-study-protocol-v2.json`
- `configs/alerting/fd002-alert-policy-study-results-v1.json`
- `src/turbofan_anomaly/`

### Claims, literature, and provenance

- `docs/research/FINAL_CLAIMS_AUDIT.md`
- `docs/research/final_claims_audit.json`
- `docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json`
- `docs/research/CORE_LITERATURE_COMPARABILITY_V1.md`
- `docs/research/core_literature_comparability_v1.json`
- `docs/research/CORE_LITERATURE_CLAIMS_IMPLICATIONS_V1.md`
- `docs/research/CORE_LITERATURE_SOURCE_VERIFICATION_V1.md`
- `docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib`
- `docs/research/ARTIFACT_MANIFEST.md`

### Frozen delivery implementation

- `configs/inference/fd002-frozen-inference-protocol-v1.json`
- `docs/research/PCA_SENSOR_ATTRIBUTION_METHOD_V1.md`
- `docs/guides/FROZEN_FD002_INFERENCE_GUIDE.md`
- `reports/inference_validation_v1/validation_regression.json`
- `src/turbofan_anomaly/inference/pipeline.py`
- `src/turbofan_anomaly/explainability/pca_attribution.py`

## Workflow to manuscript V1

1. Obtain the author's decisions recorded as blockers in `OPEN_QUESTIONS.md`.
2. Generate the planned editable SVG diagrams and script-generated plots strictly from committed aggregate authorities.
3. Validate every plotted value and table cell against `EVIDENCE_MAP.md`.
4. Draft the manuscript in Markdown using `OUTLINE.md`.
5. Convert the approved text to the target venue's LaTeX template without changing claim scope.
6. Reuse `docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib` as the citation authority; create a venue-specific BibTeX derivative only if required, preserving the existing keys.
7. Run path, citation-key, numerical-claim, and cross-format consistency checks before review.

## Planned outputs

The next stage may add the following under this directory, subject to author and venue decisions:

- `MANUSCRIPT_V1.md`: complete prose draft.
- `latex/main.tex`: venue-formatted LaTeX source.
- `latex/references.bib`: a mechanically derived, key-preserving copy or subset of the registered core bibliography.
- `figures/*.svg`: editable vector architecture and experimental-protocol diagrams.
- `figures/*.pdf`: publication exports of the editable diagrams.
- `plots/*.svg` and `plots/*.pdf`: script-generated scientific plots from committed aggregate values.
- `tables/*.md` and `tables/*.tex`: synchronized result and literature-comparison tables.
- `scripts/`: deterministic, non-scientific rendering scripts that read only committed aggregate authorities.

No planned plot may reconstruct score traces, invent curves, derive confidence intervals, or rerun evaluation.
