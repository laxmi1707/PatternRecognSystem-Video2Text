"""
Train Video2Knowledge classifiers on the CUA-Suite dataset.

Feature extraction and model training are separate pipeline stages:
  - First run: extracts features from all videos (~15 hours), saves cache,
    then trains all models (~10 minutes).
  - Subsequent runs with --load-features: skips extraction, loads cache,
    retrains models in ~10 minutes. Use after label fixes or hyperparameter
    changes that don't touch feature extraction code.

Usage:
    # Full run (first time):
    python -m app.train --dataset-root ./dataset --model-dir ./models

    # Fast retrain (after label/model changes, features already cached):
    python -m app.train --dataset-root ./dataset --model-dir ./models --load-features
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

warnings.filterwarnings("ignore", message=".*pin_memory.*")
warnings.filterwarnings("ignore", message=".*probability.*parameter was deprecated.*")
warnings.filterwarnings("ignore", message=".*torch.quantize_per_tensor.*")

import numpy as np

from app.ml.config import MLConfig, ACTIVITY_LABELS
from app.ml.dataset_loader import discover_tasks, task_level_split
from app.ml.tracking import tracker

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Video2Knowledge classifiers")
    parser.add_argument("--dataset-root", default="./dataset", help="Path to dataset directory")
    parser.add_argument("--model-dir", default="./models", help="Where to save trained models")
    parser.add_argument("--skip-deep", action="store_true", help="Skip Tier 2/3 PyTorch models (for macOS)")
    parser.add_argument(
        "--load-features", action="store_true",
        help="Skip feature extraction and load cached X_train/X_test/y_train/y_test from --model-dir. "
             "Use after label or model changes when feature extraction code is unchanged."
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    feature_cache = {
        "X_train": model_dir / "X_train.npy",
        "X_test":  model_dir / "X_test.npy",
        "y_train": model_dir / "y_train.npy",
        "y_test":  model_dir / "y_test.npy",
    }

    if args.load_features:
        # ── Fast path: skip 15-hour extraction, load cached arrays ──────────
        missing = [k for k, p in feature_cache.items() if not p.exists()]
        if missing:
            logger.error(
                f"--load-features requested but cache files missing: {missing}\n"
                f"Run without --load-features first to build the cache."
            )
            sys.exit(1)

        logger.info("Loading cached features (skipping extraction)...")
        X_train = np.load(str(feature_cache["X_train"]))
        X_test  = np.load(str(feature_cache["X_test"]))
        y_train = np.load(str(feature_cache["y_train"]))
        y_test  = np.load(str(feature_cache["y_test"]))
        logger.info(f"  X_train={X_train.shape}, X_test={X_test.shape}")

        # Labels in cache are already remapped integers — just log distribution
        logger.info(f"Label distribution in cache: {Counter(y_train.tolist())}")
        all_labels = np.unique(np.concatenate([y_train, y_test]))
        mapped_labels = [str(i) for i in all_labels]

    else:
        # ── Full path: discover tasks, extract features, save cache ─────────
        dataset_root = Path(args.dataset_root)
        if not dataset_root.exists():
            logger.error(f"Dataset directory not found: {dataset_root}")
            sys.exit(1)

        # 1. Discover tasks
        logger.info(f"Scanning dataset at {dataset_root.resolve()}")
        tasks = discover_tasks(dataset_root)
        if not tasks:
            logger.error("No tasks found in dataset")
            sys.exit(1)

        labels = Counter(t.activity_label for t in tasks)
        platforms = Counter(t.platform for t in tasks)
        has_video = sum(1 for t in tasks if t.video_path)

        logger.info(f"Discovered {len(tasks)} tasks ({has_video} with video)")
        logger.info(f"Platforms: {dict(platforms)}")
        logger.info("Label distribution:")
        for label in ACTIVITY_LABELS:
            count = labels.get(label, 0)
            logger.info(f"  {label}: {count}")

        tracker.log_training(
            model_name="dataset",
            tier="data",
            metrics={f"label_{k}": float(v) for k, v in labels.items()},
            params={
                "total_tasks": len(tasks),
                "tasks_with_video": has_video,
                "dataset_root": str(dataset_root.resolve()),
            },
            tags={"run_type": "dataset_stats"},
        )

        # 2. Split train/test at task level
        train_tasks, test_tasks = task_level_split(tasks, test_ratio=0.2, seed=42)
        logger.info(f"Split: {len(train_tasks)} train, {len(test_tasks)} test")

        # 3. Extract features
        from app.pipeline.feature_assembler import get_default_assembler
        assembler = get_default_assembler()

        total_tasks = len(train_tasks) + len(test_tasks)
        logger.info(f"Phase 1/3: Extracting TRAIN features ({len(train_tasks)}/{total_tasks} tasks)...")
        t0 = time.time()
        X_train, y_train, meta_train = assembler.build_dataset(train_tasks)
        logger.info(f"  Train features done: {X_train.shape} in {time.time()-t0:.0f}s")

        logger.info(f"Phase 2/3: Extracting TEST features ({len(test_tasks)}/{total_tasks} tasks)...")
        t1 = time.time()
        X_test, y_test, meta_test = assembler.build_dataset(test_tasks)
        logger.info(f"  Test features done: {X_test.shape} in {time.time()-t1:.0f}s")

        logger.info(
            f"Feature extraction complete: {time.time()-t0:.0f}s total | "
            f"train={X_train.shape}, test={X_test.shape}"
        )

        if X_train.shape[0] == 0:
            logger.error("No training samples extracted")
            sys.exit(1)

        # Remap labels to contiguous 0..N-1 (XGBoost/LightGBM require this)
        all_labels = np.unique(np.concatenate([y_train, y_test]))
        label_map = {old: new for new, old in enumerate(all_labels)}
        reverse_map = {new: old for old, new in label_map.items()}
        y_train = np.array([label_map[y] for y in y_train])
        y_test  = np.array([label_map[y] for y in y_test])
        mapped_labels = [ACTIVITY_LABELS[reverse_map[i]] for i in range(len(all_labels))]
        logger.info(f"Remapped {len(all_labels)} classes: {mapped_labels}")

        # Save feature cache for fast retrains
        np.save(str(feature_cache["X_train"]), X_train)
        np.save(str(feature_cache["X_test"]),  X_test)
        np.save(str(feature_cache["y_train"]), y_train)
        np.save(str(feature_cache["y_test"]),  y_test)
        logger.info(f"Feature cache saved to {model_dir} — use --load-features to skip extraction next time")

    # Augment if too few samples
    if X_train.shape[0] < 100:
        from app.pipeline.augmentation import augment_features
        logger.info(f"Augmenting training data ({X_train.shape[0]} → ~{X_train.shape[0] * 6} samples)")
        X_train, y_train = augment_features(X_train, y_train, n_augmented=5)

    # 4. Initialize ML service (all models registered at startup)
    from app.services.ml_service import ml_service

    logger.info(f"Registered {len(ml_service.list_models())} models (all tiers)")

    # 5. Train all models (save each immediately so crashes don't lose progress)
    from sklearn.metrics import accuracy_score, f1_score

    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    model_names = ml_service.list_models()
    total_models = len(model_names)
    logger.info(f"Phase 3/3: Training {total_models} models...")
    results = []
    for m_idx, clf_name in enumerate(model_names, 1):
        try:
            clf = ml_service.get_model(clf_name)
            t0 = time.time()
            clf.fit(X_train, y_train)
            train_time = time.time() - t0
            ml_service._trained_models.add(clf_name)

            clf.save(str(model_dir / f"{clf_name}.pkl"))

            pred = clf.predict(X_test)
            acc = accuracy_score(y_test, pred.labels)
            f1 = f1_score(y_test, pred.labels, average="macro", zero_division=0)

            results.append({
                "model": clf_name,
                "tier": clf.tier,
                "accuracy": acc,
                "f1_macro": f1,
                "latency_ms": pred.latency_ms,
                "train_time": train_time,
            })
            tracker.log_training(
                model_name=clf_name,
                tier=clf.tier,
                metrics={"accuracy": acc, "f1_macro": f1, "latency_ms": pred.latency_ms},
                params={"train_time_s": round(train_time, 2), "n_train": int(X_train.shape[0]), "n_test": int(X_test.shape[0])},
                tags={"tier": clf.tier},
            )
            logger.info(
                f"  [{m_idx}/{total_models}] {clf_name:20s} | acc={acc:.4f} | f1={f1:.4f} | "
                f"latency={pred.latency_ms:.1f}ms | train={train_time:.1f}s ✓"
            )
        except Exception as e:
            logger.warning(f"  [{m_idx}/{total_models}] {clf_name:20s} | FAILED: {e}")

    logger.info(f"Models saved to {model_dir.resolve()}")

    # 7. Print summary
    if results:
        results.sort(key=lambda r: (-r["f1_macro"], r["latency_ms"]))
        print("\n" + "=" * 80)
        print("MODEL COMPARISON (sorted by F1 macro)")
        print("=" * 80)
        print(f"{'#':>3}  {'Model':20s}  {'Tier':12s}  {'Accuracy':>10}  {'F1 Macro':>10}  {'Latency':>10}  {'Train':>8}")
        print("-" * 80)
        for i, r in enumerate(results, 1):
            print(
                f"{i:>3}  {r['model']:20s}  {r['tier']:12s}  "
                f"{r['accuracy']:>10.4f}  {r['f1_macro']:>10.4f}  "
                f"{r['latency_ms']:>8.1f}ms  {r['train_time']:>6.1f}s"
            )
        print("=" * 80)
        best = results[0]
        print(f"\nBest model: {best['model']} (F1={best['f1_macro']:.4f}, Accuracy={best['accuracy']:.4f})")

        tracker.log_evaluation(
            comparison_table=[
                {"model_name": r["model"], "f1_macro": r["f1_macro"], "accuracy": r["accuracy"], "latency_ms": r["latency_ms"]}
                for r in results
            ],
            best_model=best["model"],
            best_f1=best["f1_macro"],
            n_models=len(results),
            n_samples=int(X_train.shape[0]) + int(X_test.shape[0]),
        )

    print(f"\nTraining complete. {len(results)} models trained and saved.")
    print(f"Start the backend to use pre-trained models:")
    print(f"  uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
