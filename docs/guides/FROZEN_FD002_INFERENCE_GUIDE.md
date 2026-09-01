# Frozen FD002 inference interface

The supported interface is batch-only `turbofan-infer`. It loads only the repository-registered inference protocol and its hash-verified P1/K=6 preprocessor and PCA bundle. There is no user-selected model path, fallback detector, online update, calibration update, or streaming approximation.

```powershell
turbofan-infer --input cycles.csv --output timeline.json --csv-output timeline.csv --visualization timeline.svg
```

The input CSV must have exactly `engine`, `cycle`, `op1`, `op2`, `op3`, and `sensor_1` through `sensor_21`, in that order. Rows must already be sorted by engine and cycle; duplicate, gapped, short, non-finite, nonnumeric, alias, and extra-column inputs fail closed. Each engine needs at least 30 consecutive cycles.

The JSON contains `provenance`, `timeline`, and `events`. Timeline rows include engine/window cycles, endpoint mode, raw and calibrated scores, threshold, EWMA score, violation, persistence, alert/event state, top-three contribution records, and complete explanation labels. `--overwrite` is required for an existing destination.

The optional SVG is deterministic and is intended only for synthetic interface demonstrations. It carries the required label `synthetic_interface_demonstration_not_research_evidence`.

## Artifact security

Before any Joblib deserialization, the loader resolves a repository-relative registered path, requires its presence, hashes raw bytes, and rejects a mismatch. After loading it checks the expected P1/K=6 and PCA classes, six-mode mapping, 63-feature PCA dimension, embedded empirical-CDF calibration state, thresholds, sensor order, and window size. The loader records runtime provenance hashes.

See [the attribution method](../research/PCA_SENSOR_ATTRIBUTION_METHOD_V1.md) and [the registered protocol](../../configs/inference/fd002-frozen-inference-protocol-v1.json).
