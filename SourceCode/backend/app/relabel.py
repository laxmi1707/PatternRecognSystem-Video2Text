"""
Regenerate y_train.npy and y_test.npy from the dataset using the current
derive_activity_label() mapping — without re-extracting visual features.

Use this after fixing label mappings in dataset_loader.py when X_train.npy /
X_test.npy are already cached and valid.

Usage:
    python -m app.relabel --dataset-root ./dataset --model-dir ./models
"""
from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path

import numpy as np

from app.ml.config import ACTIVITY_LABELS
from app.ml.dataset_loader import discover_tasks, task_level_split

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

LABEL_TO_IDX = {label: i for i, label in enumerate(ACTIVITY_LABELS)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate y_train/y_test with updated labels")
    parser.add_argument("--dataset-root", default="./dataset")
    parser.add_argument("--model-dir", default="./models")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    dataset_root = Path(args.dataset_root)

    # Verify X caches exist
    x_train_path = model_dir / "X_train.npy"
    x_test_path = model_dir / "X_test.npy"
    if not x_train_path.exists() or not x_test_path.exists():
        logger.error("X_train.npy / X_test.npy not found — run full training first")
        raise SystemExit(1)

    X_train = np.load(str(x_train_path))
    X_test = np.load(str(x_test_path))
    logger.info(f"Loaded X_train={X_train.shape}, X_test={X_test.shape}")

    logger.info(f"Scanning dataset at {dataset_root.resolve()}")
    tasks = discover_tasks(dataset_root)
    logger.info(f"Discovered {len(tasks)} tasks")

    label_counts = Counter(t.activity_label for t in tasks)
    logger.info("New label distribution:")
    for label in ACTIVITY_LABELS:
        count = label_counts.get(label, 0)
        logger.info(f"  {label:25s}: {count}")
    logger.info(f"  {'other':25s}: {label_counts.get('other', 0)}")

    train_tasks, test_tasks = task_level_split(tasks, test_ratio=0.2, seed=42)
    logger.info(f"Split: {len(train_tasks)} train, {len(test_tasks)} test")

    y_train = np.array([LABEL_TO_IDX.get(t.activity_label, LABEL_TO_IDX["other"]) for t in train_tasks], dtype=np.int64)
    y_test = np.array([LABEL_TO_IDX.get(t.activity_label, LABEL_TO_IDX["other"]) for t in test_tasks], dtype=np.int64)

    if len(y_train) != X_train.shape[0]:
        logger.warning(
            f"y_train length ({len(y_train)}) != X_train rows ({X_train.shape[0]}). "
            "This means tasks were added/removed since the last feature extraction. "
            "Truncating/padding to match — consider a full retrain for accuracy."
        )
        min_train = min(len(y_train), X_train.shape[0])
        y_train = y_train[:min_train]

    if len(y_test) != X_test.shape[0]:
        logger.warning(
            f"y_test length ({len(y_test)}) != X_test rows ({X_test.shape[0]}). Truncating."
        )
        min_test = min(len(y_test), X_test.shape[0])
        y_test = y_test[:min_test]

    np.save(str(model_dir / "y_train.npy"), y_train)
    np.save(str(model_dir / "y_test.npy"), y_test)
    logger.info(f"Saved y_train.npy ({y_train.shape}) and y_test.npy ({y_test.shape})")
    logger.info("Run: python -m app.train --dataset-root ./dataset --model-dir ./models --load-features")


if __name__ == "__main__":
    main()
