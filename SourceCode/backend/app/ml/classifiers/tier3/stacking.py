import io
import pickle

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression

from app.ml.base import BaseClassifier, PredictionResult


class _CpuUnpickler(pickle.Unpickler):
    """Remaps CUDA tensor storage to CPU during pickle deserialization."""
    def find_class(self, module: str, name: str):
        if module == "torch.storage" and name == "_load_from_bytes":
            return lambda b: torch.load(io.BytesIO(b), map_location="cpu", weights_only=False)
        return super().find_class(module, name)


class StackingClassifier(BaseClassifier):

    def __init__(
        self,
        base_estimators: list[BaseClassifier] | None = None,
        meta_C: float = 1.0,
    ) -> None:
        self._base_estimators = base_estimators or []
        self._meta_C = meta_C
        self._meta_learner: LogisticRegression | None = None

    @property
    def name(self) -> str:
        return "stacking"

    @property
    def tier(self) -> str:
        return "tier3"

    def _build_meta_features(self, X: np.ndarray) -> np.ndarray:
        predictions = [est.predict(X) for est in self._base_estimators]
        max_classes = max(p.probabilities.shape[1] for p in predictions)
        padded = []
        for p in predictions:
            proba = p.probabilities
            if proba.shape[1] < max_classes:
                pad = np.zeros((proba.shape[0], max_classes - proba.shape[1]))
                proba = np.concatenate([proba, pad], axis=1)
            padded.append(proba)
        return np.hstack(padded)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        for est in self._base_estimators:
            est.fit(X, y)

        meta_X = self._build_meta_features(X)
        self._meta_learner = LogisticRegression(
            C=self._meta_C,
            max_iter=1000,
            random_state=42,
        )
        self._meta_learner.fit(meta_X, y)

    def predict(self, X: np.ndarray) -> PredictionResult:
        def _predict(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            meta_X = self._build_meta_features(x)
            labels = self._meta_learner.predict(meta_X)
            probas = self._meta_learner.predict_proba(meta_X)
            return labels, probas

        return self._timed_predict(_predict, X)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump({"meta_learner": self._meta_learner, "base_estimators": self._base_estimators}, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            data = _CpuUnpickler(f).load()
        self._meta_learner = data["meta_learner"]
        self._base_estimators = data["base_estimators"]

    def get_params(self) -> dict:
        return {
            "meta_C": self._meta_C,
            "n_base_estimators": len(self._base_estimators),
            "base_names": [e.name for e in self._base_estimators],
        }
