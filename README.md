# Turbofan Anomaly Detection on FD002

This repository studies whether operating-condition-aware preprocessing improves anomaly ranking and later alert behavior for unseen NASA C-MAPSS FD002 engines. It is a leakage-controlled research comparison, not a production system and not a claim of a new anomaly-detection algorithm.

## Evidence status

The frozen primary split is deterministic and engine-disjoint: 156 training, 52 validation, and 52 held-out internal-test engines (60/20/20, seed 42), with zero engine overlap. P0 is global sensor preprocessing. P1/K=6 is condition-aware preprocessing: scaled operating settings, six K-Means regimes, and per-regime sensor scaling. **P1 is preprocessing, not the LSTM.**

The current numbers are engine-disjoint **validation proxy diagnostics**, not accuracy and not final-test performance:

| P1/K=6 detector | Mean PR-AUC |
|---|---:|
| LOF | 0.84969513 |
| One-Class SVM | 0.83280767 |
| Isolation Forest | 0.78916934 |
| PCA | 0.77240729 |

Nine registered LSTM screening runs are complete. `balanced_64x16_l1 + P1/K=6` is the recommended screen candidate, with matched-seed median validation proxy PR-AUC `0.81088283`. It has **not** beaten LOF or One-Class SVM. Its final full-training refit has not run.

FD002 provides run-to-failure trajectories but no physical per-cycle anomaly-onset labels. The late-life labels used here are declared evaluation proxies. PR-AUC is a ranking metric, not accuracy.

**Frozen boundary:** do not open, inspect, transform, plot, score, or model the held-out internal-test data. The official NASA test set is also outside the current protocol. Phase 5 threshold/event evaluation and the one-time final internal-test evaluation are pending.

## Repository map

```text
configs/                 registered split, preprocessing, baseline, and LSTM protocols
docs/research/           Bible v3, literature matrix, claims and provenance records
docs/guides/             learner-oriented project guide
experiments/runs_v2.jsonl schema-versioned current-protocol ledger
notebooks/               training/validation-only descriptive EDA notebook
reports/                 registered preprocessing, classical, and LSTM evidence
scripts/                 thin command-line wrappers
src/turbofan_anomaly/    reusable importable package
tests/                   synthetic/unit and safety tests
```

Raw data, processed arrays, and model binaries are intentionally not in this checkout. Their absence prevents notebook execution and full artifact reproduction; it does not invalidate structural/unit checks.

## Setup (Python 3.12.8)

The project is declared by `pyproject.toml`. There is currently **no reproducible lockfile**; do not treat an ad-hoc environment as an exact historical reconstruction.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

Do not install or upgrade packages merely to reproduce registered evidence without first recording the environment decision. The historical LSTM screen used Python 3.12.8 and PyTorch 2.5.1+cu121; the full provenance is in its registered config.

## Safe commands

These commands inspect interfaces or run tests; they do not regenerate registered research reports:

```powershell
python -c "import turbofan_anomaly; print(turbofan_anomaly.__version__)"
pytest -q
python -m pytest tests/test_experiment_ledger.py -q
python -m scripts.make_splits --help
python -m scripts.create_window_metadata --help
python -m scripts.run_preprocessing_study --help
python -m scripts.run_classical_baselines --help
python -m scripts.run_lstm_screen --help
python -m scripts.verify_lstm_screen --help
```

`verify_lstm_screen` itself is read-only with respect to registered evidence, but a full run needs the absent training/validation arrays and model checkpoints. Commands that create splits, fit models, or rewrite reports are separated and guarded in the detailed guide; do not run them as a quick start.

## Research and governance

- [Master Execution Bible v3](docs/research/MASTER_EXECUTION_BIBLE_V3_RESEARCH_IMPLEMENTATION_2026-08-23.md)
- [100-source literature evidence matrix](docs/research/Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx)
- [Claims ledger](docs/research/CLAIMS_LEDGER.md)
- [Decision log](DECISION_LOG.md)
- [Progress log](PROGRESS.md)
- [Project understanding guide](docs/guides/PROJECT_UNDERSTANDING_GUIDE.md)
