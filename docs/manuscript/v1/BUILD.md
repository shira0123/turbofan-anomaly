# Build manuscript V1 assets

## Scope and safety

The generator reads only the explicit aggregate/config/source allowlist in `scripts/manuscript/generate_manuscript_v1_assets.py`. It refuses dataset, model, per-engine-result, validation-score, and score-trace paths. It does not import the project package or run any scientific workflow.

## Regenerate all assets

From the repository root on Windows with the recorded Python 3.12 environment:

```powershell
python scripts/manuscript/generate_manuscript_v1_assets.py --repo-root .
```

This command generates editable figure specifications/DOT sources, SVG figures, 300-dpi PNG previews, Markdown/CSV/LaTeX tables, captions, build notes, and provenance.

## Verify generated assets

```powershell
python scripts/manuscript/verify_manuscript_v1_assets.py --repo-root .
```

The verifier checks allowlisted source hashes, exact registered values, citation keys, CSV-to-Markdown/LaTeX canonical digests, SVG well-formedness, PNG dimensions and 300-dpi metadata, and all generated-artifact hashes recorded in provenance. It does not access scientific data or models.

## Render PNG previews only

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manuscript/render_manuscript_v1_previews.ps1 -RepoRoot .
```

## Rendering tools and limitations

- SVG: dependency-free Python standard-library renderer from `figure_sources/figure_specs.json`.
- PNG: Windows `System.Drawing`, saved with 300-dpi metadata from the same primitive specifications.
- Editable diagrams: DOT sources plus the shared JSON primitive specification.
- Graphviz `dot` was unavailable, so DOT was not used for rendering. The committed SVGs are produced by the local deterministic renderer and remain editable vector files.
- Matplotlib, an SVG converter, and a LaTeX engine were unavailable. No dependency was installed. LaTeX table fragments were generated but not compiled in this task.
- No PDF duplicate is produced because SVG already supplies the requested vector format.

## Display rounding

- FAR/1,000: 3 decimals.
- FAR percentage: 4 decimals.
- Coverage: 2 decimals.
- Delay: integer unless a half-cycle median is present.
- PR-AUC and ROC-AUC: 5 decimals.
- Machine-readable CSV and figure specifications retain source precision.

These conversions are display-only and do not replace the registered values.
