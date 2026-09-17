from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ExperimentTracker:
    def __init__(self, experiment_name: str = "video2knowledge", tracking_uri: str | None = None):
        self._experiment_name = experiment_name
        self._tracking_uri = tracking_uri
        self._mlflow = None
        self._enabled = False
        self._init_mlflow()

    def _init_mlflow(self) -> None:
        try:
            import mlflow
            self._mlflow = mlflow
            if self._tracking_uri:
                mlflow.set_tracking_uri(self._tracking_uri)
            mlflow.set_experiment(self._experiment_name)
            self._enabled = True
            logger.info(f"MLflow tracking enabled: experiment={self._experiment_name}")
        except ImportError:
            logger.info("MLflow not installed, tracking disabled")
        except Exception as e:
            logger.warning(f"MLflow initialization failed: {e}")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def log_training(
        self,
        model_name: str,
        tier: str,
        metrics: dict[str, float],
        params: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> str | None:
        if not self._enabled:
            return None

        with self._mlflow.start_run(run_name=f"train_{model_name}") as run:
            self._mlflow.set_tag("model_name", model_name)
            self._mlflow.set_tag("tier", tier)
            if tags:
                self._mlflow.set_tags(tags)

            if params:
                self._mlflow.log_params(params)
            self._mlflow.log_metrics(metrics)

            logger.info(f"Logged training run for {model_name}: {metrics}")
            return run.info.run_id

    def log_evaluation(
        self,
        comparison_table: list[dict],
        best_model: str,
        best_f1: float,
        n_models: int,
        n_samples: int,
    ) -> str | None:
        if not self._enabled:
            return None

        with self._mlflow.start_run(run_name="evaluation") as run:
            self._mlflow.set_tag("run_type", "evaluation")
            self._mlflow.log_param("n_models", n_models)
            self._mlflow.log_param("n_samples", n_samples)
            self._mlflow.log_metric("best_f1", best_f1)
            self._mlflow.set_tag("best_model", best_model)

            for row in comparison_table:
                name = row.get("model_name", "unknown")
                with self._mlflow.start_run(
                    run_name=f"eval_{name}", nested=True
                ):
                    eval_metrics = {
                        k: v for k, v in row.items()
                        if isinstance(v, (int, float)) and k != "model_name"
                    }
                    self._mlflow.log_metrics(eval_metrics)
                    self._mlflow.set_tag("model_name", name)

            return run.info.run_id

    def log_ablation(
        self,
        model_name: str,
        baseline_f1: float,
        ablation_results: list[dict],
    ) -> str | None:
        if not self._enabled:
            return None

        with self._mlflow.start_run(run_name=f"ablation_{model_name}") as run:
            self._mlflow.set_tag("run_type", "ablation")
            self._mlflow.set_tag("model_name", model_name)
            self._mlflow.log_metric("baseline_f1", baseline_f1)

            for ab in ablation_results:
                modality = ab.get("modality_name", "unknown")
                self._mlflow.log_metric(f"f1_without_{modality}", ab.get("f1_without", 0))
                self._mlflow.log_metric(f"f1_drop_{modality}", ab.get("f1_drop", 0))

            return run.info.run_id


_tracker: ExperimentTracker | None = None


def get_tracker() -> ExperimentTracker:
    global _tracker
    if _tracker is None:
        _tracker = ExperimentTracker()
    return _tracker
