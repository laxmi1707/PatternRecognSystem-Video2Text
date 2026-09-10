import pickle

import numpy as np
from lightgbm import LGBMClassifier

from app.ml.base import BaseClassifier, PredictionResult


class LightGBMClassifier(BaseClassifier):

    def __init__(self, n_estimators: int = 100, max_depth: int = 6, learning_rate: float = 0.1) -> None:
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._learning_rate = learning_rate
        self._model = LGBMClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42,
            verbosity=-1,
        )

    @property
    def name(self) -> str:
        return "lightgbm"

    @property
    def tier(self) -> str:
        return "tier1"

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._model.fit(X, y)

    def predict(self, X: np.ndarray) -> PredictionResult:
        def _predict(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            return self._model.predict(x), self._model.predict_proba(x)
        return self._timed_predict(_predict, X)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self._model, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            self._model = pickle.load(f)

    def get_params(self) -> dict:
        return {
            "n_estimators": self._n_estimators,
            "max_depth": self._max_depth,
            "learning_rate": self._learning_rate,
        }
