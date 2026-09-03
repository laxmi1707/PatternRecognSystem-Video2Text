import torch
import torch.nn as nn

from app.ml.classifiers.tier2._torch_base import TorchBaseClassifier


class _CNN1DNetwork(nn.Module):
    def __init__(
        self, num_filters: int, kernel_size: int,
        num_classes: int, dropout: float,
    ) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(1, num_filters, kernel_size, padding="same"),
            nn.ReLU(),
            nn.BatchNorm1d(num_filters),
            nn.Conv1d(num_filters, num_filters, kernel_size, padding="same"),
            nn.ReLU(),
            nn.BatchNorm1d(num_filters),
            nn.AdaptiveAvgPool1d(1),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(num_filters, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


class CNN1DClassifier(TorchBaseClassifier):
    def __init__(
        self, num_filters: int = 64, kernel_size: int = 3,
        dropout: float = 0.3, **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._num_filters = num_filters
        self._kernel_size = kernel_size
        self._dropout = dropout

    @property
    def name(self) -> str:
        return "cnn1d"

    def _build_model(self, input_dim: int) -> nn.Module:
        self._model = _CNN1DNetwork(
            self._num_filters, self._kernel_size,
            self._num_classes, self._dropout,
        )
        return self._model

    def _reshape_input(self, X: torch.Tensor) -> torch.Tensor:
        return X.unsqueeze(1)

    def get_params(self) -> dict:
        return {
            "num_filters": self._num_filters,
            "kernel_size": self._kernel_size,
            "dropout": self._dropout,
            **super().get_params(),
        }
