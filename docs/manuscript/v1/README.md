# Manuscript V1 evidence foundation

## Purpose and scope

This directory contains the complete venue-neutral manuscript V1, its manuscript-specific claims and review records, the verified evidence foundation, and a reproducible figure/table bundle for the FD002 context-aware anomaly-alert study. The manuscript introduces no new scientific results; it synthesizes committed aggregate evidence under the registered claim boundaries.

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
- `MANUSCRIPT_V1.md` is the editorial source of truth for the complete paper.
- `manuscript_v1.tex` is the deterministically rendered venue-neutral LaTeX counterpart.
- `references_v1.bib` is the 20-entry cited subset copied from the verified core bibliography.
- `MANUSCRIPT_CLAIMS_AUDIT_V1.md` records the authority, support status, and caveat for each major claim.
- `MANUSCRIPT_REVIEW_CHECKLIST_V1.md` records scientific, citation, asset, equation, originality, placeholder, and guide review status.
- `PLAIN_LANGUAGE_SUMMARY.md` gives a one-page nontechnical explanation for the guide and project team.
- `INDEPENDENT_REVIEW_V1.md` records findings by severity, evidence, proposed correction, and disposition before correction.
- `REVISION_LOG_V1.md` records the evidence-preserving corrections applied after independent review.
- `review_package/` contains the guide-review PDF and DOCX, guide feedback form, and verified portable LaTeX-source ZIP.

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

## Manuscript V1 status

1. Evidence foundation and detailed outline: complete.
2. Reproducible figures, diagrams, tables, captions, and provenance: complete.
3. Complete Markdown manuscript and synchronized venue-neutral LaTeX source: complete.
4. Cited bibliography subset, manuscript claims audit, review checklist, and plain-language summary: complete.
5. Static numerical, citation, path, terminology, cross-format, hash, and LaTeX-structure checks: complete.
6. Independent evidence audit and supported V1 corrections: complete (0 critical, 2 major, 5 minor, 2 editorial findings).
7. Guide-review PDF/DOCX and portable LaTeX package: complete and visually/source-package verified.
8. Author/affiliation placeholders and venue selection: deliberately unresolved for guide/author action.
9. Official NASA-test evaluation: deferred and outside manuscript V1.

## Generated artifact bundle

- Architecture, protocol, operational-results, ranking-results, and validation-comparison figures are in `figures/` as SVG and 300-dpi PNG.
- Editable figure sources are in `figure_sources/figure_specs.json`, `figure_sources/system_architecture.dot`, and `figure_sources/experimental_protocol.dot`.
- Dataset/protocol, frozen-policy, confirmatory-result, and focused-literature tables are in `tables/` as CSV, Markdown, and LaTeX.
- Run `python scripts/manuscript/generate_manuscript_v1_assets.py --repo-root .` to regenerate the complete bundle.
- Run `python scripts/manuscript/verify_manuscript_v1_assets.py --repo-root .` to verify exact registered values, cross-format digests, citations, vector/raster structure, 300-dpi metadata, and provenance hashes.
- Run `python scripts/manuscript/render_manuscript_v1_latex.py` after editing the Markdown source.
- Run `python scripts/manuscript/verify_manuscript_v1.py --repo-root .` to verify manuscript structure, citations, major values, paths, terminology, cross-format consistency, LaTeX structure, and document provenance.
- Open `review_package/MANUSCRIPT_V1_GUIDE_REVIEW.pdf` first for guide review. It is a 19-page Microsoft Edge HTML/MathML rendering, explicitly not a LaTeX compilation.
- `review_package/MANUSCRIPT_V1_GUIDE_REVIEW.docx` is the editable Microsoft Word conversion. Its 19-page Word rendering was inspected separately and contains five figures, five rendered tables, and ten editable equations.
- `review_package/manuscript_v1_latex_source.zip` contains 12 files: synchronized TeX, the 20-entry BibTeX file, five PNG figures, four LaTeX table fragments, and a build README. It was extracted and all referenced paths resolved.

Graphviz, Matplotlib, an SVG converter, and a LaTeX engine were unavailable; no dependency was installed. The committed SVGs are produced by a deterministic standard-library primitive renderer, while PNG previews use Windows `System.Drawing`. DOT sources remain available for later Graphviz rendering. The complete LaTeX source and its included table fragments passed static and portable-package checks but were not compiled. The PDF was printed locally from a complete HTML/MathML rendering with Microsoft Edge; the DOCX was produced with installed Microsoft Word. Every page of both final renderings was visually inspected through the Windows native PDF renderer.

No artifact reconstructs score traces, invents curves or intervals, or reruns evaluation. A later venue-formatting or scientific-extension task must preserve the same boundary unless separately registered.
