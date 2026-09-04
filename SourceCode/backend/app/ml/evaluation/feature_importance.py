from dataclasses import dataclass

import numpy as np

from app.ml.base import BaseClassifier


@dataclass(frozen=True)
class FeatureImportanceResult:
    model_name: str
    method: str
    feature_indices: np.ndarray
    importances_mean: np.ndarray
    importances_std: np.ndarray
    top_k_indices: np.ndarray
    top_k_means: np.ndarray


def compute_feature_importance(
    classifier: BaseClassifier,
    X: np.ndarray,
    y: np.ndarray,
    n_repeats: int = 10,
    top_k: int = 20,
    seed: int = 42,
) -> FeatureImportanceResult:
    rng = np.random.RandomState(seed)
    baseline_acc = float(np.mean(classifier.predict(X).labels == y))

    n_features = X.shape[1]
    importances = np.zeros((n_repeats, n_features))

    for r in range(n_repeats):
        for f in range(n_features):
            X_permuted = X.copy()
            X_permuted[:, f] = rng.permutation(X_permuted[:, f])
            permuted_acc = float(np.mean(classifier.predict(X_permuted).labels == y))
            importances[r, f] = baseline_acc - permuted_acc

    means = importances.mean(axis=0)
    stds = importances.std(axis=0)
    sorted_idx = np.argsort(means)[::-1]
    top_k = min(top_k, len(sorted_idx))

    return FeatureImportanceResult(
        model_name=classifier.name,
        method="permutation",
        feature_indices=sorted_idx,
        importances_mean=means[sorted_idx],
        importances_std=stds[sorted_idx],
        top_k_indices=sorted_idx[:top_k],
        top_k_means=means[sorted_idx[:top_k]],
    )


def print_feature_importance(result: FeatureImportanceResult, n: int = 10) -> None:
    print(f"\nTop {n} features for {result.model_name} ({result.method}):")
    print(f"{'Rank':<6} {'Feature':<12} {'Importance':<14} {'Std':<10}")
    print("-" * 42)
    for i in range(min(n, len(result.top_k_indices))):
        print(
            f"{i+1:<6} feature_{result.top_k_indices[i]:<5} "
            f"{result.top_k_means[i]:<14.4f} "
            f"{result.importances_std[i]:<10.4f}"
        )
