import torch
import torch.nn as nn

from app.ml.classifiers.tier2._torch_base import TorchBaseClassifier


class _MLPNetwork(nn.Module):
    def __init__(
        self, input_dim: int, hidden_dim: int, num_layers: int,
        num_classes: int, dropout: float,
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        layers += [nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout)]
        for _ in range(num_layers - 1):
            layers += [nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout)]
        layers.append(nn.Linear(hidden_dim, num_classes))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class MLPClassifier(TorchBaseClassifier):
    def __init__(
        self, hidden_dim: int = 128, num_layers: int = 2,
        dropout: float = 0.3, **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._hidden_dim = hidden_dim
        self._num_layers = num_layers
        self._dropout = dropout

    @property
    def name(self) -> str:
        return "mlp"

    def _build_model(self, input_dim: int) -> nn.Module:
        self._model = _MLPNetwork(
            input_dim, self._hidden_dim, self._num_layers,
            self._num_classes, self._dropout,
        )
        return self._model

    def _reshape_input(self, X: torch.Tensor) -> torch.Tensor:
        return X

    def get_params(self) -> dict:
        return {
            "hidden_dim": self._hidden_dim,
            "num_layers": self._num_layers,
            "dropout": self._dropout,
            **super().get_params(),
        }
