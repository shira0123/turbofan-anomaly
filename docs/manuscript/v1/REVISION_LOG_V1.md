# Manuscript V1 Revision Log

## Review basis

The independent findings in `INDEPENDENT_REVIEW_V1.md` were recorded before these changes. Corrections were limited to evidence-supported manuscript wording, reader definitions, reproducibility status, and guide-review packaging. No dataset, model artifact, score trace, per-engine output, training/inference/evaluation workflow, tuning procedure, or metric recomputation was used.

## Corrections

| Finding | Files/section | Correction | Scientific evidence changed? |
|---|---|---|---|
| IR-01 (major) | Abstract; Conclusion; review-package table wording | Replaced blanket “healthy-only pipeline” language with population-specific wording: operating-setting scaler/K-Means use all training rows, while sensor scalers, detector/feature scaler, and calibration use eligible early-life training data. | No |
| IR-02 (major) | Introduction, research question 2 | Changed “below 6%” to the registered inclusive “at or below 6%.” | No |
| IR-03 (minor) | Introduction | Separated scientific/empirical contributions from reproducibility/governance contributions. | No |
| IR-04 (minor) | Data and Experimental Design | Defined P0, P1/K=6, mode, endpoint, proxy-healthy, and internal held-out at first consolidated use. | No |
| IR-05 (minor) | Reproducibility and Data Governance | Removed the false claim that Gate 4 appears only once; retained its project-specific meaning. | No |
| IR-06 (minor) | Reproducibility; README; HANDOFF | Updated status from manuscript preparation to completed V1 independent audit and guide-review package. | No |
| IR-07 (minor) | BUILD; review-package README; source ZIP | Documented that no TeX engine is installed, packaged all portable sources, and labeled the guide PDF as a Microsoft Word rendering rather than a LaTeX compilation. | No |
| IR-08 (editorial) | Guide-review rendering | Presented wide tables in landscape sections while retaining exact evidence in CSV/evidence-map authorities. | No |
| IR-09 (editorial) | Closing sections | Retained all scientific boundaries but removed or shortened only redundant packaging/editorial language where needed for the guide rendering. | No |

## Generated-source synchronization

After editing `MANUSCRIPT_V1.md`, `manuscript_v1.tex` was regenerated with the repository renderer. The existing static manuscript and asset verifiers were rerun. The portable source ZIP was built only from manuscript source, bibliography, required figures/tables, and a build README; archive contents were extracted to a temporary directory and checked against all LaTeX references.

## Deliberately unchanged evidence

- Internal held-out FAR, coverage, delay, PR-AUC, and ROC-AUC values.
- The 156/52/52 engine split and 52-engine internal held-out population.
- The P1/K=6 selection and its validation evidence.
- Window, feature, PCA, calibration, threshold, EWMA, persistence, reset, event, and proxy definitions.
- The 6% FAR objective and 12-cycle delay aspiration outcomes.
- PCA attribution completeness and non-causal interpretation.
- Literature corpus size, extracted-value count, comparability categories, and no-Category-A conclusion.
- Deferred official NASA-test boundary and no-fusion boundary.

## Remaining limitation

Native LaTeX compilation remains unexecuted because no TeX engine is installed in the review environment. This is a packaging/toolchain limitation; it does not alter the generated `.tex` source or scientific claims. The guide-review PDF and DOCX are alternative Microsoft Word renderings and are labeled accordingly.
