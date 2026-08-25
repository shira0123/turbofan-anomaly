"""Training-only threshold fitting and frozen Phase 5 candidate generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class ThresholdRule:
    """One deterministic threshold statistic fitted to training scores."""

    rule_id: str
    kind: str
    value: float

    def __post_init__(self) -> None:
        if self.kind not in {"quantile", "mean_plus_std"}:
            raise ValueError("Threshold kind must be quantile or mean_plus_std")
        if self.kind == "quantile" and not 0.0 < self.value < 1.0:
            raise ValueError("Quantile value must be in (0, 1)")
        if self.kind == "mean_plus_std" and self.value < 0.0:
            raise ValueError("Mean-plus-standard-deviation multiplier must be nonnegative")

    def fit(self, scores: np.ndarray) -> float:
        values = validate_calibrated_scores(scores)
        if self.kind == "quantile":
            return float(np.quantile(values, self.value, method="higher"))
        return float(np.mean(values) + self.value * np.std(values, ddof=0))


@dataclass(frozen=True)
class FittedThresholds:
    """Frozen global or per-mode thresholds and their training counts."""

    context: str
    rule_id: str
    values: Mapping[int | None, float]
    reference_counts: Mapping[int | None, int]

    def threshold_for_mode(self, mode: Any) -> float:
        key: int | None = None if self.context == "global" else _mode_value(mode)
        if key not in self.values:
            raise ValueError(f"No frozen threshold exists for operating mode {mode!r}")
        return float(self.values[key])


def validate_calibrated_scores(scores: np.ndarray) -> np.ndarray:
    """Return a one-dimensional finite score view bounded by ``[0, 1]``."""
    values = np.asarray(scores, dtype=float).reshape(-1)
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("Calibrated alert scores must be finite and non-empty")
    if np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("Calibrated alert scores must lie in [0, 1]")
    return values


def _mode_value(value: Any) -> int:
    if value is None or bool(np.asarray([value], dtype=object)[0] is None):
        raise ValueError("Operating modes must be non-null")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid operating mode: {value!r}") from error
    if not np.isfinite(numeric) or not numeric.is_integer():
        raise ValueError(f"Operating modes must be finite integers: {value!r}")
    return int(numeric)


def registered_threshold_rules() -> tuple[ThresholdRule, ...]:
    """Return the eight frozen Phase 5 threshold rules in registered order."""
    return (
        ThresholdRule("quantile_0.900", "quantile", 0.900),
        ThresholdRule("quantile_0.950", "quantile", 0.950),
        ThresholdRule("quantile_0.975", "quantile", 0.975),
        ThresholdRule("quantile_0.990", "quantile", 0.990),
        ThresholdRule("quantile_0.995", "quantile", 0.995),
        ThresholdRule("mean_plus_1.0_std", "mean_plus_std", 1.0),
        ThresholdRule("mean_plus_1.5_std", "mean_plus_std", 1.5),
        ThresholdRule("mean_plus_2.0_std", "mean_plus_std", 2.0),
    )


def fit_thresholds(
    scores: np.ndarray,
    modes: np.ndarray,
    *,
    context: str,
    rule: ThresholdRule,
    split_name: str,
    expected_modes: Iterable[int] | None = None,
    minimum_mode_count: int = 1,
) -> FittedThresholds:
    """Fit a threshold once from the declared training reference population."""
    if split_name != "train":
        raise ValueError("Threshold reference statistics may use only training scores")
    if context not in {"global", "per_mode"}:
        raise ValueError("Threshold context must be global or per_mode")
    if minimum_mode_count < 1:
        raise ValueError("minimum_mode_count must be positive")
    values = validate_calibrated_scores(scores)
    mode_array = np.asarray(modes, dtype=object).reshape(-1)
    if len(mode_array) != len(values):
        raise ValueError("Operating-mode and score lengths differ")
    normalized_modes = np.asarray([_mode_value(item) for item in mode_array], dtype=int)
    observed = set(map(int, np.unique(normalized_modes)))
    if expected_modes is not None and observed != set(map(int, expected_modes)):
        raise ValueError("Training operating modes differ from the registered set")
    if context == "global":
        return FittedThresholds(
            context=context,
            rule_id=rule.rule_id,
            values={None: rule.fit(values)},
            reference_counts={None: int(len(values))},
        )
    thresholds: dict[int | None, float] = {}
    counts: dict[int | None, int] = {}
    for mode in sorted(observed):
        selected = values[normalized_modes == mode]
        if len(selected) < minimum_mode_count:
            raise ValueError(
                f"Operating mode {mode} has fewer than {minimum_mode_count} training scores"
            )
        thresholds[mode] = rule.fit(selected)
        counts[mode] = int(len(selected))
    return FittedThresholds(context, rule.rule_id, thresholds, counts)


def generate_alert_candidates(
    score_sources: Sequence[str],
    threshold_contexts: Sequence[str],
    threshold_rules: Sequence[ThresholdRule],
    ewma_states: Sequence[Mapping[str, Any]],
    persistence_values: Sequence[int],
) -> list[dict[str, Any]]:
    """Generate deterministic registered-order candidates with unique IDs."""
    candidates: list[dict[str, Any]] = []
    for detector_id in score_sources:
        for context in threshold_contexts:
            if context not in {"global", "per_mode"}:
                raise ValueError(f"Unsupported threshold context: {context}")
            for rule in threshold_rules:
                for ewma in ewma_states:
                    ewma_id = str(ewma["ewma_id"])
                    alpha = ewma.get("alpha")
                    if alpha is not None and not 0.0 < float(alpha) <= 1.0:
                        raise ValueError("EWMA alpha must be in (0, 1]")
                    for persistence in persistence_values:
                        if int(persistence) not in {1, 3, 5, 8}:
                            raise ValueError("Persistence must be one of 1, 3, 5, or 8")
                        candidate_id = (
                            f"{detector_id}__{context}__{rule.rule_id}__"
                            f"ewma_{ewma_id}__persistence_{int(persistence)}"
                        )
                        candidates.append(
                            {
                                "candidate_id": candidate_id,
                                "detector_id": str(detector_id),
                                "threshold_context": context,
                                "threshold_rule_id": rule.rule_id,
                                "threshold_kind": rule.kind,
                                "threshold_value": rule.value,
                                "ewma_id": ewma_id,
                                "ewma_alpha": None if alpha is None else float(alpha),
                                "persistence": int(persistence),
                            }
                        )
    identifiers = [row["candidate_id"] for row in candidates]
    if len(set(identifiers)) != len(identifiers):
        raise RuntimeError("Alert candidate IDs are not unique")
    return candidates
