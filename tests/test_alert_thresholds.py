from __future__ import annotations

import numpy as np
import pytest

from turbofan_anomaly.alerting.thresholds import (
    ThresholdRule,
    fit_thresholds,
    generate_alert_candidates,
    registered_threshold_rules,
    validate_calibrated_scores,
)


def test_quantile_threshold_uses_numpy_higher_method() -> None:
    scores = np.array([0.1, 0.2, 0.3, 0.4])
    rule = ThresholdRule("fixture", "quantile", 0.75)
    assert rule.fit(scores) == np.quantile(scores, 0.75, method="higher") == 0.4


def test_mean_plus_standard_deviation_uses_population_ddof_zero() -> None:
    scores = np.array([0.0, 0.0, 1.0, 1.0])
    rule = ThresholdRule("fixture", "mean_plus_std", 1.5)
    assert rule.fit(scores) == np.mean(scores) + 1.5 * np.std(scores, ddof=0)


def test_global_and_per_mode_thresholds_use_only_matching_training_scores() -> None:
    scores = np.array([0.1, 0.2, 0.8, 0.9])
    modes = np.array([0, 0, 1, 1])
    rule = ThresholdRule("q50", "quantile", 0.5)
    global_fit = fit_thresholds(
        scores, modes, context="global", rule=rule, split_name="train"
    )
    per_mode = fit_thresholds(
        scores,
        modes,
        context="per_mode",
        rule=rule,
        split_name="train",
        expected_modes={0, 1},
        minimum_mode_count=2,
    )
    assert global_fit.values == {None: 0.8}
    assert per_mode.values == {0: 0.2, 1: 0.9}
    assert per_mode.reference_counts == {0: 2, 1: 2}
    with pytest.raises(ValueError, match="No frozen threshold"):
        per_mode.threshold_for_mode(2)


def test_threshold_reference_rejects_validation_and_missing_modes() -> None:
    with pytest.raises(ValueError, match="only training"):
        fit_thresholds(
            np.array([0.1, 0.2]),
            np.array([0, 1]),
            context="global",
            rule=ThresholdRule("q", "quantile", 0.9),
            split_name="validation",
        )
    with pytest.raises(ValueError, match="registered set"):
        fit_thresholds(
            np.array([0.1, 0.2]),
            np.array([0, 1]),
            context="per_mode",
            rule=ThresholdRule("q", "quantile", 0.9),
            split_name="train",
            expected_modes={0, 1, 2},
        )


def test_calibrated_score_contract_preserves_larger_direction_and_bounds() -> None:
    scores = validate_calibrated_scores(np.array([0.0, 0.25, 1.0]))
    assert np.all(np.diff(scores) >= 0.0)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        validate_calibrated_scores(np.array([-0.1, 0.5]))
    with pytest.raises(ValueError, match="finite"):
        validate_calibrated_scores(np.array([0.5, np.nan]))


def test_registered_grid_has_exactly_1280_unique_candidates_in_stable_order() -> None:
    candidates = generate_alert_candidates(
        ["lof", "one_class_svm", "isolation_forest", "pca_reconstruction", "lstm_calibrated_ensemble"],
        ["global", "per_mode"],
        registered_threshold_rules(),
        [
            {"ewma_id": "off", "alpha": None},
            {"ewma_id": "alpha_0.20", "alpha": 0.2},
            {"ewma_id": "alpha_0.50", "alpha": 0.5},
            {"ewma_id": "alpha_0.80", "alpha": 0.8},
        ],
        [1, 3, 5, 8],
    )
    assert len(candidates) == 1280
    assert len({row["candidate_id"] for row in candidates}) == 1280
    assert candidates[0]["candidate_id"] == (
        "lof__global__quantile_0.900__ewma_off__persistence_1"
    )
    assert candidates[-1]["candidate_id"] == (
        "lstm_calibrated_ensemble__per_mode__mean_plus_2.0_std__"
        "ewma_alpha_0.80__persistence_8"
    )
