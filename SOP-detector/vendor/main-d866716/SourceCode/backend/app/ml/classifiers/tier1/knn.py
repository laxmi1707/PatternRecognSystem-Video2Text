import pickle

import numpy as np
from sklearn.neighbors import KNeighborsClassifier

from app.ml.base import BaseClassifier, PredictionResult


class KNNClassifier(BaseClassifier):

    def __init__(self, n_neighbors: int = 5) -> None:
        self._n_neighbors = n_neighbors
        self._model = KNeighborsClassifier(
            n_neighbors=n_neighbors,
            n_jobs=-1,
        )

    @property
    def name(self) -> str:
        return "knn"

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
        return {"n_neighbors": self._n_neighbors}
