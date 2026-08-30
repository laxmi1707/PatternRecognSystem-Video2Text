import pickle

import numpy as np
from sklearn.naive_bayes import GaussianNB

from app.ml.base import BaseClassifier, PredictionResult


class NaiveBayesClassifier(BaseClassifier):

    def __init__(self) -> None:
        self._model = GaussianNB()

    @property
    def name(self) -> str:
        return "naive_bayes"

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
