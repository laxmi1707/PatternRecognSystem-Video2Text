import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from app.ml.classifiers.tier2._torch_base import TorchBaseClassifier


class _SinusoidalPE(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512) -> None:
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float) * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model > 1:
            pe[:, 1::2] = torch.cos(position * div_term[:d_model // 2])
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, :x.size(1)]


class _TransformerNetwork(nn.Module):
    def __init__(
        self, token_dim: int, d_model: int, nhead: int,
        num_encoder_layers: int, dim_feedforward: int,
        num_classes: int, seq_len: int, dropout: float,
    ) -> None:
        super().__init__()
        self.projection = nn.Linear(token_dim, d_model)
        self.pe = _SinusoidalPE(d_model, max_len=seq_len)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=dim_feedforward,
            dropout=dropout, batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_encoder_layers)
        self.head = nn.Linear(d_model, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.projection(x)
        x = self.pe(x)
        x = self.encoder(x)
        x = x.mean(dim=1)
        return self.head(x)


class TransformerClassifier(TorchBaseClassifier):
    def __init__(
        self, d_model: int = 32, nhead: int = 4,
        num_encoder_layers: int = 2, dim_feedforward: int = 128,
        seq_len: int = 10, dropout: float = 0.1, **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._d_model = d_model
        self._nhead = nhead
        self._num_encoder_layers = num_encoder_layers
        self._dim_feedforward = dim_feedforward
        self._seq_len = seq_len
        self._dropout = dropout
        self._token_dim: int | None = None

    @property
    def name(self) -> str:
        return "transformer"

    def _build_model(self, input_dim: int) -> nn.Module:
        self._token_dim = math.ceil(input_dim / self._seq_len)
        self._model = _TransformerNetwork(
            self._token_dim, self._d_model, self._nhead,
            self._num_encoder_layers, self._dim_feedforward,
            self._num_classes, self._seq_len, self._dropout,
        )
        return self._model

    def _reshape_input(self, X: torch.Tensor) -> torch.Tensor:
        padded_len = self._seq_len * self._token_dim
        if X.shape[1] < padded_len:
            X = F.pad(X, (0, padded_len - X.shape[1]))
        return X.view(X.shape[0], self._seq_len, self._token_dim)

    def get_params(self) -> dict:
        return {
            "d_model": self._d_model,
            "nhead": self._nhead,
            "num_encoder_layers": self._num_encoder_layers,
            "dim_feedforward": self._dim_feedforward,
            "seq_len": self._seq_len,
            "dropout": self._dropout,
            **super().get_params(),
        }
