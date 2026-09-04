from dataclasses import dataclass

import numpy as np

from app.ml.base import BaseClassifier


@dataclass(frozen=True)
class MisclassificationCase:
    sample_index: int
    true_label: int
    true_name: str
    predicted_label: int
    predicted_name: str
    confidence: float
    true_class_prob: float


@dataclass(frozen=True)
class ConfusionPair:
    class_a: str
    class_b: str
    a_as_b: int
    b_as_a: int
    total: int


@dataclass(frozen=True)
class ErrorAnalysisResult:
    model_name: str
    total_samples: int
    total_errors: int
    error_rate: float
    worst_misclassifications: tuple[MisclassificationCase, ...]
    most_confused_pairs: tuple[ConfusionPair, ...]
    per_class_error_rate: dict[str, float]


def run_error_analysis(
    classifier: BaseClassifier,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_names: list[str] | tuple[str, ...],
    top_k_worst: int = 10,
    top_k_pairs: int = 5,
) -> ErrorAnalysisResult:
    result = classifier.predict(X_test)
    y_pred = result.labels
    probas = result.probabilities

    wrong_mask = y_pred != y_test
    wrong_indices = np.where(wrong_mask)[0]

    misclassifications = []
    for idx in wrong_indices:
        true_label = int(y_test[idx])
        pred_label = int(y_pred[idx])
        misclassifications.append(MisclassificationCase(
            sample_index=int(idx),
            true_label=true_label,
            true_name=label_names[true_label],
            predicted_label=pred_label,
            predicted_name=label_names[pred_label],
            confidence=float(probas[idx, pred_label]),
            true_class_prob=float(probas[idx, true_label]),
        ))

    misclassifications.sort(key=lambda m: m.confidence, reverse=True)

    num_classes = len(label_names)
    confusion_pairs: list[ConfusionPair] = []
    for i in range(num_classes):
        for j in range(i + 1, num_classes):
            a_as_b = int(np.sum((y_test == i) & (y_pred == j)))
            b_as_a = int(np.sum((y_test == j) & (y_pred == i)))
            total = a_as_b + b_as_a
            if total > 0:
                confusion_pairs.append(ConfusionPair(
                    class_a=label_names[i],
                    class_b=label_names[j],
                    a_as_b=a_as_b,
                    b_as_a=b_as_a,
                    total=total,
                ))
    confusion_pairs.sort(key=lambda p: p.total, reverse=True)

    per_class_error: dict[str, float] = {}
    for i, name in enumerate(label_names):
        class_mask = y_test == i
        if class_mask.sum() > 0:
            per_class_error[name] = float(np.mean(y_pred[class_mask] != i))
        else:
            per_class_error[name] = 0.0

    return ErrorAnalysisResult(
        model_name=classifier.name,
        total_samples=len(y_test),
        total_errors=len(wrong_indices),
        error_rate=float(len(wrong_indices) / len(y_test)),
        worst_misclassifications=tuple(misclassifications[:top_k_worst]),
        most_confused_pairs=tuple(confusion_pairs[:top_k_pairs]),
        per_class_error_rate=per_class_error,
    )


def print_error_analysis(result: ErrorAnalysisResult) -> None:
    print(f"\nError Analysis for {result.model_name}:")
    print(f"  Total: {result.total_samples}  Errors: {result.total_errors}  Rate: {result.error_rate:.1%}")

    if result.most_confused_pairs:
        print(f"\n  Most confused class pairs:")
        for p in result.most_confused_pairs:
            print(f"    {p.class_a} <-> {p.class_b}: {p.total} errors ({p.a_as_b} + {p.b_as_a})")

    if result.worst_misclassifications:
        print(f"\n  Highest-confidence misclassifications:")
        for m in result.worst_misclassifications[:5]:
            print(
                f"    Sample {m.sample_index}: {m.true_name} -> {m.predicted_name} "
                f"(conf={m.confidence:.2f}, true_prob={m.true_class_prob:.2f})"
            )

    print(f"\n  Per-class error rate:")
    for name, rate in sorted(result.per_class_error_rate.items(), key=lambda x: x[1], reverse=True):
        bar = "#" * int(rate * 50)
        print(f"    {name:<20} {rate:.1%} {bar}")
