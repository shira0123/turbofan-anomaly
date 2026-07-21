"""Export LSTM autoencoder reconstruction scores for phase 4 thresholding."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from scripts.log_experiment import log_experiment
from src.models.lstm_ae import LSTMAutoencoder


SEQS_PATH = Path("data/processed/sequences_train.npy")
MODES_PATH = Path("data/processed/op_modes_train.npy")
HEALTH_PATH = Path("data/processed/is_healthy_train.npy")
REPORT_DIR = Path("reports/lstm_ae")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export reconstruction errors from an LSTM AE checkpoint")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to a checkpoint produced by scripts.train_lstm_smoke",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(REPORT_DIR / "reconstruction_scores.csv"),
        help="CSV output path for per-window scores",
    )
    return parser.parse_args()


def find_latest_checkpoint() -> Path:
    candidates = sorted(Path("models").glob("lstm_ae_*.pt"))
    if not candidates:
        raise FileNotFoundError("No LSTM autoencoder checkpoint found in models/")
    return candidates[-1]


def load_checkpoint(checkpoint_path: Path) -> tuple[LSTMAutoencoder, dict]:
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config = payload.get("config", {})
    model = LSTMAutoencoder(
        input_dim=config.get("input_dim", 21),
        hidden_dim=config.get("hidden_dim", 64),
        latent_dim=config.get("latent_dim", 16),
        num_layers=config.get("num_layers", 2),
        dropout=config.get("dropout", 0.2),
    )
    model.load_state_dict(payload["model_state_dict"])
    model.eval()
    return model, config


def ensure_inputs() -> None:
    missing = [str(path) for path in [SEQS_PATH, MODES_PATH, HEALTH_PATH] if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing sequence inputs: {missing}")


def compute_reconstruction_errors(model: LSTMAutoencoder, sequences: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        tensor = torch.from_numpy(sequences.astype(np.float32))
        reconstruction = model(tensor)
        errors = torch.mean((tensor - reconstruction) ** 2, dim=(1, 2))
    return errors.cpu().numpy()


def main() -> None:
    args = parse_args()
    ensure_inputs()

    checkpoint_path = Path(args.checkpoint) if args.checkpoint else find_latest_checkpoint()
    model, config = load_checkpoint(checkpoint_path)

    sequences = np.load(SEQS_PATH)
    op_modes = np.load(MODES_PATH)
    is_healthy = np.load(HEALTH_PATH).astype(int)

    if len(sequences) != len(op_modes) or len(sequences) != len(is_healthy):
        raise RuntimeError("Sequence metadata arrays do not align")

    errors = compute_reconstruction_errors(model, sequences)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    score_df = pd.DataFrame(
        {
            "window_index": np.arange(len(errors)),
            "op_mode": op_modes,
            "is_healthy": is_healthy,
            "reconstruction_error": errors,
        }
    )
    score_df.to_csv(output_path, index=False)
    np.save(REPORT_DIR / "reconstruction_errors.npy", errors)

    summary = {
        "checkpoint": str(checkpoint_path),
        "mean_error": float(errors.mean()),
        "median_error": float(np.median(errors)),
        "max_error": float(errors.max()),
        "rows": len(errors),
        "hidden_dim": config.get("hidden_dim", 64),
        "latent_dim": config.get("latent_dim", 16),
    }

    summary_path = REPORT_DIR / "reconstruction_summary.csv"
    pd.DataFrame([summary]).to_csv(summary_path, index=False)

    log_experiment(
        [
            f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_lstm_ae_scores",
            datetime.now().isoformat(timespec="seconds"),
            "shivam",
            "lstm_autoencoder_scores",
            "lstm_ae",
            str({
                "checkpoint": str(checkpoint_path),
                "input_dim": config.get("input_dim", 21),
                "hidden_dim": config.get("hidden_dim", 64),
                "latent_dim": config.get("latent_dim", 16),
                "num_layers": config.get("num_layers", 2),
                "dropout": config.get("dropout", 0.2),
            }),
            len(sequences),
            len(sequences),
            "mean_reconstruction_error",
            f"{summary['mean_error']:.6f}",
            f"checkpoint={checkpoint_path}; max_error={summary['max_error']:.6f}",
            str(output_path),
        ]
    )

    print(summary)


if __name__ == "__main__":
    main()