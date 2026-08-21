"""Leakage-controlled preprocessing candidates for the FD002 ablation study."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


OP_COLUMNS = ("op1", "op2", "op3")
SENSOR_COLUMNS = tuple(f"sensor_{index}" for index in range(1, 22))


def _validate_frame(frame: pd.DataFrame) -> None:
    required = {"engine", "cycle", *OP_COLUMNS, *SENSOR_COLUMNS}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing preprocessing columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Cannot fit or transform an empty dataframe")
    if frame[list(required)].isna().any().any():
        raise ValueError("Preprocessing inputs may not contain null values")
    if frame.duplicated(["engine", "cycle"]).any():
        raise ValueError("Duplicate (engine, cycle) rows found")


def healthy_training_mask(frame: pd.DataFrame, fraction: float) -> pd.Series:
    """Mark rows eligible for fitting normal sensor scalers.

    This is a training assumption only. False rows are not assigned an anomaly
    label and must not be interpreted as known degradation.
    """
    if not 0.0 < fraction <= 1.0:
        raise ValueError("healthy training fraction must be in (0, 1]")
    _validate_frame(frame)
    max_cycle = frame.groupby("engine")["cycle"].transform("max")
    cutoff = np.floor(max_cycle * fraction).astype(int)
    return frame["cycle"].astype(int) <= cutoff


def _engine_id_digest(engine_ids: tuple[int, ...]) -> str:
    payload = ",".join(map(str, engine_ids)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class GlobalSensorPreprocessor:
    """P0: one sensor scaler fitted on healthy-assumption training rows."""

    method = "p0_global"

    def __init__(self, *, split_manifest_id: str, healthy_fraction: float = 0.30) -> None:
        self.split_manifest_id = split_manifest_id
        self.healthy_fraction = float(healthy_fraction)
        self.sensor_scaler_: StandardScaler | None = None
        self.fit_engine_ids_: tuple[int, ...] = ()
        self.fit_row_count_: int = 0
        self.healthy_fit_row_count_: int = 0

    def fit(self, train_frame: pd.DataFrame) -> "GlobalSensorPreprocessor":
        _validate_frame(train_frame)
        healthy_mask = healthy_training_mask(train_frame, self.healthy_fraction)
        if not healthy_mask.any():
            raise ValueError("No rows satisfy the healthy training assumption")

        self.sensor_scaler_ = StandardScaler().fit(
            train_frame.loc[healthy_mask, list(SENSOR_COLUMNS)].to_numpy(dtype=float)
        )
        self.fit_engine_ids_ = tuple(
            sorted(train_frame["engine"].astype(int).unique().tolist())
        )
        self.fit_row_count_ = int(len(train_frame))
        self.healthy_fit_row_count_ = int(healthy_mask.sum())
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        _validate_frame(frame)
        if self.sensor_scaler_ is None:
            raise RuntimeError("Call fit() before transform()")

        transformed = frame.astype(
            {sensor: "float64" for sensor in SENSOR_COLUMNS}
        ).copy()
        transformed.loc[:, list(SENSOR_COLUMNS)] = self.sensor_scaler_.transform(
            frame.loc[:, list(SENSOR_COLUMNS)].to_numpy(dtype=float)
        )
        transformed["op_mode"] = -1
        return transformed

    def fit_metadata(self) -> dict[str, Any]:
        if self.sensor_scaler_ is None:
            raise RuntimeError("Call fit() before requesting metadata")
        return {
            "method": self.method,
            "split_manifest_id": self.split_manifest_id,
            "healthy_fraction": self.healthy_fraction,
            "fit_rows_all_cycles": self.fit_row_count_,
            "sensor_scaler_fit_rows": self.healthy_fit_row_count_,
            "fit_engine_count": len(self.fit_engine_ids_),
            "fit_engine_ids_sha256": _engine_id_digest(self.fit_engine_ids_),
            "op_mode_value": -1,
        }


class RegimeSensorPreprocessor:
    """P1: scaled operating settings, K-Means, and per-regime sensor scaling."""

    method = "p1_regime"

    def __init__(
        self,
        *,
        split_manifest_id: str,
        n_clusters: int,
        healthy_fraction: float = 0.30,
        random_state: int = 42,
        n_init: int = 20,
        min_mode_fit_rows: int = 30,
    ) -> None:
        if n_clusters < 2:
            raise ValueError("n_clusters must be at least 2")
        if n_init < 1:
            raise ValueError("n_init must be positive")
        if min_mode_fit_rows < 1:
            raise ValueError("min_mode_fit_rows must be positive")

        self.split_manifest_id = split_manifest_id
        self.n_clusters = int(n_clusters)
        self.healthy_fraction = float(healthy_fraction)
        self.random_state = int(random_state)
        self.n_init = int(n_init)
        self.min_mode_fit_rows = int(min_mode_fit_rows)

        self.op_scaler_: StandardScaler | None = None
        self.kmeans_: KMeans | None = None
        self.global_sensor_scaler_: StandardScaler | None = None
        self.sensor_scalers_per_mode_: dict[int, StandardScaler] = {}
        self.sensor_fit_rows_per_mode_: dict[int, int] = {}
        self.fallback_modes_: tuple[int, ...] = ()
        self.fit_engine_ids_: tuple[int, ...] = ()
        self.fit_row_count_: int = 0
        self.healthy_fit_row_count_: int = 0

    def fit(self, train_frame: pd.DataFrame) -> "RegimeSensorPreprocessor":
        _validate_frame(train_frame)
        healthy_mask = healthy_training_mask(train_frame, self.healthy_fraction)
        if not healthy_mask.any():
            raise ValueError("No rows satisfy the healthy training assumption")

        operating_settings = train_frame.loc[:, list(OP_COLUMNS)].to_numpy(dtype=float)
        self.op_scaler_ = StandardScaler().fit(operating_settings)
        scaled_settings = self.op_scaler_.transform(operating_settings)
        self.kmeans_ = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=self.n_init,
        ).fit(scaled_settings)
        modes = self.kmeans_.labels_.astype(int)

        healthy_sensors = train_frame.loc[
            healthy_mask, list(SENSOR_COLUMNS)
        ].to_numpy(dtype=float)
        self.global_sensor_scaler_ = StandardScaler().fit(healthy_sensors)

        fallback_modes: list[int] = []
        self.sensor_scalers_per_mode_ = {}
        self.sensor_fit_rows_per_mode_ = {}
        healthy_values = healthy_mask.to_numpy(dtype=bool)
        for mode in range(self.n_clusters):
            mode_fit_mask = healthy_values & (modes == mode)
            fit_rows = int(mode_fit_mask.sum())
            self.sensor_fit_rows_per_mode_[mode] = fit_rows
            if fit_rows < self.min_mode_fit_rows:
                self.sensor_scalers_per_mode_[mode] = self.global_sensor_scaler_
                fallback_modes.append(mode)
            else:
                self.sensor_scalers_per_mode_[mode] = StandardScaler().fit(
                    train_frame.loc[mode_fit_mask, list(SENSOR_COLUMNS)].to_numpy(
                        dtype=float
                    )
                )

        self.fallback_modes_ = tuple(fallback_modes)
        self.fit_engine_ids_ = tuple(
            sorted(train_frame["engine"].astype(int).unique().tolist())
        )
        self.fit_row_count_ = int(len(train_frame))
        self.healthy_fit_row_count_ = int(healthy_mask.sum())
        return self

    def _require_fitted(self) -> None:
        if (
            self.op_scaler_ is None
            or self.kmeans_ is None
            or self.global_sensor_scaler_ is None
        ):
            raise RuntimeError("Call fit() before using the preprocessor")

    def predict_modes(self, frame: pd.DataFrame) -> np.ndarray:
        _validate_frame(frame)
        self._require_fitted()
        assert self.op_scaler_ is not None
        assert self.kmeans_ is not None
        scaled_settings = self.op_scaler_.transform(
            frame.loc[:, list(OP_COLUMNS)].to_numpy(dtype=float)
        )
        return self.kmeans_.predict(scaled_settings).astype(int)

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        _validate_frame(frame)
        self._require_fitted()
        modes = self.predict_modes(frame)
        transformed = frame.astype(
            {sensor: "float64" for sensor in SENSOR_COLUMNS}
        ).copy()

        for mode in range(self.n_clusters):
            mode_mask = modes == mode
            if not mode_mask.any():
                continue
            scaler = self.sensor_scalers_per_mode_.get(
                mode, self.global_sensor_scaler_
            )
            assert scaler is not None
            transformed.loc[mode_mask, list(SENSOR_COLUMNS)] = scaler.transform(
                frame.loc[mode_mask, list(SENSOR_COLUMNS)].to_numpy(dtype=float)
            )
        transformed["op_mode"] = modes
        return transformed

    def centroids_original_units(self) -> pd.DataFrame:
        self._require_fitted()
        assert self.op_scaler_ is not None
        assert self.kmeans_ is not None
        centroids = self.op_scaler_.inverse_transform(self.kmeans_.cluster_centers_)
        result = pd.DataFrame(centroids, columns=[f"centroid_{c}" for c in OP_COLUMNS])
        result.insert(0, "op_mode", np.arange(self.n_clusters, dtype=int))
        return result

    def fit_metadata(self) -> dict[str, Any]:
        self._require_fitted()
        return {
            "method": self.method,
            "split_manifest_id": self.split_manifest_id,
            "n_clusters": self.n_clusters,
            "healthy_fraction": self.healthy_fraction,
            "random_state": self.random_state,
            "n_init": self.n_init,
            "min_mode_fit_rows": self.min_mode_fit_rows,
            "fit_rows_all_cycles": self.fit_row_count_,
            "operating_scaler_fit_rows": self.fit_row_count_,
            "kmeans_fit_rows": self.fit_row_count_,
            "sensor_scaler_fit_rows": self.healthy_fit_row_count_,
            "sensor_fit_rows_per_mode": self.sensor_fit_rows_per_mode_,
            "fallback_modes": list(self.fallback_modes_),
            "fit_engine_count": len(self.fit_engine_ids_),
            "fit_engine_ids_sha256": _engine_id_digest(self.fit_engine_ids_),
        }


def save_preprocessor(preprocessor: Any, path: Path) -> None:
    """Persist a candidate together with its auditable fit metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "preprocessor": preprocessor,
            "metadata": preprocessor.fit_metadata(),
        },
        path,
    )


def load_preprocessor(
    path: Path, *, expected_split_manifest_id: str | None = None
) -> tuple[Any, dict[str, Any]]:
    payload = joblib.load(path)
    if "preprocessor" not in payload or "metadata" not in payload:
        raise ValueError(f"Invalid preprocessing artifact: {path}")
    metadata = payload["metadata"]
    if (
        expected_split_manifest_id is not None
        and metadata.get("split_manifest_id") != expected_split_manifest_id
    ):
        raise ValueError(
            "Preprocessing artifact split manifest mismatch: "
            f"expected {expected_split_manifest_id}, "
            f"found {metadata.get('split_manifest_id')}"
        )
    return payload["preprocessor"], metadata
