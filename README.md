# Turbofan Anomaly Detection on FD002

This repository studies whether operating-condition-aware preprocessing improves anomaly ranking and later alert behavior for unseen NASA C-MAPSS FD002 engines. It is a leakage-controlled research comparison, not a production system and not a claim of a new anomaly-detection algorithm.

## Evidence status

The frozen primary split is deterministic and engine-disjoint: 156 training, 52 validation, and 52 held-out internal-test engines (60/20/20, seed 42), with zero engine overlap. P0 is global sensor preprocessing. P1/K=6 is condition-aware preprocessing: scaled operating settings, six K-Means regimes, and per-regime sensor scaling. **P1 is preprocessing, not the LSTM.**

The current numbers are engine-disjoint **validation proxy diagnostics**, not accuracy and not final-test performance:

| P1/K=6 detector | Mean PR-AUC | Mean ROC-AUC |
|---|---:|---:|
| LOF | 0.84969513 | 0.96436313 |
| One-Class SVM | 0.83280767 | 0.96437111 |
| Final LSTM calibrated ensemble | 0.82212053 | 0.95128915 |
| Isolation Forest | 0.78916934 | 0.95592104 |
| PCA | 0.77240729 | 0.92503450 |

Nine registered LSTM screening runs and the governed final refit are complete. The final `balanced_64x16_l1 + P1/K=6` convergence best epochs were 47, 54, and 59, locking all three refits to epoch 54. The predeclared calibrated-score ensemble beat every individual final-refit LSTM seed, but it did **not** beat LOF or One-Class SVM on mean validation-proxy PR-AUC and remained below LOF, One-Class SVM, and Isolation Forest on mean validation-proxy ROC-AUC. These results do not establish LSTM superiority.

The governed Phase 5 validation-only alert-policy study is also complete. After correcting window-context lineage by assigning each window the registered P1/K=6 operating mode at its endpoint cycle, all five frozen score sources reproduced and all 1,280 alert candidates were evaluated across five proxy policies. The validation recommendation is `pca_reconstruction__per_mode__quantile_0.995__ewma_alpha_0.20__persistence_8`. Its worst primary-policy false-positive endpoint rate was `44.711/1,000` healthy endpoints and its minimum engine coverage was `57.69%`; however, its median-of-policy median delay was `23` cycles, missing the `<=12`-cycle aspiration. LOF and Isolation Forest selected conservative feasible policies that emitted no alerts and detected no engines. This is an operational validation recommendation, not a final-test result.

FD002 provides run-to-failure trajectories but no physical per-cycle anomaly-onset labels. The late-life labels used here are declared evaluation proxies. PR-AUC is a ranking metric, not accuracy.

**Frozen boundary:** do not open, inspect, transform, plot, score, or model the held-out internal-test data without separate explicit authorization. The official NASA test set is outside the protocol. Gate 4 approved and froze the PCA per-mode q=0.995 / EWMA 0.20 / persistence-8 policy. The missing P1/K=6 preprocessor has now been deterministically recovered from the owner-authorized local source using only the frozen 156-engine training allowlist and independently verified against the registered train/validation P1, PCA, and Phase 5 evidence. Final-evaluation protocol v2 is ready only for separately authorized held-out provisioning; no held-out availability check or confirmatory evaluation has occurred.

## Repository map

```text
configs/                 registered split, preprocessing, model, and alert-policy protocols/results
docs/research/           Bible v3, literature matrix, claims and provenance records
docs/guides/             learner-oriented project guide
experiments/runs_v2.jsonl schema-versioned current-protocol ledger
notebooks/               training/validation-only descriptive EDA notebook
reports/                 registered preprocessing, classical, and LSTM evidence
scripts/                 thin command-line wrappers
src/turbofan_anomaly/    reusable importable package
tests/                   synthetic/unit and safety tests
```

Raw data and model artifacts remain intentionally outside Git. Registered train/validation sequences, P1/K=6 cycle frames, immutable original window metadata, derived endpoint-context metadata, the recovered P1/K=6 preprocessor, the three final LSTM artifacts, and five reproduced Phase 5 bundles are local and ignored. Tracked evidence contains protocols, compact recovery/readiness reports, completed result configs, reports, and ledger identities; it does not contain data arrays, checkpoints, or joblib bundles.

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
python -m scripts.run_lstm_final_refit --help
python -m scripts.verify_lstm_final_refit --help
python -m scripts.run_alert_policy_study --help
python -m scripts.verify_alert_policy_study --help
python -m scripts.recover_p1_preprocessor --help
python -m scripts.verify_p1_preprocessor --help
python -m scripts.verify_final_evaluation --help
python -m scripts.run_confirmatory_evaluation --help
python -m scripts.verify_confirmatory_evaluation --help
```

The verification commands are read-only with respect to registered evidence. Historical screen reproduction still needs its absent registered checkpoints, while final-refit and Phase 5 verification use governed local ignored artifacts. Commands that create splits, fit models, or rewrite reports are separated and governed; do not run them as a quick start.

## Research and governance

- [Master Execution Bible v3](docs/research/MASTER_EXECUTION_BIBLE_V3_RESEARCH_IMPLEMENTATION_2026-08-23.md)
- [100-source literature evidence matrix](docs/research/Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx)
- [Claims ledger](docs/research/CLAIMS_LEDGER.md)
- [Decision log](DECISION_LOG.md)
- [Progress log](PROGRESS.md)
- [Confirmatory internal held-out result](configs/evaluation/fd002-confirmatory-results-v1.json)
- [Project understanding guide](docs/guides/PROJECT_UNDERSTANDING_GUIDE.md)
