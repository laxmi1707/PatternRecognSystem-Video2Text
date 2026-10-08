"""
Retrain only the tier3 ensemble models (voting, stacking, late_fusion)
using already-trained tier1/2 estimators loaded from existing .pkl files.

Requires feature cache saved by train.py (X_train.npy, y_train.npy in --model-dir).
If cache is missing, falls back to full feature extraction from dataset.

Usage:
    python -m app.retrain_tier3
    python -m app.retrain_tier3 --dataset-root ./dataset --model-dir ./models
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import numpy as np
from sklearn.metrics import f1_score

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrain tier3 ensemble models only")
    parser.add_argument("--dataset-root", default="./dataset")
    parser.add_argument("--model-dir", default="./models")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)

    # Load cached features if available (saved by train.py)
    cache_X = model_dir / "X_train.npy"
    cache_y = model_dir / "y_train.npy"

    if cache_X.exists() and cache_y.exists():
        logger.info("Loading cached train features from disk...")
        X_train = np.load(str(cache_X))
        y_train = np.load(str(cache_y))
        logger.info(f"  Loaded X_train={X_train.shape}, y_train={y_train.shape}")
    else:
        logger.info("No feature cache found — extracting from dataset (this takes a while)...")
        from app.ml.config import ACTIVITY_LABELS
        from app.ml.dataset_loader import discover_tasks, task_level_split
        from app.pipeline.feature_assembler import get_default_assembler

        dataset_root = Path(args.dataset_root)
        if not dataset_root.exists():
            logger.error(f"Dataset not found: {dataset_root}")
            sys.exit(1)

        tasks = discover_tasks(dataset_root)
        train_tasks, _ = task_level_split(tasks, test_ratio=0.2, seed=42)
        assembler = get_default_assembler()
        X_train, y_train, _ = assembler.build_dataset(train_tasks)

        all_labels = np.unique(y_train)
        label_map = {old: new for new, old in enumerate(all_labels)}
        y_train = np.array([label_map[y] for y in y_train])

        model_dir.mkdir(parents=True, exist_ok=True)
        np.save(str(cache_X), X_train)
        np.save(str(cache_y), y_train)
        logger.info(f"  Extracted and cached: X_train={X_train.shape}")

    # Load already-trained base estimators
    from app.ml.classifiers.tier1.svm import SVMClassifier
    from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
    from app.ml.classifiers.tier2 import MLPClassifier
    from app.ml.classifiers.tier3.voting import VotingClassifier
    from app.ml.classifiers.tier3.stacking import StackingClassifier
    from app.ml.classifiers.tier3.late_fusion import LateFusionClassifier

    def load_base(clf, name):
        path = model_dir / f"{name}.pkl"
        if not path.exists():
            logger.error(f"Missing base model: {path}. Run train.py first.")
            sys.exit(1)
        clf.load(str(path))
        logger.info(f"  Loaded {name}")
        return clf

    svm1 = load_base(SVMClassifier(), "svm")
    svm2 = load_base(SVMClassifier(), "svm")
    rf1  = load_base(RandomForestClassifier(), "random_forest")
    rf2  = load_base(RandomForestClassifier(), "random_forest")
    mlp1 = load_base(MLPClassifier(), "mlp")
    mlp2 = load_base(MLPClassifier(), "mlp")

    tier3 = [
        VotingClassifier(estimators=[svm1, rf1, mlp1], voting="soft"),
        StackingClassifier(base_estimators=[svm2, rf2, mlp2]),
        LateFusionClassifier(branches=[load_base(SVMClassifier(), "svm"),
                                        load_base(RandomForestClassifier(), "random_forest")]),
    ]

    for clf in tier3:
        logger.info(f"Training {clf.name}...")
        t0 = time.time()
        clf.fit(X_train, y_train)
        elapsed = time.time() - t0

        out = model_dir / f"{clf.name}.pkl"
        clf.save(str(out))

        pred = clf.predict(X_train)
        f1 = f1_score(y_train, pred.labels, average="macro", zero_division=0)
        logger.info(f"  {clf.name}: train F1={f1:.4f}, time={elapsed:.1f}s → saved {out}")

    logger.info("Tier3 retrain complete.")


if __name__ == "__main__":
    main()
