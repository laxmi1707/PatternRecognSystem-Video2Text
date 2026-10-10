from __future__ import annotations

import logging
from pathlib import Path

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

logger = logging.getLogger(__name__)


class MLService:

    def __init__(self) -> None:
        self._config = MLConfig()
        self._registry = ModelRegistry()
        self._trained_models: set[str] = set()
        self._synth_data: tuple[np.ndarray, np.ndarray] | None = None
        self._real_data: tuple[np.ndarray, np.ndarray] | None = None
        self._register_all()
        self._try_load_models()

    def _register_all(self) -> None:
        from app.ml.classifiers.tier2 import MLPClassifier, CNN1DClassifier, LSTMClassifier, TransformerClassifier
        from app.ml.classifiers.tier2.workflow_lstm import WorkflowLSTMClassifier
        from app.ml.classifiers.tier2.workflow_transformer import WorkflowTransformerClassifier
        from app.ml.classifiers.tier3 import VotingClassifier, StackingClassifier, LateFusionClassifier

        nc = self._config.num_classes
        nf = self._config.n_features

        mlp = MLPClassifier(num_classes=nc)
        rf = RandomForestClassifier()
        svm = SVMClassifier()

        for clf in [
            # ── Level 2: Activity Recognition ─────────────────────────────────────
            # Classifies WHAT task is happening (coding, git, docker, aws, etc.)
            # from multimodal features: video frames + OCR + YOLO UI detection +
            # Level 1 interaction evidence (click/keyboard/drag from action log).
            #
            # Tier 1 — Classical ML baselines (RQ1: classical vs deep learning)
            svm, NaiveBayesClassifier(), DecisionTreeClassifier(), rf,
            KNNClassifier(), XGBoostClassifier(), LightGBMClassifier(),
            # Tier 2 — Deep learning (RQ1: classical vs deep learning)
            mlp, CNN1DClassifier(num_classes=nc), LSTMClassifier(num_classes=nc), TransformerClassifier(num_classes=nc),
            # Tier 3 — Ensemble / multimodal fusion (RQ2: fusion vs individual modalities)
            VotingClassifier(estimators=[SVMClassifier(), RandomForestClassifier(), MLPClassifier(num_classes=nc)], voting="soft"),
            StackingClassifier(base_estimators=[SVMClassifier(), RandomForestClassifier(), MLPClassifier(num_classes=nc)]),
            LateFusionClassifier(branches=[SVMClassifier(), RandomForestClassifier()]),
            #
            # ── Level 3: Workflow Recognition ─────────────────────────────────────
            # Recognises SEQUENCES of Level 2 activity predictions to identify
            # higher-order workflows (e.g. "clone → edit → commit → push" = git workflow).
            # Input: temporal sequence of Level 2 predictions, not raw video features.
            # (RQ3: temporal sequence models for workflow pattern recognition)
            WorkflowLSTMClassifier(num_classes=nc, feature_dim=nf),
            WorkflowTransformerClassifier(num_classes=nc, feature_dim=nf),
        ]:
            self._registry.register(clf)

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

    def save_models(self, model_dir: str | None = None) -> None:
        d = Path(model_dir or self._config.model_dir)
        d.mkdir(parents=True, exist_ok=True)
        for clf in self._registry.all():
            if clf.name in self._trained_models:
                path = str(d / f"{clf.name}.pkl")
                clf.save(path)
                logger.info(f"Saved {clf.name} → {path}")

    def load_models(self, model_dir: str | None = None) -> int:
        d = Path(model_dir or self._config.model_dir)
        if not d.exists():
            return 0
        loaded = 0
        for clf in self._registry.all():
            path = d / f"{clf.name}.pkl"
            if path.exists():
                try:
                    clf.load(str(path))
                    self._trained_models.add(clf.name)
                    loaded += 1
                except Exception as e:
                    logger.warning(f"Failed to load {clf.name}: {e}")
        return loaded

    def _try_load_models(self) -> None:
        n = self.load_models()
        if n > 0:
            logger.info(f"Loaded {n} pre-trained models from {self._config.model_dir}")

    def train_synthetic(self, n_samples: int = 500, n_features: int | None = None) -> None:
        X, y = self._get_synth_data(n_samples, n_features)
        self.train_all(X, y)

    def get_model(self, name: str) -> BaseClassifier:
        return self._registry.get(name)

    def list_models(self) -> list[str]:
        return self._registry.names()

    def list_by_tier(self, tier: str) -> list[str]:
        return [m.name for m in self._registry.list_by_tier(tier)]

    def get_model_tier(self, name: str) -> str:
        return self._registry.get(name).tier

    def classify(self, features: np.ndarray, model_name: str | None = None) -> dict:
        name = model_name or "svm"
        self._ensure_trained(name)

        clf = self._registry.get(name)
        result = clf.predict(features)

        n_classes = result.probabilities.shape[1] if result.probabilities.ndim > 1 else len(ACTIVITY_LABELS)
        labels_for_model = [l for l in ACTIVITY_LABELS if l != "terraform_iac"][:n_classes] if n_classes < len(ACTIVITY_LABELS) else ACTIVITY_LABELS

        predictions = []
        for i in range(len(result.labels)):
            label_idx = int(result.labels[i])
            probas = result.probabilities[i]
            label_idx = min(label_idx, len(labels_for_model) - 1)
            predictions.append({
                "label": labels_for_model[label_idx],
                "confidence": float(probas[min(label_idx, len(probas) - 1)]),
                "probabilities": {
                    labels_for_model[j]: float(probas[j])
                    for j in range(min(len(labels_for_model), len(probas)))
                },
                "model_name": clf.name,
                "latency_ms": result.latency_ms,
            })
        return {"results": predictions, "model_name": clf.name, "latency_ms": result.latency_ms}

    def get_recommended_model(self) -> dict | None:
        return getattr(self, '_cached_recommendation', None)

    def _update_recommendation(self, report: EvaluationReport) -> None:
        if not report.comparison_table:
            return
        best = report.comparison_table[0]
        self._cached_recommendation = {
            "model_name": best.model_name,
            "f1_macro": round(best.f1_macro, 4),
            "accuracy": round(best.accuracy, 4),
            "latency_ms": round(best.latency_ms, 2),
            "reason": (
                f"Highest F1 score ({best.f1_macro:.2f}) "
                f"with {best.accuracy:.0%} accuracy "
                f"and {best.latency_ms:.0f}ms latency"
            ),
        }

    def run_evaluation(
        self, n_samples: int = 500, n_features: int | None = None, use_real: bool = True,
    ) -> EvaluationReport:
        if use_real:
            X, y = self._get_training_data(prefer_real=True)
        else:
            X, y = generate_synthetic_dataset(
                n_samples=n_samples,
                n_features=n_features or self._config.n_features,
                config=self._config,
            )
        X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=self._config)

        generator = ReportGenerator(classifiers=self._registry.all(), config=self._config)
        report = generator.run(X_train, y_train, X_test, y_test)
        self._update_recommendation(report)
        return report

    def run_cross_validation(
        self,
        n_samples: int = 500,
        n_features: int | None = None,
        model_names: list[str] | None = None,
        use_real: bool = True,
    ) -> list[CVResult]:
        if use_real:
            X, y = self._get_training_data(prefer_real=True)
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
