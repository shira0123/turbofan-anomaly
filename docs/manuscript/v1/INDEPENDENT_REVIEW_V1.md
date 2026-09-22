# Independent Review of Manuscript V1

## Review scope and evidence boundary

This review was recorded before any manuscript corrections. It independently checked the reader-facing claims in `MANUSCRIPT_V1.md` and `manuscript_v1.tex` against the frozen aggregate/configuration authorities, implementation source, manuscript evidence map, claims audit, and generated assets already present at evidence base commit `f760536ace49801ff72fcc1d30b82e642fa4c93e`. The review did not open raw or derived datasets, model artifacts, score traces, per-engine outputs, or protected test records; it did not run training, inference, evaluation, tuning, or metric recomputation.

Severity meanings are: **critical**, invalidates a central scientific result or creates an unsafe/misleading conclusion; **major**, materially changes the interpretation of the method or a registered criterion; **minor**, affects precision, reproducibility, or reader comprehension without changing the reported result; **editorial**, affects presentation rather than scientific meaning.

## Summary

No unsupported numerical result, fabricated comparison, equation error, leakage claim, or evidence-boundary breach was found. The frozen PCA result set, proxy definitions, state machine, attribution equation, and literature-comparability conclusion are supported by the cited authorities. The review identified **0 critical, 2 major, 5 minor, and 2 editorial findings**. Both major findings are manuscript wording errors: the pipeline is described too broadly as “healthy-only,” and one research question changes the registered inclusive false-alert boundary into a strict one.

## Findings recorded before correction

### IR-01 — Major — “Healthy-only pipeline” overstates the fitted population

- **Location:** Abstract; Conclusion; related contextual wording.
- **Problem:** “Healthy-only, condition-aware anomaly-alerting pipeline” and “condition-aware, healthy-only reconstruction pipeline” can be read to mean that every learned preprocessing component uses early-life rows. That is false for the selected P1/K=6 representation: the operating-setting scaler and K-Means model use all training-engine rows. Only the sensor scalers, detector/feature scaler, and empirical score calibration use the eligible early-life training population.
- **Evidence:** `src/turbofan_anomaly/data/preprocessing.py`, `RegimeSensorPreprocessor.fit`; `configs/preprocessing/fd002-preprocessing-selection-v1.json`; `docs/manuscript/v1/EVIDENCE_MAP.md` rows for P1/K=6 and training eligibility. The manuscript’s own Table 2 already states the correct split population.
- **Required correction:** Replace the blanket “healthy-only pipeline” label with population-specific language, for example “condition-aware pipeline with an early-life-trained reconstruction detector,” and state the two fitting populations explicitly at first use.
- **Disposition:** Correct in V1; no numerical result changes.

### IR-02 — Major — Research question makes the registered feasibility boundary strict

- **Location:** Introduction, research question 2.
- **Problem:** The question asks whether the policy can keep the false-positive rate “below 6%.” The registered decision rule is inclusive: at or below 60 false-positive active endpoints per 1,000 proxy-healthy endpoints, equivalent to at or below 6%. Although all reported values happen to be strictly below 6%, changing `<=` to `<` misstates the preregistered criterion.
- **Evidence:** `configs/alerting/fd002-alert-policy-study-protocol-v2.json`, `selection_objective.feasibility.operator = less_than_or_equal` and `maximum = 60.0`; `src/turbofan_anomaly/evaluation/alerts.py`, `aggregate_candidate_metrics`; `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json`, `evaluation.validation_targets.maximum_endpoint_false_alert_rate_percent = 6.0`.
- **Required correction:** Change “below 6%” to “at or below 6%.”
- **Disposition:** Correct in V1; reported attainment remains unchanged.

### IR-03 — Minor — Scientific contributions and governance/engineering contributions are blended

- **Location:** End of Introduction; Discussion.
- **Problem:** One contribution list combines empirical/methodological contributions with the project’s evidence-governance trail. This makes the paper’s scientific novelty harder to distinguish from reproducibility engineering.
- **Evidence:** The method and result authorities support the empirical findings; `ARTIFACT_PROVENANCE.json`, the claims audit, and the staged gate records support governance and traceability. These are different contribution classes.
- **Required correction:** Separate the scientific/empirical contributions from the reproducibility and evidence-governance contribution, while retaining the bounded novelty statement.
- **Disposition:** Correct in V1.

### IR-04 — Minor — Project-local shorthand is not fully self-contained

- **Location:** Data and Experimental Design; Methodology; Reproducibility.
- **Problem:** P0, P1/K=6, “mode,” “endpoint,” “proxy-healthy,” “internal held-out,” and Gate 4 are understandable from context but not all receive a compact first-use definition suitable for a reader without repository knowledge.
- **Evidence:** `configs/preprocessing/fd002-preprocessing-selection-v1.json`; `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json`; `src/turbofan_anomaly/evaluation/proxies.py`; `src/turbofan_anomaly/alerting/persistence.py`.
- **Required correction:** Add a short terminology paragraph and consistently describe Gate 4 as a project-specific pre-held-out policy-freeze checkpoint.
- **Disposition:** Correct in V1.

### IR-05 — Minor — “Only Gate 4 is mentioned here, once” is factually false

- **Location:** Reproducibility and Data Governance.
- **Problem:** Gate 4 appears in the abstract, a figure caption, and the reproducibility section. The sentence is also an editorial aside rather than scientific content.
- **Evidence:** Text search of `MANUSCRIPT_V1.md` and the generated LaTeX source.
- **Required correction:** Remove the frequency claim and retain only the definition of Gate 4 as project-local terminology.
- **Disposition:** Correct in V1.

### IR-06 — Minor — Repository/manuscript status is stale

- **Location:** Reproducibility and Data Governance.
- **Problem:** “Manuscript preparation in progress” does not describe a completed V1 entering independent/guide review.
- **Evidence:** Existing V1 manuscript, LaTeX source, claims audit, checklist, figures, tables, and this independent review.
- **Required correction:** State that Manuscript V1 and the independent review are complete and guide review is pending; preserve the official-test deferral.
- **Disposition:** Correct in V1 and handoff documents.

### IR-07 — Minor — LaTeX build status is not demonstrated

- **Location:** `BUILD.md`; `manuscript_v1.tex`; handoff expectations.
- **Problem:** The repository contains generated LaTeX but no compiled manuscript PDF or documented successful TeX-engine run. Source-level checks cannot establish typography, float placement, or bibliography rendering.
- **Evidence:** Toolchain inspection found no `pdflatex`, `xelatex`, `lualatex`, `latexmk`, `bibtex`, or `biber` in the current environment. The existing build record documents source generation and verification, not compilation.
- **Required correction:** Package portable LaTeX sources and explicitly label compilation as not executed in this environment. Produce a clearly identified alternative guide-review rendering if possible, without representing it as LaTeX output.
- **Disposition:** Address in review package; unresolved only as actual LaTeX compilation.

### IR-08 — Editorial — Reader-facing literature table is too wide

- **Location:** Table 4 in Markdown and generated LaTeX.
- **Problem:** Nine columns, including internal evidence-locator detail, impede guide-review readability and are likely to render too small or overflow. The exact evidence remains valuable for audit but need not occupy the principal comparison table.
- **Evidence:** `tables/table_04_literature_comparison.md`, `.tex`, and `.csv`; current manuscript table declaration.
- **Required correction:** Use a compact reader-facing table while preserving exact evidence in the machine-readable CSV/evidence map, or use a documented landscape presentation in the review rendering.
- **Disposition:** Correct presentation in V1/package; retain machine-readable evidence.

### IR-09 — Editorial — Boundary language is repetitive in the closing sections

- **Location:** Evidence interpretation, Discussion, Limitations, Reproducibility, and Conclusion.
- **Problem:** Several limitations—proxy rather than physical onset, internal rather than external evaluation, non-causal attribution, and no fusion—are repeated nearly verbatim. The repetition is defensible but slows the argument and obscures the central trade-off.
- **Evidence:** Sections 6.5–10 of `MANUSCRIPT_V1.md`.
- **Required correction:** Consolidate repeated caveats while keeping each claim boundary at the point where it is first needed and in the final limitations/conclusion.
- **Disposition:** Correct conservatively; do not remove scientific qualifications.

## Verified claims retained without correction

- The whole-engine 156/52/52 split and one-time internal held-out evaluation are supported.
- P1/K=6 uses six learned operating-context clusters and early-life per-mode sensor scaling, with the operating-setting scaler and K-Means fitted on all training rows.
- Windowing is engine-local, 30 cycles by 21 sensors, stride one; the PCA input is 63 ordered summary features using population standard deviation and endpoint-minus-start change.
- PCA reconstruction MSE, right-sided empirical-CDF calibration, per-mode 99.5th-percentile thresholds, strict comparison, EWMA alpha 0.20, persistence eight, and engine/gap reset semantics match implementation and protocol.
- The final-10/20/30% normalized-life proxies, FAR denominator, coverage denominator, conditional delay, crossing-event exclusion, and average-precision implementation match their authorities.
- The three held-out FAR, coverage, delay, PR-AUC, and ROC-AUC values match the frozen aggregate result source and generated tables.
- The 6% FAR objective was met under all three endpoint proxies; the 12-cycle aggregate delay aspiration was not met.
- The 21 PCA sensor contributions sum to raw 63-feature PCA MSE and are correctly bounded as non-causal model-fidelity explanations.
- The literature set contains 20 manuscript-grade papers, 43 located values, and Category A/B/C/D counts of 0/2/11/7; no numerical superiority claim is supported or made.

## Unresolved items after planned V1 correction

The only expected unresolved review item is a successful native LaTeX compilation and visual inspection in an environment with a TeX engine. This is a tooling limitation, not a scientific-evidence gap. All other findings are correctable in source or presentation without reopening protected evidence or recomputing results.

## Post-correction disposition

- **IR-01 through IR-06:** resolved in `MANUSCRIPT_V1.md` and synchronized `manuscript_v1.tex`.
- **IR-07:** partially resolved. The portable LaTeX package was extracted and reference-checked, and complete alternative PDF/DOCX renderings were produced and inspected; native LaTeX compilation remains unresolved because no TeX engine is installed.
- **IR-08:** resolved for guide review by a landscape reader-facing Table 4 plus a separate evidence-locator display; no table content was omitted.
- **IR-09:** resolved conservatively. Claim boundaries remain present, while redundant review/package wording was consolidated.

No unresolved scientific decision remains. Author metadata, venue selection, and native LaTeX compilation are the remaining guide/production actions.
