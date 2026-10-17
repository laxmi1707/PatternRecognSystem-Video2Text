"""
Regenerate y_train.npy and y_test.npy from the dataset using the current
derive_activity_label() mapping — without re-extracting visual features.

Requires task_ids_train.npy / task_ids_test.npy saved by train.py during
feature extraction. These map each segment row back to its source task_id,
so y labels can be regenerated at the correct per-segment shape.

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
from app.ml.dataset_loader import discover_tasks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

LABEL_TO_IDX = {label: i for i, label in enumerate(ACTIVITY_LABELS)}


def _relabel_split(
    task_id_to_label: dict[int, int],
    task_ids: np.ndarray,
    x_shape: int,
    split_name: str,
) -> np.ndarray:
    if len(task_ids) != x_shape:
        logger.error(
            f"task_ids_{split_name}.npy has {len(task_ids)} rows but "
            f"X_{split_name}.npy has {x_shape} rows — they must match. "
            "Re-run full feature extraction to regenerate task_ids files."
        )
        raise SystemExit(1)

    other_idx = LABEL_TO_IDX["other"]
    y = np.array(
        [task_id_to_label.get(int(tid), other_idx) for tid in task_ids],
        dtype=np.int64,
    )
    counts = Counter(y.tolist())
    logger.info(f"  {split_name} label distribution (index → count): {dict(sorted(counts.items()))}")
    named = {ACTIVITY_LABELS[idx]: cnt for idx, cnt in counts.items() if idx < len(ACTIVITY_LABELS)}
    logger.info(f"  {split_name} label distribution (name  → count):")
    for label in ACTIVITY_LABELS:
        logger.info(f"    {label:25s}: {named.get(label, 0)}")
    return y


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate y_train/y_test with updated labels")
    parser.add_argument("--dataset-root", default="./dataset")
    parser.add_argument("--model-dir", default="./models")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    dataset_root = Path(args.dataset_root)

    x_train_path = model_dir / "X_train.npy"
    x_test_path = model_dir / "X_test.npy"
    task_ids_train_path = model_dir / "task_ids_train.npy"
    task_ids_test_path = model_dir / "task_ids_test.npy"

    for p in [x_train_path, x_test_path, task_ids_train_path, task_ids_test_path]:
        if not p.exists():
            logger.error(
                f"Required file not found: {p}\n"
                "Run full feature extraction first (without --load-features) to generate "
                "X_train.npy, X_test.npy, task_ids_train.npy, task_ids_test.npy."
            )
            raise SystemExit(1)

    X_train = np.load(str(x_train_path))
    X_test = np.load(str(x_test_path))
    task_ids_train = np.load(str(task_ids_train_path))
    task_ids_test = np.load(str(task_ids_test_path))
    logger.info(f"Loaded X_train={X_train.shape}, X_test={X_test.shape}")
    logger.info(f"Loaded task_ids_train={task_ids_train.shape}, task_ids_test={task_ids_test.shape}")

    logger.info(f"Scanning dataset at {dataset_root.resolve()}")
    tasks = discover_tasks(dataset_root)
    logger.info(f"Discovered {len(tasks)} tasks")

    task_id_to_label: dict[int, int] = {
        t.task_id: LABEL_TO_IDX.get(t.activity_label, LABEL_TO_IDX["other"])
        for t in tasks
    }

    logger.info("Regenerating y_train...")
    y_train = _relabel_split(task_id_to_label, task_ids_train, X_train.shape[0], "train")

    logger.info("Regenerating y_test...")
    y_test = _relabel_split(task_id_to_label, task_ids_test, X_test.shape[0], "test")

    np.save(str(model_dir / "y_train.npy"), y_train)
    np.save(str(model_dir / "y_test.npy"), y_test)
    logger.info(f"Saved y_train.npy {y_train.shape} and y_test.npy {y_test.shape}")
    logger.info("Now run: python -m app.train --dataset-root ./dataset --model-dir ./models --load-features")


if __name__ == "__main__":
    main()
