# Manuscript V1 Review Checklist

Status legend: `[x]` checked, `[ ]` requires guide or author action.

## Scientific accuracy

- [x] Dataset, split, row, window, and fitting-window counts agree with registered aggregate authorities.
- [x] P1/K=6 fitting boundaries distinguish all-training-row operating-context fitting from eligible-training-row sensor scaling.
- [x] Window shape, endpoint-mode assignment, 63-feature ordering, `ddof=0`, PCA scoring, and calibration direction agree with implementation.
- [x] Runtime order is calibration → EWMA → strict per-mode threshold → persistence.
- [x] Reset, no-backdating, event, and conditional-delay semantics are explicit.
- [x] LOF validation ranking and PCA operational selection are not conflated.
- [x] Validation evidence and internal held-out evidence are separated.
- [x] All confirmatory numerators, denominators, rates, coverage, delays, PR-AUC, and ROC-AUC agree with the frozen result authority.
- [x] Aggregate delay is identified as the median of three proxy medians.
- [x] Onsets are described as normalized-life evaluation proxies, not physical labels.
- [x] No official NASA-test, external-validation, field-readiness, causal, or physical-root-cause claim is made.

## Citations and bibliography

- [x] Twenty unique manuscript citation keys are present.
- [x] Every key exists in `references_v1.bib` and the verified core bibliography.
- [x] `references_v1.bib` contains only cited entries copied from the verified core bibliography.
- [x] Related-work numerical values retain their verified native meanings and caveats.
- [x] The 20-paper/43-value/0-2-11-7 evidence statement does not imply deep extraction of all 100 discovery items.
- [x] No Category A comparator and strongest Category B wording are bounded to the manuscript-grade evidence set.

## Figures and tables

- [x] Five figures are included and discussed near first use.
- [x] Four generated tables are included and discussed.
- [x] Figure 1 distinguishes PCA primary, LSTM comparator, and no fusion.
- [x] Figures 1 and 2 define the pre-held-out policy freeze and explain project governance Gate 4.
- [x] Figure 2 places official NASA-test evaluation outside the completed study.
- [x] SVG is retained as editable vector authority; LaTeX uses 300-dpi PNG previews.
- [x] Diagram clipping, overlap, arrow direction, boundaries, and text size were visually reviewed after regeneration.

## Equations and cross-format consistency

- [x] Mean, population standard deviation, endpoint change, PCA MSE, empirical CDF, EWMA, threshold comparison, attribution, FAR, and onset equations are present.
- [x] Symbols and denominators match the prose and implementation.
- [x] Markdown is the editorial source; LaTeX is deterministically rendered from it.
- [x] Title, abstract, section order, equations, metrics, figures, tables, citations, limitations, and conclusion agree across formats.
- [x] LaTeX braces/environments and referenced paths pass static validation.
- [x] The 19-page alternative guide PDF and the DOCX's 19-page Word rendering were visually inspected page by page.
- [x] The DOCX contains five figures, five editable rendered tables, and ten native editable Word equations.
- [x] The portable LaTeX ZIP was extracted; all five graphics, four table inputs, and the bibliography reference resolved inside the archive.
- [ ] Compile LaTeX when a preinstalled engine is available; none was present during manuscript V1 preparation.

## Originality review

- [x] Prose was written specifically for this manuscript; no paper abstract or long quotation was copied.
- [x] A local phrase-overlap scan was run against available extracted evidence and project documentation.
- [x] Exact 10-word matches were limited to the required comparator conclusion and two project-specific implementation phrases; no source-paper sentence pattern requiring revision was identified.
- [x] Citation ambiguity and unattributed numerical claims were reviewed against the claims audit.

This was a local originality review, not a Turnitin or other commercial similarity result. Expected technical overlaps—dataset names, registered policy labels, equations, exact metrics, and bibliography metadata—were not treated as evidence of copied prose.

## Terminology and claim restraint

- [x] First abstract occurrence defines project governance Gate 4 in external-facing language.
- [x] Later uses prefer “pre-held-out policy freeze” or “frozen policy.”
- [x] No unexplained Gate 4 label remains in manuscript or affected diagrams.
- [x] No unsupported “novel,” “state-of-the-art,” “superior,” “real-time,” first-ever, or accuracy claim appears.
- [x] Attribution is explicitly non-causal and is not physical fault localization.

## Unresolved placeholders

- [ ] `[AUTHOR 1]`
- [ ] `[AUTHOR 2]`
- [ ] `[DEPARTMENT]`
- [ ] `[INSTITUTION]`
- [ ] `[CITY, COUNTRY]`
- [ ] `[CORRESPONDING EMAIL]`

## Questions for the guide

1. Confirm author order, affiliation spelling, location, and corresponding-author email.
2. Choose a target venue only after accepting the venue-neutral scientific text; formatting and word limits may then require a separate submission task.
3. Decide whether the 20-paper focused review is sufficient for the intended venue or whether a separately governed literature update is needed.
4. Decide whether uncertainty analysis, another engine-disjoint split, or official NASA-test evaluation should be preregistered as new work rather than added retrospectively to this result.

## Final release checks

- [x] Claims audit complete.
- [x] Independent findings were recorded before correction and post-correction dispositions were added.
- [x] Asset and manuscript verifiers pass.
- [x] Guide PDF, editable DOCX, feedback form, and portable LaTeX-source ZIP are complete.
- [x] Protected scientific-source hashes remain unchanged.
- [x] `git diff --check` passes.
- [x] Changed Python scripts compile.
- [x] Work was documentation-only: no dataset, model artifact, score trace, per-engine file, or temporary PDF was opened.
- [x] No scientific workflow, dependency operation, or remote operation was performed.
