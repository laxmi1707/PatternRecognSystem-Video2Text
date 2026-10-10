import io
import pickle

import numpy as np
import torch

from app.ml.base import BaseClassifier, PredictionResult


class _CpuUnpickler(pickle.Unpickler):
    """Remaps CUDA tensor storage to CPU during pickle deserialization."""
    def find_class(self, module: str, name: str):
        if module == "torch.storage" and name == "_load_from_bytes":
            return lambda b: torch.load(io.BytesIO(b), map_location="cpu", weights_only=False)
        return super().find_class(module, name)


class VotingClassifier(BaseClassifier):

    def __init__(
        self,
        estimators: list[BaseClassifier] | None = None,
        voting: str = "soft",
    ) -> None:
        self._estimators = estimators or []
        self._voting = voting

    @property
    def name(self) -> str:
        return "voting"

    @property
    def tier(self) -> str:
        return "tier3"

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        for est in self._estimators:
            est.fit(X, y)

    def predict(self, X: np.ndarray) -> PredictionResult:
        def _predict(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            predictions = [est.predict(x) for est in self._estimators]
            max_classes = max(p.probabilities.shape[1] for p in predictions)
            n_samples = x.shape[0]

            padded = []
            for p in predictions:
                proba = p.probabilities
                if proba.shape[1] < max_classes:
                    pad = np.zeros((n_samples, max_classes - proba.shape[1]))
                    proba = np.concatenate([proba, pad], axis=1)
                padded.append(proba)

            all_probas = np.stack(padded, axis=0)

            if self._voting == "soft":
                avg_probas = np.mean(all_probas, axis=0)
            else:
                all_labels = np.argmax(all_probas, axis=2)
                avg_probas = np.zeros((n_samples, max_classes))
                for i in range(n_samples):
                    for label in all_labels[:, i]:
                        avg_probas[i, label] += 1.0
                avg_probas /= len(self._estimators)

            labels = np.argmax(avg_probas, axis=1)
            return labels, avg_probas

        return self._timed_predict(_predict, X)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump({"voting": self._voting, "estimators": self._estimators}, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            data = _CpuUnpickler(f).load()
        self._voting = data["voting"]
        self._estimators = data["estimators"]

    def get_params(self) -> dict:
        return {
            "voting": self._voting,
            "n_estimators": len(self._estimators),
            "estimator_names": [e.name for e in self._estimators],
        }
