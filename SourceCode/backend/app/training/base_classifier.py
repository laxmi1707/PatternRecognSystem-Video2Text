from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class BaseClassifierConfig:
    num_classes: int
    feature_dim: int
    dropout: float = 0.3


class BaseActivityClassifier(nn.Module):
    def __init__(self, config: BaseClassifierConfig) -> None:
        super().__init__()
        self.config = config
        self.net = nn.Sequential(
            nn.Linear(config.feature_dim, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(config.dropout),
            nn.Linear(256, config.num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch_size, feature_dim) -> (batch_size, num_classes)
        return self.net(x)
