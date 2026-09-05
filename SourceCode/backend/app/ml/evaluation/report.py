from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.ml.base import BaseClassifier
from app.ml.config import MLConfig
from app.ml.evaluation.metrics import ModelMetrics, compute_metrics
from app.ml.evaluation.confusion import ConfusionMatrixResult, compute_confusion_matrix
from app.ml.evaluation.roc_curves import ROCCurveResult, compute_roc_curves

import numpy as np


@dataclass
class EvaluationReport:
    comparison_table: list[ModelMetrics] = field(default_factory=list)
    confusion_matrices: dict[str, ConfusionMatrixResult] = field(default_factory=dict)
    roc_curves: dict[str, ROCCurveResult] = field(default_factory=dict)
    generated_at: str = ""


class ReportGenerator:

    def __init__(
        self,
        classifiers: list[BaseClassifier],
        config: MLConfig | None = None,
    ) -> None:
        self.classifiers = classifiers
        self.config = config or MLConfig()

    def run(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> EvaluationReport:
        report = EvaluationReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        labels = list(self.config.labels)

        for clf in self.classifiers:
            clf.fit(X_train, y_train)
            result = clf.predict(X_test)

            metrics = compute_metrics(
                model_name=clf.name,
                tier=clf.tier,
                y_true=y_test,
                y_pred=result.labels,
                y_proba=result.probabilities,
                latency_ms=result.latency_ms,
                num_classes=self.config.num_classes,
            )
            report.comparison_table.append(metrics)

            cm = compute_confusion_matrix(
                model_name=clf.name,
                y_true=y_test,
                y_pred=result.labels,
                labels=labels,
            )
            report.confusion_matrices[clf.name] = cm

            roc = compute_roc_curves(
                model_name=clf.name,
                y_true=y_test,
                y_proba=result.probabilities,
                labels=labels,
            )
            report.roc_curves[clf.name] = roc

        report.comparison_table.sort(key=lambda m: m.f1_macro, reverse=True)
        return report

    def print_comparison_table(self, report: EvaluationReport) -> None:
        header = (
            f"{'Model':<20} {'Tier':<8} {'Acc':>6} {'Prec':>6} "
            f"{'Rec':>6} {'F1':>6} {'AUC':>6} {'ms':>8}"
        )
        print(header)
        print("-" * len(header))
        for m in report.comparison_table:
            print(
                f"{m.model_name:<20} {m.tier:<8} {m.accuracy:>6.3f} "
                f"{m.precision_macro:>6.3f} {m.recall_macro:>6.3f} "
                f"{m.f1_macro:>6.3f} {m.auc_macro:>6.3f} {m.latency_ms:>8.2f}"
            )
