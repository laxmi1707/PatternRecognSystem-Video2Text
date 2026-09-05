from dataclasses import dataclass

import numpy as np
from sklearn.metrics import roc_curve, auc


@dataclass(frozen=True)
class ROCCurveResult:
    model_name: str
    fpr: dict[int, np.ndarray]
    tpr: dict[int, np.ndarray]
    auc_scores: dict[int, float]
    labels: list[str]


def compute_roc_curves(
    model_name: str,
    y_true: np.ndarray,
    y_proba: np.ndarray,
    labels: list[str],
) -> ROCCurveResult:
    num_classes = len(labels)
    fpr = {}
    tpr = {}
    auc_scores = {}

    for i in range(num_classes):
        if np.sum(y_true == i) == 0:
            continue
        binary_true = (y_true == i).astype(int)
        fpr[i], tpr[i], _ = roc_curve(binary_true, y_proba[:, i])
        auc_scores[i] = auc(fpr[i], tpr[i])

    return ROCCurveResult(
        model_name=model_name,
        fpr=fpr,
        tpr=tpr,
        auc_scores=auc_scores,
        labels=labels,
    )
