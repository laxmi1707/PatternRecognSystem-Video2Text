from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch
from torch import nn

from app.training.base_classifier import BaseActivityClassifier, BaseClassifierConfig


@dataclass
class BoostingConfig:
    num_rounds: int = 10
    learning_rate: float = 0.1
    dropout: float = 0.3
    inner_epochs: int = 20
    inner_batch_size: int = 32
    inner_learning_rate: float = 1e-3
    seed: int = 42


# Combines successive BaseActivityClassifier rounds, reweighting hard examples
# each round — distinct from evidence fusion in
# app.data_pipeline.labeling.evidence_fusion, which votes/stacks across
# evidence sources (OCR, UI detection) to produce a single candidate label.
#
# Implements SAMME (multiclass AdaBoost): each round trains a fresh weak
# learner on the current sample weights (via a weighted cross-entropy loss
# rather than resampling), scores it by weighted training error, and derives
# a learner weight (alpha) from that error. Samples the ensemble still gets
# wrong are upweighted for the next round.
@dataclass
class BoostingEnsemble:
    config: BoostingConfig
    base_learners: list[BaseActivityClassifier] = field(default_factory=list)
    learner_weights: list[float] = field(default_factory=list)

    def fit(self, features: torch.Tensor, labels: torch.Tensor) -> None:
        num_samples, feature_dim = features.shape
        num_classes = int(labels.max().item()) + 1
        if num_classes < 2:
            raise ValueError("boosting requires at least 2 distinct classes")

        torch.manual_seed(self.config.seed)

        self.base_learners = []
        self.learner_weights = []

        sample_weights = torch.full((num_samples,), 1.0 / num_samples)

        for _ in range(self.config.num_rounds):
            learner = BaseActivityClassifier(
                BaseClassifierConfig(
                    num_classes=num_classes,
                    feature_dim=feature_dim,
                    dropout=self.config.dropout,
                )
            )
            self._fit_weak_learner(learner, features, labels, sample_weights)

            with torch.no_grad():
                predictions = learner(features).argmax(dim=1)
            incorrect = (predictions != labels).float()

            weighted_error = torch.sum(sample_weights * incorrect).item()
            weighted_error = min(max(weighted_error, 1e-10), 1 - 1e-10)

            # SAMME learner weight: rewards better-than-chance learners even
            # with >2 classes (plain AdaBoost's formula assumes 2 classes).
            alpha = self.config.learning_rate * (
                math.log((1 - weighted_error) / weighted_error) + math.log(num_classes - 1)
            )
            if alpha <= 0:
                # No better than random guessing for this many classes; stop.
                break

            self.base_learners.append(learner)
            self.learner_weights.append(alpha)

            sample_weights = sample_weights * torch.exp(alpha * incorrect)
            sample_weights = sample_weights / sample_weights.sum()

        if not self.base_learners:
            raise RuntimeError("boosting failed to fit any learner better than chance")

    def _fit_weak_learner(
        self,
        learner: BaseActivityClassifier,
        features: torch.Tensor,
        labels: torch.Tensor,
        sample_weights: torch.Tensor,
    ) -> None:
        optimizer = torch.optim.Adam(learner.parameters(), lr=self.config.inner_learning_rate)
        num_samples = features.shape[0]
        batch_size = min(self.config.inner_batch_size, num_samples)

        learner.train()
        for _ in range(self.config.inner_epochs):
            perm = torch.randperm(num_samples)
            for start in range(0, num_samples, batch_size):
                idx = perm[start : start + batch_size]
                logits = learner(features[idx])
                per_sample_loss = nn.functional.cross_entropy(
                    logits, labels[idx], reduction="none"
                )
                batch_weights = sample_weights[idx]
                loss = torch.sum(per_sample_loss * batch_weights) / batch_weights.sum()

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        learner.eval()

    def predict(self, features: torch.Tensor) -> torch.Tensor:
        if not self.base_learners:
            raise RuntimeError("ensemble has not been fit yet")

        num_classes = self.base_learners[0].config.num_classes
        votes = torch.zeros((features.shape[0], num_classes))

        with torch.no_grad():
            for learner, weight in zip(self.base_learners, self.learner_weights):
                predictions = learner(features).argmax(dim=1)
                votes[torch.arange(features.shape[0]), predictions] += weight

        return votes.argmax(dim=1)
