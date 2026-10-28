from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import time

import numpy as np


@dataclass(frozen=True)
class PredictionResult:
    labels: np.ndarray
    probabilities: np.ndarray
    latency_ms: float


class BaseClassifier(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def tier(self) -> str:
        ...

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        ...

    @abstractmethod
    def predict(self, X: np.ndarray) -> PredictionResult:
        ...

    @abstractmethod
    def save(self, path: str) -> None:
        ...

    @abstractmethod
    def load(self, path: str) -> None:
        ...

    def get_params(self) -> dict[str, Any]:
        return {}

    def _timed_predict(
        self,
        predict_fn: Any,
        X: np.ndarray,
    ) -> PredictionResult:
        start = time.perf_counter()
        labels, probas = predict_fn(X)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return PredictionResult(
            labels=labels,
            probabilities=probas,
            latency_ms=elapsed_ms,
        )
