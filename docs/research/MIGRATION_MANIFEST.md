# Clean-v3 Migration Manifest

**Repository:** `C:/Users/shiva_lajayge/turbofan-clean-v3`

**Branch/base:** `refactor/clean-v3` at `3aa9f0fd6b6f8f92395e3f4940b839859a84664d`

**Policy:** active code is migrated into one importable package; obsolete paths are removed only as exact, reviewable worktree changes; no archive directory is created.

For every tracked old path below, the base bytes remain recoverable with:

```powershell
git restore --source=3aa9f0fd6b6f8f92395e3f4940b839859a84664d -- <old-path>
```

That recovery command is documentation only and was not executed during the refactor.

## Research-authority migrations

| Old/source path | Action/new path | Reason | Verification | Recovery/provenance |
|---|---|---|---|---|
| `C:/Users/shiva_lajayge/Downloads/MASTER_EXECUTION_BIBLE_V3_RESEARCH_IMPLEMENTATION_2026-08-23.md` | exact copy → `docs/research/MASTER_EXECUTION_BIBLE_V3_RESEARCH_IMPLEMENTATION_2026-08-23.md` | Place the approved authority in the active repository under its authoritative filename. | Source/destination size 48,764 bytes and SHA-256 `f7bea8ad60cd7ba53dd40ea3a877914bd2b845a4d183080c5f75853828d778af` match. | External source remains unchanged; destination can be removed without affecting it. |
| `C:/Users/shiva_lajayge/Downloads/Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx` | exact copy → `docs/research/Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx` | Place the 100-source register beside the Bible under its authoritative filename. | Source/destination size 42,201 bytes and SHA-256 `ae173e281fbcbccae7da91920980f4d208a908d2f1a6a6dcfb54af5ebdf05ac3` match; all five workbook sheets decoded successfully. | External source remains unchanged; destination can be removed without affecting it. |

## Active implementation migrations

| Old path | New path/replacement | Reason | Verification | Git recovery |
|---|---|---|---|---|
| `src/data/split_manifest.py` | `src/turbofan_anomaly/data/splits.py`; raw loading factored to `data/io.py` | Establish the importable package and separate I/O from split logic. | Engine-split and package-contract tests; stale-import search. | Base path recoverable with the command above. |
| `src/data/preprocessing.py` | `src/turbofan_anomaly/data/preprocessing.py` | Preserve P0/P1 behavior under the package namespace. | Preprocessing numerical/unit tests and import smoke test. | Base path recoverable. |
| `src/data/window_metadata.py` | `src/turbofan_anomaly/data/metadata.py` | Make window identity and safety metadata reusable. | Metadata count/boundary and safe-default tests. | Base path recoverable. |
| `src/data/window_arrays.py` | `src/turbofan_anomaly/data/windows.py` | Preserve engine-local sequence construction in reusable code. | Window-array shape/alignment tests. | Base path recoverable. |
| `src/evaluation/proxy_policies.py` | `src/turbofan_anomaly/evaluation/proxies.py` | Keep evaluation proxies separate from physical labels. | Proxy-policy tests. | Base path recoverable. |
| `src/models/classical_baselines.py` | `src/turbofan_anomaly/models/classical.py`; calibrator factored to `alerting/calibration.py` | Preserve classical selection/scoring behavior and isolate calibration. | Classical-baseline numerical tests. | Base path recoverable. |
| `src/models/lstm_ae.py` | `src/turbofan_anomaly/models/lstm_autoencoder.py` | Preserve the registered LSTM architecture under the package namespace. | LSTM validation/unit tests. | Base path recoverable. |
| `src/models/lstm_validation.py` | `src/turbofan_anomaly/models/lstm_training.py` | Preserve registered training/validation behavior in reusable code. | LSTM validation/unit tests. | Base path recoverable. |

## Thin-wrapper migrations

Each retained script keeps its path but now delegates implementation to the same-name module under `turbofan_anomaly.workflows`.

| Rewritten path | Replacement implementation | Verification | Git recovery |
|---|---|---|---|
| `scripts/make_splits.py` | `src/turbofan_anomaly/workflows/make_splits.py` | CLI `--help`, package import, engine-split tests | Base script recoverable. |
| `scripts/create_window_metadata.py` | `src/turbofan_anomaly/workflows/create_window_metadata.py` | CLI `--help`, safe training/validation default tests | Base script recoverable. |
| `scripts/run_preprocessing_study.py` | `src/turbofan_anomaly/workflows/run_preprocessing_study.py` | CLI `--help`, preprocessing tests | Base script recoverable. |
| `scripts/run_classical_baselines.py` | `src/turbofan_anomaly/workflows/run_classical_baselines.py` | CLI `--help`, classical tests | Base script recoverable. |
| `scripts/run_lstm_screen.py` | `src/turbofan_anomaly/workflows/run_lstm_screen.py` | CLI `--help`, LSTM tests | Base script recoverable. |
| `scripts/verify_lstm_screen.py` | `src/turbofan_anomaly/workflows/verify_lstm_screen.py` | CLI `--help`, LSTM verification tests | Base script recoverable. |

## Experiment-ledger migration

| Source | Replacement | Reason | Verification | Git recovery |
|---|---|---|---|---|
| `experiments/experiments.csv` | `experiments/runs_v2.jsonl` | The legacy CSV is malformed and mixes current protocol with ten historical/smoke rows. | 22 JSON objects: 13 `run_20260822_*` and 9 `fd002_lstm_v1_*`; schema `2.0.0`; unique run IDs; exact legacy value strings; source-row SHA-256; JSON round-trip test. | Source checkout SHA-256 `021133b38a07268b2eb2a76c07ab7346749161965922b28eee4d380f789e240f`; Git/LF SHA-256 `f1b65636d738d4c15949663c1d43a9170cd94f40ad083b77a27cd311445a3e37`; base path recoverable. |

Migrated physical source lines are 12–33. The ten excluded rows are `run_000`, `run_20260627_184001_isolation_forest`, `run_20260627_184001_lof`, `run_20260629_205101_isolation_forest`, `run_20260629_205101_lof`, `run_20260629_222541_lstm_ae_smoke`, `run_20260629_222613_lstm_ae_smoke`, `run_20260629_222756_lstm_ae_scores`, `run_20260629_222821_lstm_ae_scores`, and `run_20260629_222919_adaptive_threshold`. They were not silently repaired or promoted.

**Deletion status:** removed from the active branch after validating all 22 migrated records. Before removal, the exact tracked path and SHA-256 were verified and a byte-identical temporary safety copy was made; the authoritative recovery path remains Git at base `3aa9f0f`.

## Completed obsolete-code removals

| Removed path | Reason | Replacement | Verification | Git recovery |
|---|---|---|---|---|
| `requirements.txt` | Superseded dependency declaration. | `pyproject.toml` | Packaging/import/test checks. | Base file recoverable. |
| `scripts/fit_domain_adapter_and_save.py` | Obsolete alternate 70/30/domain-adapter path. | Registered P0/P1 preprocessing workflow. | Stale-reference search and active CLI tests. | Base file recoverable. |
| `scripts/transform_and_save_processed.py` | Obsolete alternate preprocessing path. | `run_preprocessing_study.py` thin workflow. | Stale-reference search. | Base file recoverable. |
| `scripts/create_sequences_save.py` | Obsolete sequence path. | `create_window_metadata.py` plus package windows API. | Metadata/window tests. | Base file recoverable. |
| `scripts/run_eda.py` | Obsolete implementation duplicated preprocessing and old split assumptions. | `notebooks/01_fd002_eda.ipynb` with config `fd002-eda-v1.json`. | Notebook JSON/source safety checks. | Base file recoverable. |
| `scripts/run_baselines.py` | Historical 70/30 baseline workflow. | `run_classical_baselines.py`. | Classical tests and stale-reference search. | Base file recoverable. |
| `scripts/train_lstm_smoke.py` | Smoke-only LSTM path, not current evidence. | Registered LSTM screen workflow; final refit remains future work. | LSTM tests. | Base file recoverable. |
| `scripts/export_lstm_scores.py` | Legacy smoke checkpoint exporter. | Registered LSTM workflow/verification reports. | LSTM verification tests. | Base file recoverable. |
| `scripts/fit_adaptive_threshold.py` | Old online/adaptive-threshold prototype is outside current protocol. | None; Phase 5 alerting is future registered work. | Stale-reference search. | Base file recoverable. |
| `scripts/log_experiment.py` | Free-form CSV writer cannot enforce schema 2.0.0. | `experiments/runs_v2.jsonl` and its validation test. | JSONL round-trip test. | Base file recoverable. |
| `tests/test_api_inference.py` | Covered a removed prototype API, not the validated research path. | Package/workflow contract tests. | Full safe suite. | Base file recoverable. |
| `src/__init__.py` | Old namespace initializer. | `src/turbofan_anomaly/__init__.py`. | Import smoke test. | Base file recoverable. |
| `src/data/__init__.py` | Old namespace initializer. | `src/turbofan_anomaly/data/__init__.py`. | Import smoke test. | Base file recoverable. |
| `src/data/domain_adapter.py` | Obsolete domain-adapter implementation. | P0/P1 registered preprocessing. | Preprocessing tests and stale-import search. | Base file recoverable. |
| `src/evaluation/__init__.py` | Old namespace initializer. | `src/turbofan_anomaly/evaluation/__init__.py`. | Import smoke test. | Base file recoverable. |
| `src/models/__init__.py` | Old namespace initializer. | `src/turbofan_anomaly/models/__init__.py`. | Import smoke test. | Base file recoverable. |
| `src/models/baselines.py` | Historical baseline implementation. | `src/turbofan_anomaly/models/classical.py`. | Classical tests and stale-import search. | Base file recoverable. |
| `src/api/__init__.py` | Prototype API namespace outside validated pipeline. | None; future API requires a frozen bundle. | Stale-import/path search. | Base file recoverable. |
| `src/api/main.py` | Prototype API and placeholder explanation behavior. | None; future gated API/explanation contract. | Stale API/fake-SHAP search. | Base file recoverable. |
| `src/thresholding/__init__.py` | Prototype adaptive-threshold namespace. | None; Phase 5 remains pending. | Stale-import/path search. | Base file recoverable. |
| `src/thresholding/adaptive_threshold.py` | Online recalibration can absorb degradation and is not current evidence. | None; future frozen validation-selected alert policy. | Stale-import/path search. | Base file recoverable. |
| `src/explainability/__init__.py` | Empty/placeholder legacy namespace. | No active replacement until a tested reconstruction-contribution contract exists. | Stale-import/path search. | Base file recoverable. |
| `CODEBASE_EXECUTION_GUIDE.md` | Redundant and described obsolete paths. | `docs/guides/PROJECT_UNDERSTANDING_GUIDE.md`. | Unique shapes, flow, commands, and troubleshooting migrated; local-link review. | Base file recoverable. |
| `QUICK_REFERENCE.md` | Redundant quick guide described obsolete paths. | `docs/guides/PROJECT_UNDERSTANDING_GUIDE.md` and concise `README.md`. | Unique useful content migrated; local-link review. | Base file recoverable. |

## Completed obsolete-report removals

Every file below was verified as tracked at `3aa9f0f`, hashed before removal, and has a current replacement or an explicit “no current evidence” boundary. The exact named files were removed only after byte-identical temporary safety copies were confirmed. Their authoritative recovery path is Git history at the base commit.

| Removed path | Base raw SHA-256 | Reason | Replacement / verification | Git recovery |
|---|---|---|---|---|
| `reports/baselines/baseline_metrics.csv` | `8916f4908b416941288b5e371fd265999adaf3265d924de2e2e11b90274ed7de` | Historical 70/30 baseline output. | Current `reports/baselines_v2/`; registered hashes unchanged. | Base path recoverable. |
| `reports/eda/cluster_validation.csv` | `40daeb8a85e61a2011fba1ed593d378f91a8cc133891df3b86bd9c8d48701919` | Old K=4-only EDA. | Config-driven notebook plus current preprocessing reports. | Base path recoverable. |
| `reports/eda/degradation_trends.csv` | `18ed50f4b108bb7ac442cb1b85745ed52e42fb70cdcacb8a44a4a3e398ae13fa` | Old descriptive output with obsolete split assumptions. | Output-cleared notebook; regeneration pending allowed inputs. | Base path recoverable. |
| `reports/eda/degradation_trends.png` | `e78fd31538f8d29f0fd43d2d85f6ad6b5343e2fb4dda62f6bfe7fb796e1c972f` | Same. | Same. | Base path recoverable. |
| `reports/eda/op_mode_counts.csv` | `0fb6fdd4197804f3c16160cb0f8a2f99c6cc7c6aff8f7758ad228236c1996011` | Old K=4 condition counts. | `reports/preprocessing/occupancy.csv` and notebook K=4/6/8 section. | Base path recoverable. |
| `reports/eda/op_mode_counts.png` | `6aebf278a5199ebac7e21d01900097e5c01d9a22e954d92bed3781a7786e6c62` | Same. | Same. | Base path recoverable. |
| `reports/eda/sensor_correlation_heatmap.png` | `87e7c30a27dd2ccba7be84a72da1f805a37dde5e32973936e16875564d9091ba` | Old unregistered EDA output. | Notebook non-causal correlation section; execution pending. | Base path recoverable. |
| `reports/eda/sensor_correlation_matrix.csv` | `f4d6ae65e3f999b60f608c303b5faacba888888e8bc1b8cbe1010940a2a7cd5f` | Same. | Same. | Base path recoverable. |
| `reports/eda/sensor_distribution_stats.csv` | `a94acce8d5efebfa61d1ba7c847d7dcd4292d707a744c5328f781a3b6a7b2bc5` | Old unregistered EDA output. | Notebook split-specific quality/distribution sections. | Base path recoverable. |
| `reports/lstm_ae/reconstruction_scores.csv` | `2f33ca3ede43e7ce178113d94121abec532dfad29f86c5785bc380c7098a1a5b` | Smoke-LSTM scores, protocol-incompatible. | Current registered `reports/lstm_v2/`; no final refit result exists. | Base path recoverable. |
| `reports/lstm_ae/reconstruction_summary.csv` | `21725657f1821c79daccf9ebef1885460b12abac568b995c4130a890e92c4ae9` | Same. | Same. | Base path recoverable. |
| `reports/lstm_ae/threshold_summary.csv` | `0a25e9753fa1d0ff886a44bade8a97370d85246d7de51bd8cebbefc24ce893e9` | Obsolete adaptive threshold, not Phase 5 evidence. | None; threshold/event evaluation remains pending. | Base path recoverable. |
| `reports/lstm_ae/training_curve_20260629_222541.csv` | `90862de4d3dcddaabf73c69505480c47f845d7d70aff009d9d43ca81c27fd322` | Smoke training trace. | Current registered `reports/lstm_v2/training_history.csv`. | Base path recoverable. |
| `reports/lstm_ae/training_curve_20260629_222613.csv` | `90862de4d3dcddaabf73c69505480c47f845d7d70aff009d9d43ca81c27fd322` | Duplicate smoke training trace. | Current registered `reports/lstm_v2/training_history.csv`. | Base path recoverable. |

## New governed artifacts

The following are new rather than migrated executable evidence: `CLAIMS_LEDGER.md`, `ARTIFACT_MANIFEST.md`, `PATH_AND_HASH_POLICY.md`, `configs/evaluation/fd002-eda-v1.json`, and `notebooks/01_fd002_eda.ipynb`. They do not alter any registered metric, config, or report bytes.

No held-out internal-test contents and no official NASA test data were accessed during this migration.
