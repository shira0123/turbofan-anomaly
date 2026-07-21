"""Minimal inference service for the turbofan anomaly pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI

from src.data.domain_adapter import OperatingConditionNormalizer
from src.models.lstm_ae import LSTMAutoencoder
from src.thresholding import AdaptiveThresholdEngine


ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"


class AnomalyService:
    def __init__(self, models_dir: Path | None = None) -> None:
        self.models_dir = models_dir or MODELS_DIR
        self.adapter = None
        self.model = None
        self.engine = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        adapter_path = self.models_dir / "kmeans_clusterer.pkl"
        scaler_paths = sorted(self.models_dir.glob("scaler_cluster_*.pkl"))
        threshold_path = self.models_dir / "adaptive_threshold.pkl"
        checkpoint_paths = sorted(self.models_dir.glob("lstm_ae_*.pt"))

        if not adapter_path.exists() or not scaler_paths or not threshold_path.exists() or not checkpoint_paths:
            raise FileNotFoundError("Missing trained artifacts. Run the preprocessing and training scripts first.")

        self.adapter = OperatingConditionNormalizer(n_clusters=4)
        self.adapter.kmeans = joblib.load(adapter_path)
        self.adapter.scalers_per_mode = {int(p.stem.split("_")[-1]): joblib.load(p) for p in scaler_paths}

        self.engine = joblib.load(threshold_path)

        checkpoint_path = checkpoint_paths[-1]
        payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        config = payload.get("config", {})
        self.model = LSTMAutoencoder(
            input_dim=config.get("input_dim", 21),
            hidden_dim=config.get("hidden_dim", 64),
            latent_dim=config.get("latent_dim", 16),
            num_layers=config.get("num_layers", 2),
            dropout=config.get("dropout", 0.2),
        )
        self.model.load_state_dict(payload["model_state_dict"])
        self.model.eval()

    def _prepare_window(self, row_records: List[Dict[str, Any]]) -> np.ndarray:
        if not row_records:
            raise ValueError("At least one row is required")

        df = pd.DataFrame(row_records)
        missing = [col for col in ["op1", "op2", "op3"] + [f"sensor_{i}" for i in range(1, 22)] if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        sensor_cols = [f"sensor_{i}" for i in range(1, 22)]
        features = df[["op1", "op2", "op3"] + sensor_cols].copy()
        features = self.adapter.transform(features)
        return features[sensor_cols].to_numpy(dtype=np.float32)

    def _reconstruction_error(self, window: np.ndarray) -> float:
        with torch.no_grad():
            tensor = torch.from_numpy(window.astype(np.float32)).unsqueeze(0)
            reconstruction = self.model(tensor)
            error = torch.mean((tensor - reconstruction) ** 2, dim=(1, 2)).item()
        return float(error)

    def predict_window(self, row_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        window = self._prepare_window(row_records)
        row_frame = pd.DataFrame(row_records)
        op_mode = int(self.adapter.kmeans.predict(row_frame[["op1", "op2", "op3"]].to_numpy())[0])
        reconstruction_error = self._reconstruction_error(window)
        alert, threshold, smoothed_score = self.engine.process_inference_cycle(reconstruction_error, op_mode)
        return {
            "alert": bool(alert),
            "score": float(smoothed_score),
            "threshold": float(threshold),
            "op_mode": op_mode,
            "reconstruction_error": float(reconstruction_error),
        }


app = FastAPI(title="Turbofan anomaly API")
service = AnomalyService()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "model": "lstm_autoencoder"}


@app.post("/predict")
def predict(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = payload.get("rows", [])
    if not rows:
        return {"alert": False, "score": 0.0, "threshold": 0.0, "op_mode": -1, "reconstruction_error": 0.0}
    return service.predict_window(rows)


def create_app() -> FastAPI:
    return app
