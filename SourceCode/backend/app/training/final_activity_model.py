from __future__ import annotations

from pathlib import Path

import torch

from app.training.base_classifier import BaseActivityClassifier
from app.training.boosting import BoostingEnsemble


class FinalActivityModel:
    def __init__(self, ensemble: BoostingEnsemble, activity_labels: tuple[str, ...]) -> None:
        self.ensemble = ensemble
        self.activity_labels = activity_labels

    def predict_activity(self, features: torch.Tensor) -> str:
        if features.dim() == 1:
            features = features.unsqueeze(0)

        predicted = self.ensemble.predict(features)
        return self.activity_labels[int(predicted[0].item())]

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        torch.save(
            {
                "activity_labels": self.activity_labels,
                "boosting_config": self.ensemble.config,
                "learner_weights": self.ensemble.learner_weights,
                "learner_configs": [learner.config for learner in self.ensemble.base_learners],
                "learner_state_dicts": [
                    learner.state_dict() for learner in self.ensemble.base_learners
                ],
            },
            path,
        )

    @classmethod
    def load(cls, path: Path) -> FinalActivityModel:
        checkpoint = torch.load(Path(path), map_location="cpu", weights_only=False)

        base_learners = []
        for config, state_dict in zip(
            checkpoint["learner_configs"], checkpoint["learner_state_dicts"]
        ):
            learner = BaseActivityClassifier(config)
            learner.load_state_dict(state_dict)
            learner.eval()
            base_learners.append(learner)

        ensemble = BoostingEnsemble(
            config=checkpoint["boosting_config"],
            base_learners=base_learners,
            learner_weights=checkpoint["learner_weights"],
        )

        return cls(ensemble=ensemble, activity_labels=checkpoint["activity_labels"])
