"""Adaptive thresholding for reconstruction-error streams."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple

import numpy as np


@dataclass
class AdaptiveThresholdEngine:
    """Context-aware threshold engine using EWMA smoothing and per-mode bounds."""

    alpha: float = 0.15
    k: float = 2.5
    m: int = 3
    decay: float = 0.98
    update_interval: int = 50
    mu_per_mode: Dict[int, float] = field(default_factory=dict)
    sigma_per_mode: Dict[int, float] = field(default_factory=dict)
    smoothed_score: float = 0.0
    consecutive_violations: int = 0
    iteration_count: int = 0
    history_buffer: deque = field(default_factory=lambda: deque(maxlen=50))

    def fit_baseline_parameters(self, healthy_errors: Iterable[float], operational_modes: Iterable[int]) -> "AdaptiveThresholdEngine":
        healthy_errors = np.asarray(list(healthy_errors), dtype=float)
        operational_modes = np.asarray(list(operational_modes), dtype=int)

        if len(healthy_errors) != len(operational_modes):
            raise ValueError("healthy_errors and operational_modes must have the same length")

        unique_modes = np.unique(operational_modes)
        for mode in unique_modes:
            mode_errors = healthy_errors[operational_modes == mode]
            if len(mode_errors) == 0:
                continue
            self.mu_per_mode[int(mode)] = float(np.mean(mode_errors))
            self.sigma_per_mode[int(mode)] = float(np.std(mode_errors))
        return self

    def dynamic_threshold(self, current_mode: int) -> float:
        if not self.mu_per_mode:
            raise RuntimeError("Call fit_baseline_parameters before thresholding")

        mu = self.mu_per_mode.get(current_mode, float(np.mean(list(self.mu_per_mode.values()))))
        sigma = self.sigma_per_mode.get(current_mode, float(np.mean(list(self.sigma_per_mode.values()))))
        return mu + self.k * sigma

    def process_inference_cycle(self, raw_score: float, current_mode: int) -> Tuple[bool, float, float]:
        self.smoothed_score = self.alpha * raw_score + (1 - self.alpha) * self.smoothed_score
        threshold = self.dynamic_threshold(current_mode)

        if self.smoothed_score > threshold:
            self.consecutive_violations += 1
        else:
            self.consecutive_violations = 0

        is_anomalous_alert = self.consecutive_violations >= self.m

        self.history_buffer.append(raw_score)
        self.iteration_count += 1
        if self.iteration_count % self.update_interval == 0 and len(self.history_buffer) == self.update_interval:
            recent_mean = float(np.mean(self.history_buffer))
            recent_std = float(np.std(self.history_buffer))
            prev_mu = self.mu_per_mode.get(current_mode, recent_mean)
            prev_sigma = self.sigma_per_mode.get(current_mode, recent_std)
            self.mu_per_mode[current_mode] = self.decay * prev_mu + (1 - self.decay) * recent_mean
            self.sigma_per_mode[current_mode] = self.decay * prev_sigma + (1 - self.decay) * recent_std

        return is_anomalous_alert, threshold, self.smoothed_score
