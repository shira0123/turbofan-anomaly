# Manuscript V1 open questions

The evidence foundation and outline are not blocked. The items below must be resolved before a complete manuscript can be finalized or submitted.

## Genuine blockers for the full manuscript

### 1. Author and affiliation metadata

- What are the verified author names, order, affiliations, addresses, corresponding author, and contact details?
- Are ORCID identifiers required and verified?

These details are not present in the repository and must remain TODO until supplied by the author.

### 2. Target venue and article type

- Which journal/conference and article type should V1 target?
- What are its word, abstract, figure, table, reference, data-availability, and supplementary-material limits?
- Does it require structured headings, a graphical abstract, highlights, author-contribution statements, or a specific LaTeX class?

The venue decision controls formatting and space allocation but does not change scientific claims.

### 3. Final title and emphasis

- Choose one working title from `OUTLINE.md` or provide a replacement.
- Decide whether the main emphasis is context-aware preprocessing, governed alert-policy evaluation, or the complete integrated pipeline.

The title must not imply official NASA-test evaluation, physical fault localization, production readiness, or algorithmic novelty.

### 4. Versioned resolution of the claims-audit implementation-status conflict

`docs/research/final_claims_audit.json` FCA-015/FCA-016 says attribution and inference were not implemented. Later registered artifacts and current code show a hash-checked batch inference path and exact PCA reconstruction-error contribution decomposition:

- `configs/inference/fd002-frozen-inference-protocol-v1.json`
- `reports/inference_validation_v1/validation_regression.json`
- `src/turbofan_anomaly/inference/`
- `src/turbofan_anomaly/explainability/pca_attribution.py`
- `docs/research/PCA_SENSOR_ATTRIBUTION_METHOD_V1.md`

For this foundation, the conflict is resolved by source precedence and recorded in `EVIDENCE_MAP.md`. Before final manuscript approval, the author should authorize either a versioned claims-audit addendum or a new audit version. The existing audit must remain unchanged. Any update must preserve the limitations: not SHAP, non-causal, no physical localization, batch-only, and not production deployment.

### 5. Scope of delivery and attribution material

- Should the batch inference and sensor-contribution implementation appear in the main methodology, an appendix, or future-work discussion?
- Is the paper intended primarily as an evaluation paper or also as a reproducible prototype paper?

The capability is supported as implementation evidence but contributes no new held-out performance result.

### 6. Author approval of final wording

- The author must approve the claims, limitations, table captions, and abstract language before V1 is considered final.
- In particular, approve the explicit statement that the FAR objective was met across all three proxies while the 25-cycle aggregate delay missed the 12-cycle aspiration.

## Publication choices that are not scientific blockers

### Main-text versus supplementary placement

- Put the 20-paper comparability table in the main text, supplement, or both?
- Include the optional validation-only five-model comparison figure, or retain only the frozen held-out figures?
- Include the metric-definition table in the main text or appendix?
- Keep the attribution details in the main text or a reproducibility appendix?

### Result presentation

- Use FAR/1,000 as the primary display with FAR % in a secondary column, or show both equally?
- Show numerator/denominator counts directly in the frozen result table or in a footnote?
- Use a three-panel bar chart or categorical point chart for FAR/coverage/delay?

Recommendation: make FAR/1,000 primary because it names the implemented denominator; retain FAR % for continuity with the preregistered 6% objective.

### Terminology

- Use “internal held-out” consistently in prose while explaining once that the manifest labels the partition `test`.
- Prefer “endpoint false-positive alert rate” or “endpoint FAR” after giving the exact definition.
- Use “operating modes” or “operating-context clusters,” not “physical regimes,” unless externally validated.

## Resolved discrepancies and corrected assumptions

These are not open questions unless the author wants to change manuscript scope.

1. **PCA input:** It is a 63-feature vector—21 means, 21 population SDs, and 21 endpoint-minus-start differences—not a flattened `30×21` window.
2. **Standard-deviation convention:** `numpy.std(axis=1)` uses `ddof=0`, so the window SD uses divisor 30.
3. **FAR denominator:** FAR/1,000 is false-positive active endpoints divided by proxy-healthy endpoints, multiplied by 1,000. FAR % is the same endpoint ratio ×100. It is not the percentage of engines with false alerts.
4. **Aggregate delay:** 25 cycles is the median of the three proxy-specific median delays (12, 25, 42.5), not a pooled median across engines/proxies.
5. **Endpoint mode:** A window receives the P1/K=6 mode at its endpoint cycle by exact key join; no majority vote or sensor inference is used.
6. **Runtime state order:** Calibrated score is smoothed by EWMA before strict threshold comparison; persistence counts consecutive violations. Thresholds themselves were fitted beforehand from calibrated eligible-training scores.
7. **Primary selection:** LOF led validation ranking PR-AUC, but PCA won the later preregistered operational alert-policy objective and was frozen at Gate 4.
8. **Ensemble/fusion:** The only evaluated ensemble is the arithmetic mean of three aligned, calibrated LSTM seed scores. PCA–LSTM score/decision fusion was not implemented.
9. **Inference/attribution status:** Later registered implementation supersedes guide/audit statements that these were wholly absent, but only for the narrow batch and non-causal PCA-decomposition claims.
10. **Guide history:** Sections that call Phase 5 “future” or list attribution/inference as incomplete are stale; current configs, results, and code show those steps complete. Official-test evaluation, engine-bootstrap uncertainty, failure analysis, fusion, and streaming remain incomplete.

## Optional improvements or future studies

These are not permitted additions to the current result unless separately preregistered and authorized.

- Engine-level bootstrap confidence intervals for a future evaluation.
- Split-sensitivity analysis across multiple engine partitions.
- Failure analysis for missed engines and healthy-region false alerts.
- A separately registered fusion study.
- A separately registered official NASA-test RUL/proxy evaluation with the already frozen detector.
- External datasets, real-engine validation, or observed physical onset data.
- Attribution stability analysis and domain-expert evaluation.
- Streaming inference state serialization, operational monitoring, and deployment validation.
- A reproducible dependency lockfile and packaging plan.

No optional improvement may revise, replace, or selectively reinterpret the first valid frozen confirmatory result.

## Known evidence limitations to carry into the paper

- One simulated FD002 fleet and one fixed split.
- Proxy onsets instead of observed physical fault onset.
- One internal held-out confirmatory partition and no official NASA-test result.
- Pooled-window ranking metrics and no engine-bootstrap uncertainty.
- Delay medians condition on detected engines; missed engines are represented through coverage.
- No Category A literature comparator.
- Local/ignored data and model artifacts; no exact environment lockfile.
- No evaluated fusion, causal explanation, physical localization, streaming operation, or production monitoring.
