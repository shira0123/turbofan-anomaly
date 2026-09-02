# FD002 Official-Test Literature Assessment V1

This assessment uses only the inspected manuscripts. It does not open, hash, inspect, preprocess, score, or summarize the repository's local `test_FD002.txt` or `RUL_FD002.txt`.

## Core-paper use of official FD002 files

| Paper | `test_FD002.txt` | `RUL_FD002.txt` | Task | Evaluation unit | Per-cycle RUL | Anomaly onset | Truncation | Alert delay / coverage / FAR |
|---|:---:|:---:|---|---|---|---|---|---|
| LIT-009 | yes | yes | Change-point-informed supervised RUL | Official-test terminal cycle for RUL; change points are learned on complete training trajectories | Terminal RUL is extended backward by remaining observed cycles, subject to the paper's 130-cycle cap | No observed official-test anomaly onset; training change point is model-derived from persistent T2/Q breaches | Official trajectories end before failure and the terminal offset supplies remaining life | no / no / no |
| LIT-018 | yes | yes | Supervised informed RUL regression | Last observed official-test window per engine | Standard C-MAPSS terminal RUL offset supports a piecewise/capped training target | No anomaly-onset label | Truncated official trajectories are paired with terminal RUL truth | no / no / no |

`LIT-010` studies FD002 key points but does not identify its reported “test set” clearly enough to assert raw `test_FD002.txt`/`RUL_FD002.txt` use. It is recorded as `NR`, not silently counted. `LIT-006` uses an official C-MAPSS test/RUL pair for the single-condition 100-engine subset, not FD002. The C-MAPSS benchmark/review papers (`LIT-003`, `LIT-004`) discuss official files but are not counted as new experimental use. The inaccessible selected paper `LIT-019` was replaced before extraction and is not counted.

## What the official files support

The inspected literature predominantly uses the official test files for terminal RUL regression. Each official trajectory is right-truncated before failure. `RUL_FD002` gives remaining life at the final observed cycle; a deterministic per-cycle RUL can be reconstructed by adding the number of remaining observed cycles when moving backward. That creates a time-to-failure coordinate, not an observed physical fault-onset label.

None of the two core FD002 official-test studies reports the frozen project's endpoint false-alert rate, engine detection coverage, persistent alert delay, or all-cycle anomaly-event metrics. Neither establishes a physical onset for the truncated trajectory. Their RMSE/NASA-score results cannot be compared directly with the project's PR-AUC, ROC-AUC, FAR, coverage, or delay.

## Reproducibility with the frozen system

The frozen P1/K=6 preprocessing, PCA reconstruction score, training-only calibration, per-mode quantile thresholds, EWMA reset/initialization, and persistence-8 rule could in principle score every eligible observed official-test window without refitting. The current system is not an RUL regressor and cannot reproduce the papers' RUL predictions. Any labels based on reconstructed per-cycle RUL would be newly preregistered secondary proxies; they would not be physical onset.

## Recommendation

**Perform a preregistered secondary RUL-proxy evaluation.**

This would materially strengthen the paper only as an external, frozen-policy robustness check across the 259 truncated FD002 test engines. A future protocol should freeze the terminal-RUL back-projection, one or more clinically interpretable RUL-proximity cutoffs, eligible-window rules, all-cycle and terminal summaries, and a no-retuning rule before any local official-test file is opened. Results must be labeled secondary official-test RUL-proxy evidence, not anomaly-onset validation. A separate RUL benchmark is unnecessary because the frozen system does not predict RUL; omitting all official-test analysis would forgo a useful external generalization check.

No such evaluation is authorized or implemented by this document.
