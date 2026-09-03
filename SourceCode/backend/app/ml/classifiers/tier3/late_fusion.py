import pickle

import numpy as np
from sklearn.linear_model import LogisticRegression

from app.ml.base import BaseClassifier, PredictionResult


class LateFusionClassifier(BaseClassifier):
    """Multimodal late fusion: each modality branch has its own classifier,
    a meta-learner fuses their probability outputs.

    In production each branch receives a different feature subset (OCR, UI,
    cursor, scene). During development with a single feature matrix, we
    split the columns evenly across branches to simulate multimodal fusion.
    """

    def __init__(
        self,
        branches: list[BaseClassifier] | None = None,
        meta_C: float = 1.0,
    ) -> None:
        self._branches = branches or []
        self._meta_C = meta_C
        self._meta_learner: LogisticRegression | None = None
        self._split_indices: list[tuple[int, int]] | None = None

    @property
    def name(self) -> str:
        return "late_fusion"

    @property
    def tier(self) -> str:
        return "tier3"

    def _compute_splits(self, n_features: int) -> list[tuple[int, int]]:
        n = len(self._branches)
        chunk = n_features // n
        splits = []
        for i in range(n):
            start = i * chunk
            end = n_features if i == n - 1 else (i + 1) * chunk
            splits.append((start, end))
        return splits

    def _branch_predict(self, X: np.ndarray) -> np.ndarray:
        probas = []
        for branch, (start, end) in zip(self._branches, self._split_indices):
            result = branch.predict(X[:, start:end])
            probas.append(result.probabilities)
        return np.hstack(probas)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._split_indices = self._compute_splits(X.shape[1])

        for branch, (start, end) in zip(self._branches, self._split_indices):
            branch.fit(X[:, start:end], y)

        meta_X = self._branch_predict(X)
        self._meta_learner = LogisticRegression(
            C=self._meta_C,
            max_iter=1000,
            random_state=42,
        )
        self._meta_learner.fit(meta_X, y)

    def predict(self, X: np.ndarray) -> PredictionResult:
        def _predict(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            meta_X = self._branch_predict(x)
            labels = self._meta_learner.predict(meta_X)
            probas = self._meta_learner.predict_proba(meta_X)
            return labels, probas

        return self._timed_predict(_predict, X)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump({
                "meta_learner": self._meta_learner,
                "split_indices": self._split_indices,
            }, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            data = pickle.load(f)
        self._meta_learner = data["meta_learner"]
        self._split_indices = data["split_indices"]

    def get_params(self) -> dict:
        return {
            "meta_C": self._meta_C,
            "n_branches": len(self._branches),
            "branch_names": [b.name for b in self._branches],
            "split_indices": self._split_indices,
        }
