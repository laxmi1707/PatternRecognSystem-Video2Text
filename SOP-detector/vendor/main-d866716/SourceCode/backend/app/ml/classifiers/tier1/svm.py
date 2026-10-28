import pickle

import numpy as np
from sklearn.svm import SVC

from app.ml.base import BaseClassifier, PredictionResult


class SVMClassifier(BaseClassifier):

    def __init__(self, kernel: str = "rbf", C: float = 1.0) -> None:
        self._kernel = kernel
        self._C = C
        self._model = SVC(
            kernel=kernel,
            C=C,
            probability=True,
            random_state=42,
        )

    @property
    def name(self) -> str:
        return "svm"

    @property
    def tier(self) -> str:
        return "tier1"

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._model.fit(X, y)

    def predict(self, X: np.ndarray) -> PredictionResult:
        def _predict(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            labels = self._model.predict(x)
            probas = self._model.predict_proba(x)
            return labels, probas

        return self._timed_predict(_predict, X)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self._model, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            self._model = pickle.load(f)

    def get_params(self) -> dict:
        return {"kernel": self._kernel, "C": self._C}
