import pickle

import numpy as np
from sklearn.linear_model import LogisticRegression

from app.ml.base import BaseClassifier, PredictionResult


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
        probas = [est.predict(X).probabilities for est in self._base_estimators]
        return np.hstack(probas)

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
            pickle.dump(self._meta_learner, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            self._meta_learner = pickle.load(f)

    def get_params(self) -> dict:
        return {
            "meta_C": self._meta_C,
            "n_base_estimators": len(self._base_estimators),
            "base_names": [e.name for e in self._base_estimators],
        }
