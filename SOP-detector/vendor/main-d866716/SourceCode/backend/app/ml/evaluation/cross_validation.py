from dataclasses import dataclass, field

import numpy as np
from sklearn.model_selection import StratifiedKFold

from app.ml.base import BaseClassifier
from app.ml.config import MLConfig
from app.ml.evaluation.metrics import ModelMetrics, compute_metrics


@dataclass(frozen=True)
class CVResult:
    model_name: str
    tier: str
    n_folds: int
    fold_metrics: tuple[ModelMetrics, ...]
    mean_accuracy: float
    std_accuracy: float
    mean_f1: float
    std_f1: float
    mean_auc: float
    std_auc: float
    mean_latency_ms: float


def cross_validate(
    classifier: BaseClassifier,
    X: np.ndarray,
    y: np.ndarray,
    config: MLConfig | None = None,
) -> CVResult:
    config = config or MLConfig()
    skf = StratifiedKFold(
        n_splits=config.cv_folds,
        shuffle=True,
        random_state=config.seed,
    )

    fold_metrics: list[ModelMetrics] = []

    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        classifier.fit(X_train, y_train)
        result = classifier.predict(X_val)

        metrics = compute_metrics(
            model_name=classifier.name,
            tier=classifier.tier,
            y_true=y_val,
            y_pred=result.labels,
            y_proba=result.probabilities,
            latency_ms=result.latency_ms,
            num_classes=config.num_classes,
        )
        fold_metrics.append(metrics)

    accuracies = np.array([m.accuracy for m in fold_metrics])
    f1s = np.array([m.f1_macro for m in fold_metrics])
    aucs = np.array([m.auc_macro for m in fold_metrics])
    latencies = np.array([m.latency_ms for m in fold_metrics])

    return CVResult(
        model_name=classifier.name,
        tier=classifier.tier,
        n_folds=config.cv_folds,
        fold_metrics=tuple(fold_metrics),
        mean_accuracy=float(accuracies.mean()),
        std_accuracy=float(accuracies.std()),
        mean_f1=float(f1s.mean()),
        std_f1=float(f1s.std()),
        mean_auc=float(aucs.mean()),
        std_auc=float(aucs.std()),
        mean_latency_ms=float(latencies.mean()),
    )


def print_cv_results(results: list[CVResult]) -> None:
    header = (
        f"{'Model':<20} {'Tier':<8} {'Acc (mean±std)':<18} "
        f"{'F1 (mean±std)':<18} {'AUC (mean±std)':<18} {'ms':>8}"
    )
    print(header)
    print("-" * len(header))
    for r in sorted(results, key=lambda x: x.mean_f1, reverse=True):
        print(
            f"{r.model_name:<20} {r.tier:<8} "
            f"{r.mean_accuracy:.3f} ± {r.std_accuracy:.3f}   "
            f"{r.mean_f1:.3f} ± {r.std_f1:.3f}   "
            f"{r.mean_auc:.3f} ± {r.std_auc:.3f}   "
            f"{r.mean_latency_ms:>8.2f}"
        )
