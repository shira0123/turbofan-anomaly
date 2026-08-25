"""Explicit degradation-onset proxy policies for run-to-failure windows."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class NormalizedLifeOnsetPolicy:
    """Classify windows relative to an onset at the final life fraction."""

    onset_fraction: float
    semantics: str = "endpoint"
    selection_policy: bool = True

    def __post_init__(self) -> None:
        if not 0.0 < self.onset_fraction < 1.0:
            raise ValueError("onset_fraction must be in (0, 1)")
        if self.semantics not in {"endpoint", "full_window"}:
            raise ValueError("semantics must be endpoint or full_window")

    @property
    def policy_id(self) -> str:
        percent = int(round(self.onset_fraction * 100))
        return f"normalized_life_last_{percent}pct_{self.semantics}"

    def apply(self, metadata: pd.DataFrame) -> pd.DataFrame:
        required = {"window_id", "engine", "start_cycle", "end_cycle", "max_cycle"}
        missing = required - set(metadata.columns)
        if missing:
            raise ValueError(f"Missing policy metadata columns: {sorted(missing)}")

        onset_cycle = (
            np.floor(metadata["max_cycle"] * (1.0 - self.onset_fraction)).astype(int)
            + 1
        )
        healthy = metadata["end_cycle"].astype(int) < onset_cycle
        if self.semantics == "endpoint":
            anomalous = ~healthy
            ambiguous = pd.Series(False, index=metadata.index)
        else:
            anomalous = metadata["start_cycle"].astype(int) >= onset_cycle
            ambiguous = ~(healthy | anomalous)

        states = np.full(len(metadata), "ambiguous", dtype=object)
        states[healthy.to_numpy()] = "healthy"
        states[anomalous.to_numpy()] = "anomalous"
        labels = pd.array([pd.NA] * len(metadata), dtype="Int64")
        labels[healthy.to_numpy()] = 0
        labels[anomalous.to_numpy()] = 1

        return pd.DataFrame(
            {
                "window_id": metadata["window_id"].to_numpy(),
                "engine": metadata["engine"].astype(int).to_numpy(),
                "policy_id": self.policy_id,
                "policy_semantics": self.semantics,
                "selection_policy": self.selection_policy,
                "onset_fraction": self.onset_fraction,
                "onset_cycle": onset_cycle.to_numpy(dtype=int),
                "label_state": states,
                "proxy_label": labels,
            },
            index=metadata.index,
        )


def registered_validation_policies() -> list[NormalizedLifeOnsetPolicy]:
    """Return primary endpoint policies plus secondary overlap-excluded checks."""
    return [
        NormalizedLifeOnsetPolicy(0.10, "endpoint", True),
        NormalizedLifeOnsetPolicy(0.20, "endpoint", True),
        NormalizedLifeOnsetPolicy(0.30, "endpoint", True),
        NormalizedLifeOnsetPolicy(0.20, "full_window", False),
        NormalizedLifeOnsetPolicy(0.30, "full_window", False),
    ]


def training_eligible_windows(
    metadata: pd.DataFrame, healthy_fraction: float
) -> pd.Series:
    """Return the healthy-training assumption without labeling other windows."""
    if not 0.0 < healthy_fraction <= 1.0:
        raise ValueError("healthy_fraction must be in (0, 1]")
    required = {"end_cycle", "max_cycle"}
    missing = required - set(metadata.columns)
    if missing:
        raise ValueError(f"Missing training policy columns: {sorted(missing)}")
    cutoff = np.floor(metadata["max_cycle"] * healthy_fraction).astype(int)
    return metadata["end_cycle"].astype(int) <= cutoff
