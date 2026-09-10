import numpy as np

from app.ml.config import MLConfig, NUM_CLASSES


def generate_synthetic_dataset(
    n_samples: int = 500,
    n_features: int = 200,
    config: MLConfig | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if config is None:
        config = MLConfig()

    rng = np.random.RandomState(config.seed)

    samples_per_class = n_samples // NUM_CLASSES
    X_parts = []
    y_parts = []

    for class_idx in range(NUM_CLASSES):
        center = rng.randn(n_features) * (class_idx + 1) * 0.3
        noise = rng.randn(samples_per_class, n_features) * 0.8
        X_class = center + noise
        y_class = np.full(samples_per_class, class_idx)
        X_parts.append(X_class)
        y_parts.append(y_class)

    X = np.vstack(X_parts)
    y = np.concatenate(y_parts)

    shuffle_idx = rng.permutation(len(y))
    return X[shuffle_idx], y[shuffle_idx]


def train_test_split_data(
    X: np.ndarray,
    y: np.ndarray,
    config: MLConfig | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if config is None:
        config = MLConfig()

    rng = np.random.RandomState(config.seed)
    n = len(y)
    indices = rng.permutation(n)
    split = int(n * (1 - config.test_size))

    train_idx = indices[:split]
    test_idx = indices[split:]

    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]
