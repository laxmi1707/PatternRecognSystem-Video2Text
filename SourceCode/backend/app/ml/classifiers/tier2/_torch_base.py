from abc import abstractmethod

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from app.ml.base import BaseClassifier, PredictionResult


class TorchBaseClassifier(BaseClassifier):

    def __init__(
        self,
        epochs: int = 20,
        batch_size: int = 32,
        learning_rate: float = 1e-3,
        seed: int = 42,
        num_classes: int = 10,
    ) -> None:
        self._epochs = epochs
        self._batch_size = batch_size
        self._learning_rate = learning_rate
        self._seed = seed
        self._num_classes = num_classes
        self._model: nn.Module | None = None
        self._input_dim: int | None = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @property
    def tier(self) -> str:
        return "tier2"

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def _build_model(self, input_dim: int) -> nn.Module: ...

    @abstractmethod
    def _reshape_input(self, X: torch.Tensor) -> torch.Tensor: ...

    def _seed_everything(self) -> None:
        torch.manual_seed(self._seed)
        np.random.seed(self._seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self._seed)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._seed_everything()
        self._input_dim = X.shape[1]
        self._model = self._build_model(self._input_dim)
        self._model.to(self._device)
        self._model.train()

        X_t = torch.tensor(X, dtype=torch.float32, device=self._device)
        y_t = torch.tensor(y, dtype=torch.long, device=self._device)
        loader = DataLoader(
            TensorDataset(X_t, y_t),
            batch_size=self._batch_size,
            shuffle=True,
        )

        optimizer = torch.optim.Adam(self._model.parameters(), lr=self._learning_rate)
        criterion = nn.CrossEntropyLoss()

        for _ in range(self._epochs):
            for X_batch, y_batch in loader:
                X_batch = self._reshape_input(X_batch)
                logits = self._model(X_batch)
                loss = criterion(logits, y_batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        self._model.eval()

    def predict(self, X: np.ndarray) -> PredictionResult:
        def _predict(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            X_t = torch.tensor(X, dtype=torch.float32, device=self._device)
            X_t = self._reshape_input(X_t)
            with torch.no_grad():
                logits = self._model(X_t)
                probas = F.softmax(logits, dim=1).cpu().numpy()
                labels = np.argmax(probas, axis=1)
            return labels, probas

        return self._timed_predict(_predict, X)

    def save(self, path: str) -> None:
        torch.save(
            {
                "state_dict": self._model.state_dict(),
                "input_dim": self._input_dim,
            },
            path,
        )

    def load(self, path: str) -> None:
        checkpoint = torch.load(path, map_location=self._device, weights_only=False)
        self._input_dim = checkpoint["input_dim"]
        self._model = self._build_model(self._input_dim)
        self._model.load_state_dict(checkpoint["state_dict"])
        self._model.to(self._device)
        self._model.eval()

    def get_params(self) -> dict:
        return {
            "epochs": self._epochs,
            "batch_size": self._batch_size,
            "learning_rate": self._learning_rate,
        }
