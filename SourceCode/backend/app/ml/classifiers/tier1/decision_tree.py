import pickle

import numpy as np
from sklearn.tree import DecisionTreeClassifier as SklearnDT

from app.ml.base import BaseClassifier, PredictionResult


class DecisionTreeClassifier(BaseClassifier):

    def __init__(self, max_depth: int = 20) -> None:
        self._max_depth = max_depth
        self._model = SklearnDT(
            max_depth=max_depth,
            random_state=42,
        )

    @property
    def name(self) -> str:
        return "decision_tree"

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
        return {"max_depth": self._max_depth}
