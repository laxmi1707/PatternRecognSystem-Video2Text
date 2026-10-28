from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from app.ml.config import MLConfig, NUM_CLASSES

logger = logging.getLogger(__name__)


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


def load_real_dataset(
    dataset_root: str | None = None,
    config: MLConfig | None = None,
    use_augmentation: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    if config is None:
        config = MLConfig()
    root = Path(dataset_root or config.dataset_root)

    from app.ml.dataset_loader import discover_tasks
    from app.pipeline.feature_assembler import get_default_assembler

    tasks = discover_tasks(root)
    if not tasks:
        logger.warning(f"No tasks found in {root}, falling back to synthetic data")
        return generate_synthetic_dataset(n_features=config.n_features, config=config)

    logger.info(f"Found {len(tasks)} tasks in {root}")
    assembler = get_default_assembler()
    X, y, metadata = assembler.build_dataset(tasks)

    if use_augmentation and X.shape[0] < 100:
        from app.pipeline.augmentation import augment_features
        logger.info(f"Augmenting {X.shape[0]} samples (too few for training)...")
        X, y = augment_features(X, y, n_augmented=5, seed=config.seed)

    logger.info(f"Real dataset loaded: X={X.shape}, y={y.shape}")
    return X, y


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


def task_level_split(
    X: np.ndarray,
    y: np.ndarray,
    task_ids: np.ndarray,
    test_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)

    unique_tasks = np.unique(task_ids)
    rng.shuffle(unique_tasks)

    split_idx = max(1, int(len(unique_tasks) * (1 - test_ratio)))
    train_tasks = set(unique_tasks[:split_idx].tolist())

    train_mask = np.array([tid in train_tasks for tid in task_ids])
    test_mask = ~train_mask

    return X[train_mask], X[test_mask], y[train_mask], y[test_mask]
