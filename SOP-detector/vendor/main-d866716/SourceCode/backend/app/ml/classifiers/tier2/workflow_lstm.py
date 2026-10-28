from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from app.ml.base import BaseClassifier, PredictionResult


class _WorkflowLSTMNet(nn.Module):
    def __init__(
        self,
        feature_dim: int,
        hidden_dim: int,
        num_layers: int,
        num_classes: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=feature_dim,
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


class WorkflowLSTMClassifier(BaseClassifier):
    """LSTM that operates on real temporal sequences of segment features.

    Input: X of shape (n_tasks, max_segments * feature_dim) — flattened.
    Internally reshaped to (n_tasks, max_segments, feature_dim).
    """

    def __init__(
        self,
        feature_dim: int = 150,
        max_segments: int = 20,
        hidden_dim: int = 128,
        num_layers: int = 2,
        num_classes: int = 10,
        dropout: float = 0.3,
        epochs: int = 30,
        batch_size: int = 16,
        learning_rate: float = 1e-3,
        seed: int = 42,
    ) -> None:
        self._feature_dim = feature_dim
        self._max_segments = max_segments
        self._hidden_dim = hidden_dim
        self._num_layers = num_layers
        self._num_classes = num_classes
        self._dropout = dropout
        self._epochs = epochs
        self._batch_size = batch_size
        self._lr = learning_rate
        self._seed = seed
        self._model: _WorkflowLSTMNet | None = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @property
    def name(self) -> str:
        return "workflow_lstm"

    @property
    def tier(self) -> str:
        return "tier2"

    def _reshape(self, X: torch.Tensor) -> torch.Tensor:
        expected = self._max_segments * self._feature_dim
        if X.shape[1] < expected:
            X = F.pad(X, (0, expected - X.shape[1]))
        elif X.shape[1] > expected:
            X = X[:, :expected]
        return X.view(X.shape[0], self._max_segments, self._feature_dim)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        torch.manual_seed(self._seed)
        np.random.seed(self._seed)

        self._model = _WorkflowLSTMNet(
            self._feature_dim, self._hidden_dim, self._num_layers,
            self._num_classes, self._dropout,
        ).to(self._device)

        X_t = torch.tensor(X, dtype=torch.float32, device=self._device)
        y_t = torch.tensor(y, dtype=torch.long, device=self._device)

        loader = DataLoader(
            TensorDataset(X_t, y_t), batch_size=self._batch_size, shuffle=True,
        )

        optimizer = torch.optim.Adam(self._model.parameters(), lr=self._lr)
        criterion = nn.CrossEntropyLoss()

        self._model.train()
        for _ in range(self._epochs):
            for xb, yb in loader:
                xb = self._reshape(xb)
                logits = self._model(xb)
                loss = criterion(logits, yb)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        self._model.eval()

    def predict(self, X: np.ndarray) -> PredictionResult:
        def _predict(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            X_t = torch.tensor(X, dtype=torch.float32, device=self._device)
            X_t = self._reshape(X_t)
            with torch.no_grad():
                logits = self._model(X_t)
                probas = F.softmax(logits, dim=1).cpu().numpy()
                labels = np.argmax(probas, axis=1)
            return labels, probas

        return self._timed_predict(_predict, X)

    def save(self, path: str) -> None:
        torch.save({"state_dict": self._model.state_dict()}, path)

    def load(self, path: str) -> None:
        self._model = _WorkflowLSTMNet(
            self._feature_dim, self._hidden_dim, self._num_layers,
            self._num_classes, self._dropout,
        ).to(self._device)
        checkpoint = torch.load(path, map_location=self._device, weights_only=False)
        self._model.load_state_dict(checkpoint["state_dict"])
        self._model.eval()

    def get_params(self) -> dict:
        return {
            "feature_dim": self._feature_dim,
            "max_segments": self._max_segments,
            "hidden_dim": self._hidden_dim,
            "num_layers": self._num_layers,
            "dropout": self._dropout,
            "epochs": self._epochs,
        }
