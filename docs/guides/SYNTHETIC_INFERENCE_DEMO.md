# Synthetic inference demonstration

Use synthetic FD002-like cycle records only. Do not use held-out internal or official NASA-test records for screenshots, demos, or interface development.

Create a CSV with the exact inference schema, 30 or more consecutive rows per engine, then run `turbofan-infer` with `--visualization`. The SVG displays calibrated score, endpoint-mode threshold, EWMA score, alert locations, and event locations. Label every such output `synthetic_interface_demonstration_not_research_evidence`.

The visualization is an interface aid, not a research result. It does not infer physical faults, causes, or general sensor importance.
