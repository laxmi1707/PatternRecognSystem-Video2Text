import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from app.ml.classifiers.tier2._torch_base import TorchBaseClassifier


class _LSTMNetwork(nn.Module):
    def __init__(
        self, token_dim: int, hidden_dim: int, num_layers: int,
        num_classes: int, dropout: float,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=token_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, (h_n, _) = self.lstm(x)
        return self.head(h_n[-1])


class LSTMClassifier(TorchBaseClassifier):
    def __init__(
        self, hidden_dim: int = 64, num_layers: int = 1,
        seq_len: int = 10, dropout: float = 0.3, **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._hidden_dim = hidden_dim
        self._num_layers = num_layers
        self._seq_len = seq_len
        self._dropout = dropout
        self._token_dim: int | None = None

    @property
    def name(self) -> str:
        return "lstm"

    def _build_model(self, input_dim: int) -> nn.Module:
        self._token_dim = math.ceil(input_dim / self._seq_len)
        self._model = _LSTMNetwork(
            self._token_dim, self._hidden_dim, self._num_layers,
            self._num_classes, self._dropout,
        )
        return self._model

    def _reshape_input(self, X: torch.Tensor) -> torch.Tensor:
        padded_len = self._seq_len * self._token_dim
        if X.shape[1] < padded_len:
            X = F.pad(X, (0, padded_len - X.shape[1]))
        return X.view(X.shape[0], self._seq_len, self._token_dim)

    def get_params(self) -> dict:
        return {
            "hidden_dim": self._hidden_dim,
            "num_layers": self._num_layers,
            "seq_len": self._seq_len,
            "dropout": self._dropout,
            **super().get_params(),
        }
