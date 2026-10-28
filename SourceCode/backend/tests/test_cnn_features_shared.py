"""One EfficientNet per process: every job's extractor reuses the model loaded first."""
from __future__ import annotations

import torch
import torchvision.models as models

from app.pipeline import cnn_features


class _TinyNet(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.classifier = torch.nn.Linear(1, 1)

    def forward(self, x):
        return x.mean(dim=(2, 3)).repeat(1, 1280 // 3 + 1)[:, :1280]


def test_extractors_share_one_loaded_model(monkeypatch):
    loads = []

    def fake_efficientnet_b0(weights=None):
        loads.append(weights)
        return _TinyNet()

    monkeypatch.setattr(models, "efficientnet_b0", fake_efficientnet_b0)
    monkeypatch.setattr(cnn_features, "_MODELS", {})

    first = cnn_features.CNNFeatureExtractor()
    second = cnn_features.CNNFeatureExtractor()
    first._load_model()
    second._load_model()

    assert len(loads) == 1
    assert first._model is second._model
