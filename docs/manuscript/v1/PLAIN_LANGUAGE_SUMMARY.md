# Plain-Language Summary

## What this study asked

Aircraft engines operate under changing conditions, so a sensor pattern can look unusual because the engine is working differently rather than because it is degrading. This study asks whether a model can account for those operating conditions, learn from early-life behavior, and issue useful anomaly alerts while limiting false alerts.

The experiment uses FD002, a simulated NASA C-MAPSS turbofan benchmark with 260 complete engine trajectories, six operating conditions, three operating-setting variables, and 21 sensor variables. Entire engines—not individual rows or windows—were separated into 156 training engines, 52 validation engines, and 52 internal held-out engines. This prevents windows from one engine from appearing in more than one experimental role.

## What the system does

The selected preprocessing groups operating context into six clusters using the three operating settings and normalizes sensors with training-fitted, context-specific statistics. Each example contains 30 consecutive cycles. For the primary model, each sensor is summarized by its mean, variability, and endpoint change, producing 63 features. Principal component analysis (PCA) learns the dominant structure of eligible early-life training windows and assigns a reconstruction-error score when a new window does not fit that structure well.

The score passes through a fixed alert policy: a training-derived calibration, exponentially weighted smoothing, a threshold for the current operating mode, and a requirement for eight consecutive threshold violations. The complete configuration was locked before the internal held-out partition was accessed. The project calls that governance checkpoint Gate 4; in the manuscript it is described as the **pre-held-out policy freeze**. Its purpose was to prevent held-out results from influencing model or policy selection. The recurrent LSTM ensemble remained a comparator, and no PCA–LSTM fusion was implemented.

## What was found

FD002 does not provide an observed physical fault-onset label for each cycle, so the study evaluates three assumptions: degradation begins in the final 10%, 20%, or 30% of each engine's observed life. These are sensitivity proxies, not ground truth.

| Assumed onset | False-alert rate | Engines detected | Median delay among detected engines |
|---|---:|---:|---:|
| Final 10% | 3.2440% | 51.92% | 12 cycles |
| Final 20% | 0.9443% | 78.85% | 25 cycles |
| Final 30% | 0.5153% | 84.62% | 42.5 cycles |

All three false-alert rates were below the registered 6% objective. However, the registered aggregate delay was the median of the three delay values, or 25 cycles, so the 12-cycle aggregate aspiration was not achieved. Reporting false-alert rate, coverage, and delay together matters: a low false-alert rate alone does not show that enough engines were detected or that alerts arrived promptly.

The literature review deeply extracted 20 core papers and verified 43 numerical values. None used a fully protocol-equivalent combination of dataset role, engine split, onset labels, alert semantics, and metric aggregation. One paper was a strong partial comparator, but its within-trajectory split and different labels and metrics prevent a direct numerical ranking. This is a comparability limitation, not a claim that the present method is first or superior.

## What the result does not show

The work uses one simulated subset and one simulated fault mode. The onsets are normalized-life assumptions, not observed fault times. Results come from an internal held-out partition, not the separately supplied official NASA test or an external real-engine dataset. No confidence interval was registered, and the reported false-alert rate is per proxy-healthy endpoint—not per flight hour, per engine, or per event.

PCA sensor contributions faithfully divide one reconstruction score among sensor summaries, but they do not identify a physical root cause. The study therefore does not establish field readiness, physical fault localization, causal diagnosis, or external generalization.

## Practical takeaway

The strongest contribution is the evaluation discipline: keep engines separated, model operating context, freeze the whole alert path before held-out access, preserve the first valid result, and report false alerts together with coverage and delay under more than one onset assumption. Future work should be separately preregistered and may include uncertainty analysis, failure analysis, official-test evaluation, real-engine validation, attribution-stability review, and streaming-state implementation.
