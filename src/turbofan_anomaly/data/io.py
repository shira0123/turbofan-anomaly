"""FD002 schema validation and tabular input loading."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


FD002_COLUMNS = [
    "engine",
    "cycle",
    "op1",
    "op2",
    "op3",
    *[f"sensor_{index}" for index in range(1, 22)],
]


def validate_fd002_frame(frame: pd.DataFrame) -> None:
    """Validate identity and chronological invariants used by active workflows."""
    required = {"engine", "cycle"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required source columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("FD002 input may not be empty")
    if frame[["engine", "cycle"]].isna().any().any():
        raise ValueError("engine and cycle columns may not contain null values")
    if frame.duplicated(["engine", "cycle"]).any():
        raise ValueError("Duplicate (engine, cycle) rows found")
    for engine, engine_frame in frame.groupby("engine", sort=True):
        cycles = np.sort(engine_frame["cycle"].to_numpy(dtype=int))
        if len(cycles) > 1 and not np.all(np.diff(cycles) == 1):
            raise ValueError(f"Engine {engine} has non-consecutive cycles")


def load_fd002(path: Path) -> pd.DataFrame:
    """Load the whitespace-delimited run-to-failure FD002 training file."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"FD002 source file not found: {source}")
    frame = pd.read_csv(source, sep=r"\s+", header=None, names=FD002_COLUMNS)
    validate_fd002_frame(frame)
    return frame

def load_split_csv(path: Path) -> pd.DataFrame:
    """Load a materialized engine split without inferring or changing its role."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"FD002 split CSV not found: {source}")
    frame = pd.read_csv(source)
    validate_fd002_frame(frame)
    return frame
