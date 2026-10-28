from __future__ import annotations

import logging

import numpy as np

from app.ml.base import BaseClassifier
from app.ml.config import MLConfig, ACTIVITY_LABELS
from app.ml.registry import ModelRegistry
from app.ml.dataset import (
    generate_synthetic_dataset,
    load_real_dataset,
    train_test_split_data,
)
from app.ml.evaluation.report import ReportGenerator, EvaluationReport
from app.ml.evaluation.cross_validation import CVResult, cross_validate

from app.ml.classifiers.tier1.svm import SVMClassifier
from app.ml.classifiers.tier1.naive_bayes import NaiveBayesClassifier
from app.ml.classifiers.tier1.decision_tree import DecisionTreeClassifier
from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
from app.ml.classifiers.tier1.knn import KNNClassifier
from app.ml.classifiers.tier1.xgboost_clf import XGBoostClassifier
from app.ml.classifiers.tier1.lightgbm_clf import LightGBMClassifier
from app.ml.classifiers.tier2 import MLPClassifier, CNN1DClassifier, LSTMClassifier, TransformerClassifier
from app.ml.classifiers.tier3 import VotingClassifier, StackingClassifier, LateFusionClassifier

logger = logging.getLogger(__name__)


class MLService:

    def __init__(self) -> None:
        self._config = MLConfig()
        self._registry = ModelRegistry()
        self._trained_models: set[str] = set()
        self._synth_data: tuple[np.ndarray, np.ndarray] | None = None
        self._real_data: tuple[np.ndarray, np.ndarray] | None = None
        self._register_all()

    def _register_all(self) -> None:
        tier1 = [
            SVMClassifier(),
            NaiveBayesClassifier(),
            DecisionTreeClassifier(),
            RandomForestClassifier(),
            KNNClassifier(),
            XGBoostClassifier(),
            LightGBMClassifier(),
        ]
        tier2 = [
            MLPClassifier(),
            CNN1DClassifier(),
            LSTMClassifier(),
            TransformerClassifier(),
        ]
        for clf in tier1 + tier2:
            self._registry.register(clf)

        self._registry.register(VotingClassifier(
            estimators=[SVMClassifier(), RandomForestClassifier(), MLPClassifier()],
            voting="soft",
        ))
        self._registry.register(StackingClassifier(
            base_estimators=[SVMClassifier(), RandomForestClassifier(), MLPClassifier()],
        ))
        self._registry.register(LateFusionClassifier(
            branches=[SVMClassifier(), RandomForestClassifier()],
        ))

    def _get_synth_data(
        self, n_samples: int = 500, n_features: int | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        n_features = n_features or self._config.n_features
        if self._synth_data is None or self._synth_data[0].shape[1] != n_features:
            self._synth_data = generate_synthetic_dataset(
                n_samples=n_samples, n_features=n_features, config=self._config,
            )
        return self._synth_data

    def _get_real_data(self) -> tuple[np.ndarray, np.ndarray]:
        if self._real_data is None:
            logger.info("Loading real CUA-Suite dataset...")
            self._real_data = load_real_dataset(config=self._config)
        return self._real_data

    def _get_training_data(self, prefer_real: bool = False) -> tuple[np.ndarray, np.ndarray]:
        if not prefer_real:
            return self._get_synth_data()
        try:
            return self._get_real_data()
        except Exception as e:
            logger.warning(f"Failed to load real dataset, falling back to synthetic: {e}")
            return self._get_synth_data()

    def _ensure_trained(self, model_name: str) -> None:
        if model_name not in self._trained_models:
            X, y = self._get_training_data(prefer_real=True)
            self._registry.get(model_name).fit(X, y)
            self._trained_models.add(model_name)

    def train_all(self, X: np.ndarray, y: np.ndarray) -> None:
        for clf in self._registry.all():
            clf.fit(X, y)
            self._trained_models.add(clf.name)

    def train_synthetic(self, n_samples: int = 500, n_features: int | None = None) -> None:
        X, y = self._get_synth_data(n_samples, n_features)
        self.train_all(X, y)

    def get_model(self, name: str) -> BaseClassifier:
        return self._registry.get(name)

    def list_models(self) -> list[str]:
        return self._registry.names()

    def list_by_tier(self, tier: str) -> list[str]:
        return [m.name for m in self._registry.list_by_tier(tier)]

    def classify(self, features: np.ndarray, model_name: str | None = None) -> dict:
        name = model_name or "svm"
        self._ensure_trained(name)

        clf = self._registry.get(name)
        result = clf.predict(features)

        predictions = []
        for i in range(len(result.labels)):
            label_idx = int(result.labels[i])
            probas = result.probabilities[i]
            predictions.append({
                "label": ACTIVITY_LABELS[label_idx],
                "confidence": float(probas[label_idx]),
                "probabilities": {
                    ACTIVITY_LABELS[j]: float(probas[j])
                    for j in range(len(ACTIVITY_LABELS))
                },
                "model_name": clf.name,
                "latency_ms": result.latency_ms,
            })
        return {"results": predictions, "model_name": clf.name, "latency_ms": result.latency_ms}

    def run_evaluation(
        self, n_samples: int = 500, n_features: int | None = None, use_real: bool = True,
    ) -> EvaluationReport:
        if use_real:
            X, y = self._get_training_data()
        else:
            X, y = generate_synthetic_dataset(
                n_samples=n_samples,
                n_features=n_features or self._config.n_features,
                config=self._config,
            )
        X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=self._config)

        generator = ReportGenerator(classifiers=self._registry.all(), config=self._config)
        return generator.run(X_train, y_train, X_test, y_test)

    def run_cross_validation(
        self,
        n_samples: int = 500,
        n_features: int | None = None,
        model_names: list[str] | None = None,
        use_real: bool = True,
    ) -> list[CVResult]:
        if use_real:
            X, y = self._get_training_data()
        else:
            X, y = generate_synthetic_dataset(
                n_samples=n_samples,
                n_features=n_features or self._config.n_features,
                config=self._config,
            )

        if model_names:
            classifiers = [self._registry.get(name) for name in model_names]
        else:
            classifiers = self._registry.all()

        return [cross_validate(clf, X, y, config=self._config) for clf in classifiers]


ml_service = MLService()
