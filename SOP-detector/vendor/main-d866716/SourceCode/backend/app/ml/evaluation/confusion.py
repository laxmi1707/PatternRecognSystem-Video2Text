from dataclasses import dataclass

import numpy as np
from sklearn.metrics import confusion_matrix


@dataclass(frozen=True)
class ConfusionMatrixResult:
    matrix: np.ndarray
    labels: list[str]
    model_name: str


def compute_confusion_matrix(
    model_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: list[str],
) -> ConfusionMatrixResult:
    num_classes = len(labels)
    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=list(range(num_classes)),
    )
    return ConfusionMatrixResult(
        matrix=cm,
        labels=labels,
        model_name=model_name,
    )
