from dataclasses import dataclass

import numpy as np

from app.ml.base import BaseClassifier
from app.ml.evaluation.metrics import ModelMetrics, compute_metrics


@dataclass(frozen=True)
class AblationResult:
    model_name: str
    baseline_f1: float
    ablations: tuple["ModalityAblation", ...]


@dataclass(frozen=True)
class ModalityAblation:
    modality_name: str
    feature_range: tuple[int, int]
    f1_without: float
    f1_drop: float
    drop_pct: float


def run_ablation_study(
    classifier: BaseClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    modality_map: dict[str, tuple[int, int]] | None = None,
    num_classes: int = 10,
) -> AblationResult:
    """Remove each modality (feature group) and measure F1 drop.

    modality_map: {"ocr_text": (0, 15), "ui_labels": (15, 30), "cursor": (30, 40), "scene": (40, 50)}
    If None, splits features into 5 equal groups to simulate modalities.
    """
    if modality_map is None:
        n_features = X_train.shape[1]
        chunk = n_features // 5
        modality_map = {
            "modality_A": (0, chunk),
            "modality_B": (chunk, 2 * chunk),
            "modality_C": (2 * chunk, 3 * chunk),
            "modality_D": (3 * chunk, 4 * chunk),
            "modality_E": (4 * chunk, n_features),
        }

    classifier.fit(X_train, y_train)
    baseline = classifier.predict(X_test)
    baseline_metrics = compute_metrics(
        model_name=classifier.name, tier=classifier.tier,
        y_true=y_test, y_pred=baseline.labels, y_proba=baseline.probabilities,
        latency_ms=baseline.latency_ms, num_classes=num_classes,
    )
    baseline_f1 = baseline_metrics.f1_macro

    ablations: list[ModalityAblation] = []
    for name, (start, end) in modality_map.items():
        X_train_ablated = X_train.copy()
        X_test_ablated = X_test.copy()
        X_train_ablated[:, start:end] = 0.0
        X_test_ablated[:, start:end] = 0.0

        classifier.fit(X_train_ablated, y_train)
        result = classifier.predict(X_test_ablated)
        metrics = compute_metrics(
            model_name=classifier.name, tier=classifier.tier,
            y_true=y_test, y_pred=result.labels, y_proba=result.probabilities,
            latency_ms=result.latency_ms, num_classes=num_classes,
        )

        f1_drop = baseline_f1 - metrics.f1_macro
        drop_pct = (f1_drop / baseline_f1 * 100) if baseline_f1 > 0 else 0.0

        ablations.append(ModalityAblation(
            modality_name=name,
            feature_range=(start, end),
            f1_without=metrics.f1_macro,
            f1_drop=f1_drop,
            drop_pct=drop_pct,
        ))

    ablations.sort(key=lambda a: a.f1_drop, reverse=True)

    return AblationResult(
        model_name=classifier.name,
        baseline_f1=baseline_f1,
        ablations=tuple(ablations),
    )


def print_ablation_results(result: AblationResult) -> None:
    print(f"\nAblation Study for {result.model_name} (baseline F1: {result.baseline_f1:.3f}):")
    print(f"{'Modality':<15} {'F1 without':<12} {'F1 drop':<10} {'Drop %':<8}")
    print("-" * 45)
    for a in result.ablations:
        print(f"{a.modality_name:<15} {a.f1_without:<12.3f} {a.f1_drop:<10.3f} {a.drop_pct:<8.1f}")
