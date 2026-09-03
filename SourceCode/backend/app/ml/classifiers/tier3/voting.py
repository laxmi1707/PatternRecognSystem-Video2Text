import pickle

import numpy as np

from app.ml.base import BaseClassifier, PredictionResult


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
            all_probas = np.array([est.predict(x).probabilities for est in self._estimators])

            if self._voting == "soft":
                avg_probas = np.mean(all_probas, axis=0)
            else:
                all_labels = np.array([np.argmax(p, axis=1) for p in all_probas])
                num_classes = all_probas.shape[2]
                avg_probas = np.zeros((x.shape[0], num_classes))
                for i in range(x.shape[0]):
                    for label in all_labels[:, i]:
                        avg_probas[i, label] += 1.0
                avg_probas /= len(self._estimators)

            labels = np.argmax(avg_probas, axis=1)
            return labels, avg_probas

        return self._timed_predict(_predict, X)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump({"voting": self._voting, "estimator_names": [e.name for e in self._estimators]}, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            pickle.load(f)

    def get_params(self) -> dict:
        return {
            "voting": self._voting,
            "n_estimators": len(self._estimators),
            "estimator_names": [e.name for e in self._estimators],
        }
