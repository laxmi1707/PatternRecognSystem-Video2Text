"""AdaBoost, added here rather than in the backend.

The backend registers 14 classifiers and AdaBoost is not one of them. It is
added on this side, following the same `BaseClassifier` contract, so it can be
scored on exactly the same folds as the other 14 without touching `MLService`
or its registry. Any table that includes it has to say so: it is our addition,
not part of the pipeline the team ships.

Worth having in the comparison because AdaBoost is the original boosting scheme
and XGBoost and LightGBM are its regularised successors. Reporting all three
shows that the two modern implementations are chosen on evidence rather than on
being the obvious names.

The backend's `save`/`load` pickle only what a classifier needs to predict
again; the whole estimator is pickled here, so a loaded model is usable - unlike
`tier3/stacking.py:save`, which stores the meta-learner and drops the base
estimators it needs.
"""
from __future__ import annotations

import pickle

import numpy as np

from app.ml.base import BaseClassifier, PredictionResult


class AdaBoostClassifier(BaseClassifier):

    def __init__(self, n_estimators: int = 100, learning_rate: float = 1.0,
                 max_depth: int = 1) -> None:
        from sklearn.ensemble import AdaBoostClassifier as SklearnAda
        from sklearn.tree import DecisionTreeClassifier

        self._n_estimators = n_estimators
        self._learning_rate = learning_rate
        self._max_depth = max_depth
        # A depth-1 stump is AdaBoost's classic weak learner. Depth is exposed
        # because the tuning grid found depth 10 right for the boosted trees on
        # these 150 dimensions, and a stump may well be too weak here too.
        self._model = SklearnAda(
            estimator=DecisionTreeClassifier(max_depth=max_depth, random_state=42),
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            random_state=42,
        )

    @property
    def name(self) -> str:
        return "adaboost"

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
            "learning_rate": self._learning_rate,
            "max_depth": self._max_depth,
        }
