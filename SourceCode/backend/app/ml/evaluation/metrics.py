from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass(frozen=True)
class ModelMetrics:
    model_name: str
    tier: str
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    auc_macro: float
    latency_ms: float
    f1_per_class: np.ndarray
    auc_per_class: np.ndarray


def compute_metrics(
    model_name: str,
    tier: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
    latency_ms: float,
    num_classes: int = 10,
) -> ModelMetrics:
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average="macro", zero_division=0)
    recall = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)

    try:
        auc_macro = roc_auc_score(
            y_true, y_proba, multi_class="ovr", average="macro",
        )
        auc_per_class = np.array([
            roc_auc_score((y_true == i).astype(int), y_proba[:, i])
            for i in range(num_classes)
            if np.sum(y_true == i) > 0
        ])
    except ValueError:
        auc_macro = 0.0
        auc_per_class = np.zeros(num_classes)

    return ModelMetrics(
        model_name=model_name,
        tier=tier,
        accuracy=accuracy,
        precision_macro=precision,
        recall_macro=recall,
        f1_macro=f1_macro,
        auc_macro=auc_macro,
        latency_ms=latency_ms,
        f1_per_class=f1_per_class,
        auc_per_class=auc_per_class,
    )
