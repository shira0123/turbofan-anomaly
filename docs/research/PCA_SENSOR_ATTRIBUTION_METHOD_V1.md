# Frozen PCA sensor reconstruction attribution v1

The deployed policy remains `pca_reconstruction__per_mode__quantile_0.995__ewma_alpha_0.20__persistence_8`. This implementation does not fit, tune, select, recalibrate, fuse, or replace any component.

## Method

The frozen PCA consumes 63 normalized summary features, ordered as 21 sensor means, 21 sensor standard deviations, and 21 endpoint-minus-start slopes. It does not consume or reconstruct a flattened `(30, 21)` sensor-time grid.

For standardized feature vector `z`, reconstruction `r`, and sensor `s`, the local contribution is `((z_mean[s]-r_mean[s])^2 + (z_std[s]-r_std[s])^2 + (z_slope[s]-r_slope[s])^2) / 63`.

The sum of the 21 contributions equals the frozen raw PCA mean-squared reconstruction score. A positive score uses contribution/score shares; a zero score returns zero shares and ranks sensors in registered `sensor_1` through `sensor_21` order. Rankings are descending contribution with ascending sensor index ties.

This is a `pca_reconstruction_error_contribution`, a `local_model_fidelity_explanation` in `normalized_feature_space`. It is `non_causal` and `not_shap`. It must not be described as root-cause identification, physical fault localization, causal explanation, or global feature importance.

The registered machine-readable contract is [fd002-frozen-inference-protocol-v1.json](../../configs/inference/fd002-frozen-inference-protocol-v1.json).
