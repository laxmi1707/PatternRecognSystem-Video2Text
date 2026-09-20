from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

from app.data_pipeline.types import DatasetSplits, Frame, LabeledExample
from app.ml.config import ACTIVITY_LABELS
from app.training.boosting import BoostingConfig, BoostingEnsemble
from app.training.final_activity_model import FinalActivityModel
from app.training.pipeline import train_final_activity_model

FAST_CONFIG = BoostingConfig(num_rounds=3, inner_epochs=15, inner_batch_size=16)


def _make_separable_dataset(
    n_per_class: int = 20, feature_dim: int = 4
) -> tuple[torch.Tensor, torch.Tensor]:
    rng = torch.Generator().manual_seed(0)
    class0 = torch.randn(n_per_class, feature_dim, generator=rng) * 0.1 - 1.0
    class1 = torch.randn(n_per_class, feature_dim, generator=rng) * 0.1 + 1.0
    features = torch.cat([class0, class1], dim=0)
    labels = torch.cat(
        [torch.zeros(n_per_class, dtype=torch.long), torch.ones(n_per_class, dtype=torch.long)]
    )
    return features, labels


def test_boosting_ensemble_fits_and_predicts_separable_data():
    features, labels = _make_separable_dataset()

    ensemble = BoostingEnsemble(config=FAST_CONFIG)
    ensemble.fit(features, labels)

    assert len(ensemble.base_learners) > 0
    assert len(ensemble.base_learners) == len(ensemble.learner_weights)

    predictions = ensemble.predict(features)
    accuracy = (predictions == labels).float().mean().item()
    assert accuracy > 0.9


def test_boosting_ensemble_predict_before_fit_raises():
    ensemble = BoostingEnsemble(config=FAST_CONFIG)
    with pytest.raises(RuntimeError):
        ensemble.predict(torch.zeros(1, 4))


def test_boosting_ensemble_requires_multiple_classes():
    features = torch.randn(10, 4)
    labels = torch.zeros(10, dtype=torch.long)

    ensemble = BoostingEnsemble(config=FAST_CONFIG)
    with pytest.raises(ValueError):
        ensemble.fit(features, labels)


def test_final_activity_model_predict_and_round_trip(tmp_path: Path):
    features, labels = _make_separable_dataset()

    ensemble = BoostingEnsemble(config=FAST_CONFIG)
    ensemble.fit(features, labels)

    model = FinalActivityModel(ensemble=ensemble, activity_labels=tuple(ACTIVITY_LABELS))

    predicted_label = model.predict_activity(features[0])
    assert predicted_label in ACTIVITY_LABELS
    assert predicted_label == ACTIVITY_LABELS[0]

    checkpoint_path = tmp_path / "final_activity_model.pt"
    model.save(checkpoint_path)
    reloaded = FinalActivityModel.load(checkpoint_path)

    assert reloaded.activity_labels == model.activity_labels
    assert reloaded.predict_activity(features[0]) == predicted_label
    assert reloaded.predict_activity(features[-1]) == model.predict_activity(features[-1])


def _write_frame(tmp_path: Path, video_id: str, frame_index: int, fill_value: int) -> Frame:
    image_path = tmp_path / f"{video_id}_{frame_index}.png"
    image = np.full((60, 100), fill_value, dtype=np.uint8)
    cv2.imwrite(str(image_path), image)
    return Frame(
        video_id=video_id,
        frame_index=frame_index,
        timestamp_s=float(frame_index),
        image_path=image_path,
    )


def _make_dataset_splits(tmp_path: Path) -> DatasetSplits:
    dark_label, light_label = ACTIVITY_LABELS[0], ACTIVITY_LABELS[1]
    examples = []
    for i in range(15):
        frame = _write_frame(tmp_path, video_id="v1", frame_index=i, fill_value=10)
        examples.append(
            LabeledExample(
                frame=frame, activity=dark_label, label_confidence=1.0, label_source="auto"
            )
        )
    for i in range(15):
        frame = _write_frame(tmp_path, video_id="v1", frame_index=100 + i, fill_value=245)
        examples.append(
            LabeledExample(
                frame=frame, activity=light_label, label_confidence=1.0, label_source="auto"
            )
        )
    return DatasetSplits(train=tuple(examples), validation=(), test=())


def test_train_final_activity_model_end_to_end(tmp_path: Path):
    splits = _make_dataset_splits(tmp_path)

    model = train_final_activity_model(splits, boosting_config=FAST_CONFIG)

    assert isinstance(model, FinalActivityModel)
    assert model.activity_labels == tuple(ACTIVITY_LABELS)

    dark_frame = splits.train[0].frame
    from app.data_pipeline.featurize import extract_frame_feature

    dark_features = torch.from_numpy(extract_frame_feature(dark_frame)).unsqueeze(0)
    predicted = model.predict_activity(dark_features)
    assert predicted == ACTIVITY_LABELS[0]


def test_train_final_activity_model_raises_on_empty_splits():
    empty_splits = DatasetSplits(train=(), validation=(), test=())
    with pytest.raises(ValueError):
        train_final_activity_model(empty_splits)


def test_train_final_activity_model_raises_on_unknown_label(tmp_path: Path):
    frame = _write_frame(tmp_path, video_id="v1", frame_index=0, fill_value=100)
    bad_example = LabeledExample(
        frame=frame, activity="not_a_real_activity", label_confidence=1.0, label_source="auto"
    )
    splits = DatasetSplits(train=(bad_example,), validation=(), test=())

    with pytest.raises(ValueError):
        train_final_activity_model(splits)
