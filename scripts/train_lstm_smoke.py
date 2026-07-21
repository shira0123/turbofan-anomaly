"""Train an LSTM autoencoder on healthy windows and save checkpoints."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from scripts.log_experiment import log_experiment
from src.models.lstm_ae import LSTMAutoencoder


SEQS_PATH = Path("data/processed/sequences_train.npy")
HEALTH_PATH = Path("data/processed/is_healthy_train.npy")
OUT_DIR = Path("models")
REPORT_DIR = Path("reports/lstm_ae")
EXPERIMENTS_DIR = Path("experiments")


@dataclass(frozen=True)
class TrainConfig:
    window_size: int = 30
    input_dim: int = 21
    hidden_dim: int = 64
    latent_dim: int = 16
    num_layers: int = 2
    dropout: float = 0.2
    batch_size: int = 64
    epochs: int = 15
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    smoke: bool = False
    seed: int = 42


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_training_windows(smoke: bool) -> tuple[torch.Tensor, torch.Tensor]:
    if not SEQS_PATH.exists() or not HEALTH_PATH.exists():
        raise FileNotFoundError(
            "Missing processed sequences. Run scripts.create_sequences_save first."
        )

    sequences = np.load(SEQS_PATH).astype(np.float32)
    is_healthy = np.load(HEALTH_PATH).astype(bool)
    healthy_sequences = sequences[is_healthy]

    if healthy_sequences.size == 0:
        raise RuntimeError("No healthy windows available for training")

    if smoke:
        limit = min(256, len(healthy_sequences))
        healthy_sequences = healthy_sequences[:limit]

    split_index = max(1, int(len(healthy_sequences) * 0.9))
    train_sequences = healthy_sequences[:split_index]
    valid_sequences = healthy_sequences[split_index:]
    if len(valid_sequences) == 0:
        valid_sequences = train_sequences[: max(1, min(32, len(train_sequences)))]

    return torch.from_numpy(train_sequences), torch.from_numpy(valid_sequences)


def build_dataloaders(config: TrainConfig) -> tuple[DataLoader, DataLoader, torch.device]:
    train_tensor, valid_tensor = load_training_windows(config.smoke)
    train_loader = DataLoader(
        TensorDataset(train_tensor),
        batch_size=min(config.batch_size, len(train_tensor)),
        shuffle=True,
        drop_last=False,
    )
    valid_loader = DataLoader(
        TensorDataset(valid_tensor),
        batch_size=min(config.batch_size, len(valid_tensor)),
        shuffle=False,
        drop_last=False,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return train_loader, valid_loader, device


def run_epoch(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device, optimizer: torch.optim.Optimizer | None = None) -> float:
    is_training = optimizer is not None
    model.train(is_training)
    total_loss = 0.0
    total_items = 0

    for (batch,) in loader:
        batch = batch.to(device)
        if is_training:
            optimizer.zero_grad(set_to_none=True)

        reconstruction = model(batch)
        loss = criterion(reconstruction, batch)

        if is_training:
            loss.backward()
            optimizer.step()

        batch_size = batch.size(0)
        total_loss += loss.item() * batch_size
        total_items += batch_size

    return total_loss / max(1, total_items)


def save_artifacts(model: LSTMAutoencoder, config: TrainConfig, train_loss: list[float], valid_loss: list[float]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifact_name = f"lstm_ae_{'smoke' if config.smoke else 'full'}_{timestamp}.pt"
    artifact_path = OUT_DIR / artifact_name
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": asdict(config),
        },
        artifact_path,
    )

    pd.DataFrame(
        {"epoch": np.arange(1, len(train_loss) + 1), "train_loss": train_loss, "valid_loss": valid_loss}
    ).to_csv(REPORT_DIR / f"training_curve_{timestamp}.csv", index=False)

    return artifact_path


def parse_args() -> TrainConfig:
    parser = argparse.ArgumentParser(description="Train the LSTM autoencoder")
    parser.add_argument("--full", action="store_true", help="Train on the full healthy-window set")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--latent-dim", type=int, default=16)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    return TrainConfig(
        hidden_dim=args.hidden_dim,
        latent_dim=args.latent_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
        batch_size=args.batch_size,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        smoke=not args.full,
        seed=args.seed,
    )


def main() -> None:
    config = parse_args()
    set_seed(config.seed)

    train_loader, valid_loader, device = build_dataloaders(config)
    model = LSTMAutoencoder(
        input_dim=config.input_dim,
        hidden_dim=config.hidden_dim,
        latent_dim=config.latent_dim,
        num_layers=config.num_layers,
        dropout=config.dropout,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    criterion = nn.MSELoss()

    train_losses: list[float] = []
    valid_losses: list[float] = []

    for _epoch in range(config.epochs):
        train_loss = run_epoch(model, train_loader, criterion, device, optimizer)
        valid_loss = run_epoch(model, valid_loader, criterion, device)
        train_losses.append(train_loss)
        valid_losses.append(valid_loss)

    artifact_path = save_artifacts(model, config, train_losses, valid_losses)

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_lstm_ae_smoke"
    params = {
        "window": config.window_size,
        "hidden": config.hidden_dim,
        "latent": config.latent_dim,
        "layers": config.num_layers,
        "batch": config.batch_size,
        "epochs": config.epochs,
        "smoke": config.smoke,
    }
    log_experiment(
        [
            run_id,
            datetime.now().isoformat(timespec="seconds"),
            "shivam",
            "lstm_autoencoder",
            "lstm_ae",
            str(params),
            len(train_loader.dataset),
            len(valid_loader.dataset),
            "valid_loss",
            f"{valid_losses[-1]:.6f}",
            f"smoke={config.smoke}; final_train_loss={train_losses[-1]:.6f}",
            str(artifact_path),
        ]
    )

    print(
        {
            "device": str(device),
            "train_loss": train_losses[-1],
            "valid_loss": valid_losses[-1],
            "artifact": str(artifact_path),
        }
    )


if __name__ == "__main__":
    main()