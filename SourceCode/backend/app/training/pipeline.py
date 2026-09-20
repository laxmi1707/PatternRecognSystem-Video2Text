from __future__ import annotations

import numpy as np
import torch

from app.data_pipeline.featurize import extract_frame_feature
from app.data_pipeline.types import DatasetSplits, LabeledExample
from app.ml.config import ACTIVITY_LABELS
from app.training.boosting import BoostingConfig, BoostingEnsemble
from app.training.final_activity_model import FinalActivityModel


def _labeled_examples_to_tensors(
    examples: tuple[LabeledExample, ...],
) -> tuple[torch.Tensor, torch.Tensor]:
    if not examples:
        raise ValueError("no labeled examples to train on")

    features = []
    labels = []
    for example in examples:
        if example.activity not in ACTIVITY_LABELS:
            raise ValueError(f"unknown activity label: {example.activity!r}")
        features.append(extract_frame_feature(example.frame))
        labels.append(ACTIVITY_LABELS.index(example.activity))

    X = np.stack(features).astype(np.float32)
    y = np.array(labels, dtype=np.int64)
    return torch.from_numpy(X), torch.from_numpy(y)


def train_final_activity_model(
    splits: DatasetSplits,
    boosting_config: BoostingConfig | None = None,
) -> FinalActivityModel:
    features, labels = _labeled_examples_to_tensors(splits.train)

    ensemble = BoostingEnsemble(config=boosting_config or BoostingConfig())
    ensemble.fit(features, labels)

    return FinalActivityModel(ensemble=ensemble, activity_labels=tuple(ACTIVITY_LABELS))
