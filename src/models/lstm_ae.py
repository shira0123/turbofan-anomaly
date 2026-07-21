"""LSTM autoencoder for turbofan sequence reconstruction."""

from __future__ import annotations

import torch
from torch import nn


class LSTMAutoencoder(nn.Module):
    """Sequence-to-sequence LSTM autoencoder."""

    def __init__(
        self,
        input_dim: int = 21,
        hidden_dim: int = 64,
        latent_dim: int = 16,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        if num_layers < 1:
            raise ValueError("num_layers must be at least 1")

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.num_layers = num_layers

        lstm_dropout = dropout if num_layers > 1 else 0.0

        self.encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
        )
        self.to_latent = nn.Linear(hidden_dim, latent_dim)
        self.from_latent = nn.Linear(latent_dim, hidden_dim)
        self.decoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
        )
        self.reconstruction_head = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Reconstruct a batch of sequences with shape [batch, time, sensors]."""
        if x.dim() != 3:
            raise ValueError("Expected input with shape [batch, time, sensors]")

        batch_size, seq_len, _ = x.shape
        _, (hidden_state, _) = self.encoder(x)
        encoded = hidden_state[-1]
        latent = self.to_latent(encoded)

        decoder_seed = self.from_latent(latent).unsqueeze(1).repeat(1, seq_len, 1)
        decoded, _ = self.decoder(decoder_seed)
        reconstruction = self.reconstruction_head(decoded)
        return reconstruction
