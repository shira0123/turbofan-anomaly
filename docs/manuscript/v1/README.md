# Manuscript V1 evidence foundation

## Purpose and scope

This directory contains the verified evidence foundation, detailed outline, and reproducible figure/table bundle for a first manuscript about the FD002 context-aware anomaly-alert study. It does not yet contain the full manuscript and introduces no new scientific results.

The intended paper reports a governed, engine-disjoint study of operating-condition-aware preprocessing and frozen anomaly-alert behavior on an internal held-out partition. The reported endpoint labels are normalized-life proxies. They are not observed physical fault onsets, and the results are not official NASA-test, operational, production, or real-aircraft estimates.

This work is documentation and evidence synthesis only. It must not trigger data access, model loading, inference, refitting, tuning, threshold selection, fusion, confirmatory reruns, or modifications to existing protocols and scientific authorities. The official NASA-test secondary evaluation remains deferred.

## Contents

- `EVIDENCE_MAP.md` maps proposed numerical and methodological claims to exact repository authorities, JSON keys, tables, and code symbols.
- `OUTLINE.md` provides title options and the detailed manuscript structure.
- `FIGURE_TABLE_PLAN.md` defines the editable diagrams, scientific plots, and tables implemented by the artifact bundle.
- `OPEN_QUESTIONS.md` separates blockers for manuscript drafting/publication from optional improvements and future studies.
- `HANDOFF.md` gives a self-contained continuation brief for a new session.
- `figures/` contains five SVG publication figures and matching 300-dpi PNG previews.
- `figure_sources/` contains the shared editable JSON specification and DOT diagram sources.
- `tables/` contains synchronized CSV, Markdown, and LaTeX versions of four manuscript tables.
- `CAPTIONS.md` contains self-contained figure and table captions.
- `ARTIFACT_PROVENANCE.json` records artifact/source hashes, source selectors, commands, software versions, and scientific-boundary declarations.
- `BUILD.md` records exact regeneration and verification commands plus renderer limitations.

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

1. Evidence foundation and outline: complete.
2. Reproducible figures, diagrams, tables, captions, and provenance: complete.
3. Next: resolve the manuscript decisions in `OPEN_QUESTIONS.md` and synthesize the full Markdown manuscript from `OUTLINE.md` with verified citations.
4. Convert approved text to the target venue's LaTeX template without changing claim scope.
5. Reuse `docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib` as the citation authority; create a venue-specific BibTeX derivative only if required, preserving the existing keys.
6. Run path, citation-key, numerical-claim, and cross-format consistency checks before review.

## Generated artifact bundle

- Architecture, protocol, operational-results, ranking-results, and validation-comparison figures are in `figures/` as SVG and 300-dpi PNG.
- Editable figure sources are in `figure_sources/figure_specs.json`, `figure_sources/system_architecture.dot`, and `figure_sources/experimental_protocol.dot`.
- Dataset/protocol, frozen-policy, confirmatory-result, and focused-literature tables are in `tables/` as CSV, Markdown, and LaTeX.
- Run `python scripts/manuscript/generate_manuscript_v1_assets.py --repo-root .` to regenerate the complete bundle.
- Run `python scripts/manuscript/verify_manuscript_v1_assets.py --repo-root .` to verify exact registered values, cross-format digests, citations, vector/raster structure, 300-dpi metadata, and provenance hashes.

Graphviz, Matplotlib, an SVG converter, and a LaTeX engine were unavailable; no dependency was installed. The committed SVGs are produced by a deterministic standard-library primitive renderer, while PNG previews use Windows `System.Drawing`. DOT sources remain available for later Graphviz rendering, and LaTeX table fragments remain uncompiled.

No artifact reconstructs score traces, invents curves or intervals, or reruns evaluation. The next-stage prose draft must preserve the same boundary.
