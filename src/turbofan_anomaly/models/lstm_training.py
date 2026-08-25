"""Deterministic training utilities for engine-disjoint LSTM validation."""

from __future__ import annotations

import copy
import hashlib
import math
from numbers import Integral
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from turbofan_anomaly.models.lstm_autoencoder import LSTMAutoencoder


@dataclass(frozen=True)
class LSTMArchitecture:
    architecture_id: str
    hidden_dim: int
    latent_dim: int
    num_layers: int
    dropout: float

    def build(self, input_dim: int) -> LSTMAutoencoder:
        return LSTMAutoencoder(
            input_dim=input_dim,
            hidden_dim=self.hidden_dim,
            latent_dim=self.latent_dim,
            num_layers=self.num_layers,
            dropout=self.dropout,
        )


@dataclass(frozen=True)
class TrainingSettings:
    batch_size: int
    max_epochs: int
    minimum_epochs: int
    patience: int
    min_delta: float
    learning_rate: float
    weight_decay: float
    gradient_clip_norm: float

    def __post_init__(self) -> None:
        if self.batch_size < 1 or self.max_epochs < 1:
            raise ValueError("batch_size and max_epochs must be positive")
        if not 1 <= self.minimum_epochs <= self.max_epochs:
            raise ValueError("minimum_epochs must be within the epoch budget")
        if self.patience < 1:
            raise ValueError("patience must be positive")
        if self.learning_rate <= 0.0 or self.weight_decay < 0.0:
            raise ValueError("Invalid optimizer settings")
        if self.gradient_clip_norm <= 0.0:
            raise ValueError("gradient_clip_norm must be positive")


@dataclass
class LSTMFitResult:
    model: LSTMAutoencoder
    history: list[dict[str, float | int]]
    best_epoch: int
    best_monitor_loss: float


@dataclass(frozen=True)
class FixedEpochSettings:
    """Optimization controls for a locked all-training-window refit."""

    batch_size: int
    epoch_count: int
    learning_rate: float
    weight_decay: float
    gradient_clip_norm: float

    def __post_init__(self) -> None:
        if self.batch_size < 1 or self.epoch_count < 1:
            raise ValueError("batch_size and epoch_count must be positive")
        if self.learning_rate <= 0.0 or self.weight_decay < 0.0:
            raise ValueError("Invalid optimizer settings")
        if self.gradient_clip_norm <= 0.0:
            raise ValueError("gradient_clip_norm must be positive")


@dataclass
class FixedEpochFitResult:
    """A locked refit and its complete training-only loss history."""

    model: LSTMAutoencoder
    history: list[dict[str, float | int]]


def engine_id_digest(engine_ids: list[int] | tuple[int, ...]) -> str:
    payload = ",".join(map(str, sorted(map(int, engine_ids)))).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def median_locked_epoch(best_epochs: Sequence[int]) -> int:
    """Return the integer median of exactly three positive best epochs."""
    epochs = list(best_epochs)
    if len(epochs) != 3:
        raise ValueError("Exactly three best epochs are required")
    if any(isinstance(value, bool) or not isinstance(value, Integral) for value in epochs):
        raise ValueError("Best epochs must be positive integers")
    normalized = [int(value) for value in epochs]
    if any(value < 1 for value in normalized):
        raise ValueError("Best epochs must be positive integers")
    return sorted(normalized)[1]


def final_refit_artifact_name(seed: int) -> str:
    """Return the frozen collision-resistant artifact name for one refit seed."""
    if isinstance(seed, bool) or not isinstance(seed, Integral) or int(seed) < 1:
        raise ValueError("seed must be a positive integer")
    return (
        "fd002_lstm_final_v1_locked_p1_k6_"
        f"balanced_64x16_l1_seed{int(seed)}.pt"
    )


def ensure_output_paths_available(paths: Sequence[Path]) -> None:
    """Refuse duplicate or existing destinations before a governed run."""
    resolved = [Path(path).resolve() for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("Output destinations must be unique")
    existing = [path for path in resolved if path.exists()]
    if existing:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing output: {joined}")


def validate_sequence_collection(
    sequences: np.ndarray,
    *,
    expected_window_shape: tuple[int, int],
    expected_count: int | None = None,
    name: str = "sequences",
) -> np.ndarray:
    """Validate a finite chronological sequence collection without copying it."""
    values = np.asarray(sequences)
    if values.ndim != 3 or tuple(values.shape[1:]) != tuple(expected_window_shape):
        raise ValueError(
            f"{name} must have shape (N,{expected_window_shape[0]},"
            f"{expected_window_shape[1]})"
        )
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError(f"{name} must be finite and non-empty")
    if expected_count is not None and len(values) != int(expected_count):
        raise ValueError(
            f"{name} must contain exactly {int(expected_count)} windows"
        )
    return values


def aligned_calibrated_score_ensemble(
    score_frames: Mapping[int, pd.DataFrame],
    *,
    expected_seeds: Sequence[int] = (43, 44, 45),
) -> pd.DataFrame:
    """Average calibrated scores after strict window-ID alignment."""
    seeds = tuple(map(int, expected_seeds))
    if len(seeds) != 3 or len(set(seeds)) != 3:
        raise ValueError("Exactly three unique ensemble seeds are required")
    if set(map(int, score_frames)) != set(seeds):
        raise ValueError("Score frames must match the three registered seeds")

    aligned: dict[int, pd.Series] = {}
    expected_ids: set[Any] | None = None
    for seed in seeds:
        frame = score_frames[seed]
        required = {"window_id", "calibrated_score"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"Missing ensemble columns: {sorted(missing)}")
        if frame["window_id"].isna().any() or frame["window_id"].duplicated().any():
            raise ValueError(f"Seed {seed} has missing or duplicate window IDs")
        values = frame["calibrated_score"].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"Seed {seed} has non-finite calibrated scores")
        series = pd.Series(values, index=frame["window_id"].to_numpy(), name=seed)
        ids = set(series.index)
        if expected_ids is None:
            expected_ids = ids
        elif ids != expected_ids:
            raise ValueError("Ensemble seed window IDs are not identical")
        aligned[seed] = series

    if not expected_ids:
        raise ValueError("Ensemble score frames may not be empty")
    ordered_ids = sorted(expected_ids, key=str)
    output = pd.DataFrame({"window_id": ordered_ids})
    seed_columns: list[str] = []
    for seed in seeds:
        column = f"seed_{seed}_calibrated_score"
        seed_columns.append(column)
        output[column] = aligned[seed].reindex(ordered_ids).to_numpy(dtype=float)
    output["ensemble_calibrated_score"] = output[seed_columns].mean(axis=1)
    return output


def split_eligible_training_windows(
    metadata: pd.DataFrame,
    eligible_mask: np.ndarray,
    *,
    monitor_fraction: float,
    random_state: int,
    n_strata: int = 5,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Split eligible windows by whole engine for optimization monitoring."""
    required = {"engine", "max_cycle", "split"}
    missing = required - set(metadata.columns)
    if missing:
        raise ValueError(f"Missing monitor-split columns: {sorted(missing)}")
    if set(metadata["split"]) != {"train"}:
        raise ValueError("Monitor split may only be created from training metadata")
    eligible = np.asarray(eligible_mask, dtype=bool)
    if eligible.shape != (len(metadata),) or not eligible.any():
        raise ValueError("eligible_mask must select training windows")
    if not 0.0 < monitor_fraction < 1.0:
        raise ValueError("monitor_fraction must be in (0, 1)")

    eligible_metadata = metadata.loc[eligible, ["engine", "max_cycle"]]
    engine_summary = (
        eligible_metadata.groupby("engine", as_index=False)["max_cycle"]
        .max()
        .sort_values("engine")
        .reset_index(drop=True)
    )
    if len(engine_summary) < 2 * n_strata:
        raise ValueError("Not enough eligible engines for stratified monitoring")
    if math.ceil(len(engine_summary) * monitor_fraction) < n_strata:
        raise ValueError("Monitor engine count must cover every stratum")
    ranked_life = engine_summary["max_cycle"].rank(method="first")
    engine_summary["stratum"] = pd.qcut(
        ranked_life, q=n_strata, labels=False
    ).astype(int)
    development_ids, monitor_ids = train_test_split(
        engine_summary["engine"].astype(int).to_numpy(),
        test_size=monitor_fraction,
        random_state=random_state,
        shuffle=True,
        stratify=engine_summary["stratum"].to_numpy(),
    )
    development_set = set(map(int, development_ids))
    monitor_set = set(map(int, monitor_ids))
    if development_set & monitor_set:
        raise RuntimeError("Development and monitor engines overlap")

    engine_values = metadata["engine"].astype(int)
    development_mask = eligible & engine_values.isin(development_set).to_numpy()
    monitor_mask = eligible & engine_values.isin(monitor_set).to_numpy()
    if np.any(development_mask & monitor_mask):
        raise RuntimeError("Development and monitor windows overlap")
    if not np.array_equal(development_mask | monitor_mask, eligible):
        raise RuntimeError("Monitor split does not cover every eligible window")

    roles = np.where(
        engine_summary["engine"].isin(development_set), "development", "monitor"
    )
    split_summary = engine_summary.assign(role=roles).sort_values("engine")
    return development_mask, monitor_mask, split_summary.reset_index(drop=True)


def set_reproducible_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)


def parameter_count(model: nn.Module) -> int:
    return int(sum(parameter.numel() for parameter in model.parameters()))


def _loader(
    sequences: np.ndarray,
    *,
    batch_size: int,
    shuffle: bool,
    seed: int,
    pin_memory: bool,
) -> DataLoader:
    values = np.asarray(sequences, dtype=np.float32)
    if values.ndim != 3 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("Expected finite non-empty [windows, time, sensors] data")
    generator = torch.Generator()
    generator.manual_seed(seed)
    return DataLoader(
        TensorDataset(torch.from_numpy(values)),
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=0,
        pin_memory=pin_memory,
        drop_last=False,
    )


def _mean_squared_error(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    gradient_clip_norm: float,
) -> float:
    model.train(optimizer is not None)
    squared_error = 0.0
    element_count = 0
    for (batch,) in loader:
        batch = batch.to(device, non_blocking=device.type == "cuda")
        if optimizer is not None:
            optimizer.zero_grad(set_to_none=True)
        reconstruction = model(batch)
        loss = torch.mean((reconstruction - batch) ** 2)
        if optimizer is not None:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
            optimizer.step()
        squared_error += float(torch.sum((reconstruction.detach() - batch) ** 2))
        element_count += int(batch.numel())
    return squared_error / element_count


def fit_lstm_autoencoder(
    development_sequences: np.ndarray,
    monitor_sequences: np.ndarray,
    *,
    architecture: LSTMArchitecture,
    settings: TrainingSettings,
    seed: int,
    device: torch.device,
) -> LSTMFitResult:
    if development_sequences.shape[1:] != monitor_sequences.shape[1:]:
        raise ValueError("Development and monitor sequence shapes disagree")
    set_reproducible_seed(seed)
    model = architecture.build(int(development_sequences.shape[-1])).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.learning_rate,
        weight_decay=settings.weight_decay,
    )
    development_loader = _loader(
        development_sequences,
        batch_size=settings.batch_size,
        shuffle=True,
        seed=seed,
        pin_memory=device.type == "cuda",
    )
    monitor_loader = _loader(
        monitor_sequences,
        batch_size=settings.batch_size,
        shuffle=False,
        seed=seed,
        pin_memory=device.type == "cuda",
    )

    best_loss = float("inf")
    best_epoch = 0
    best_state: dict[str, torch.Tensor] | None = None
    epochs_without_improvement = 0
    history: list[dict[str, float | int]] = []
    for epoch in range(1, settings.max_epochs + 1):
        train_loss = _mean_squared_error(
            model,
            development_loader,
            device,
            optimizer,
            settings.gradient_clip_norm,
        )
        with torch.no_grad():
            monitor_loss = _mean_squared_error(
                model,
                monitor_loader,
                device,
                None,
                settings.gradient_clip_norm,
            )
        history.append(
            {
                "epoch": epoch,
                "development_loss": train_loss,
                "monitor_loss": monitor_loss,
            }
        )
        if monitor_loss < best_loss - settings.min_delta:
            best_loss = monitor_loss
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
        if (
            epoch >= settings.minimum_epochs
            and epochs_without_improvement >= settings.patience
        ):
            break
    if best_state is None:
        raise RuntimeError("Training did not produce a checkpoint")
    model.load_state_dict(best_state)
    return LSTMFitResult(model, history, best_epoch, float(best_loss))


def fit_lstm_autoencoder_fixed_epochs(
    training_sequences: np.ndarray,
    *,
    architecture: LSTMArchitecture,
    settings: FixedEpochSettings,
    seed: int,
    device: torch.device,
) -> FixedEpochFitResult:
    """Fit on one training collection for exactly the locked epoch count.

    This function intentionally has no monitor or validation input. It is the
    distinct all-training-window path used only after the epoch rule is locked.
    """
    values = np.asarray(training_sequences)
    if values.ndim != 3:
        raise ValueError(
            "fixed-epoch training sequences must have shape (N,time,sensors)"
        )
    sequences = validate_sequence_collection(
        values,
        expected_window_shape=(
            int(values.shape[1]),
            int(values.shape[2]),
        ),
        name="fixed-epoch training sequences",
    )
    set_reproducible_seed(seed)
    model = architecture.build(int(sequences.shape[-1])).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.learning_rate,
        weight_decay=settings.weight_decay,
    )
    loader = _loader(
        sequences,
        batch_size=settings.batch_size,
        shuffle=True,
        seed=seed,
        pin_memory=device.type == "cuda",
    )
    history: list[dict[str, float | int]] = []
    for epoch in range(1, settings.epoch_count + 1):
        training_loss = _mean_squared_error(
            model,
            loader,
            device,
            optimizer,
            settings.gradient_clip_norm,
        )
        history.append({"epoch": epoch, "training_loss": training_loss})
    if len(history) != settings.epoch_count:
        raise RuntimeError("Fixed-epoch fit did not complete the locked epoch count")
    return FixedEpochFitResult(model=model, history=history)


def reconstruction_errors(
    model: nn.Module,
    sequences: np.ndarray,
    *,
    batch_size: int,
    device: torch.device,
) -> np.ndarray:
    loader = _loader(
        sequences,
        batch_size=batch_size,
        shuffle=False,
        seed=0,
        pin_memory=device.type == "cuda",
    )
    model.eval()
    scores: list[np.ndarray] = []
    with torch.no_grad():
        for (batch,) in loader:
            batch = batch.to(device, non_blocking=device.type == "cuda")
            reconstruction = model(batch)
            error = torch.mean((reconstruction - batch) ** 2, dim=(1, 2))
            scores.append(error.cpu().numpy())
    result = np.concatenate(scores).astype(np.float64)
    if not np.isfinite(result).all():
        raise RuntimeError("Model produced non-finite reconstruction errors")
    return result


def save_lstm_artifact(
    model: LSTMAutoencoder,
    architecture: LSTMArchitecture,
    score_reference: np.ndarray,
    metadata: dict[str, Any],
    path: Path,
) -> None:
    reference = np.asarray(score_reference, dtype=np.float64).reshape(-1)
    if len(reference) == 0 or not np.isfinite(reference).all():
        raise ValueError("score_reference must be finite and non-empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        name: tensor.detach().cpu().clone()
        for name, tensor in model.state_dict().items()
    }
    torch.save(
        {
            "state_dict": state,
            "architecture": asdict(architecture),
            "sorted_training_scores": np.sort(reference),
            "metadata": dict(metadata),
        },
        path,
    )


def load_lstm_artifact(
    path: Path,
    *,
    expected_split_manifest_id: str | None = None,
    expected_preprocessing_decision_id: str | None = None,
) -> tuple[LSTMAutoencoder, np.ndarray, dict[str, Any]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    required = {"state_dict", "architecture", "sorted_training_scores", "metadata"}
    if not required.issubset(payload):
        raise ValueError(f"Invalid LSTM artifact: {path}")
    metadata = payload["metadata"]
    if (
        expected_split_manifest_id is not None
        and metadata.get("split_manifest_id") != expected_split_manifest_id
    ):
        raise ValueError("LSTM artifact split manifest mismatch")
    if (
        expected_preprocessing_decision_id is not None
        and metadata.get("preprocessing_decision_id")
        != expected_preprocessing_decision_id
    ):
        raise ValueError("LSTM artifact preprocessing decision mismatch")
    architecture = LSTMArchitecture(**payload["architecture"])
    model = architecture.build(int(metadata["input_dim"]))
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, np.asarray(payload["sorted_training_scores"]), metadata
