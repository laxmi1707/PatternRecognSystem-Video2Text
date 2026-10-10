"""
Rebuild tier3 ensemble .pkl files without re-extracting features.

Loads already-trained svm.pkl, random_forest.pkl, mlp.pkl from disk,
wraps them in voting/stacking/late_fusion, fits the meta-learners on a
small synthetic dataset, then saves the corrected .pkl files.

Runs in under 2 minutes — no video or dataset access needed.

Usage:
    python -m app.retrain_tier3
    python -m app.retrain_tier3 --model-dir ./models
"""
from __future__ import annotations

import argparse
import logging
import os
import time
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import numpy as np
from sklearn.metrics import f1_score

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="./models")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)

    from app.ml.config import MLConfig
    from app.ml.classifiers.tier1.svm import SVMClassifier
    from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
    from app.ml.classifiers.tier2 import MLPClassifier
    from app.ml.classifiers.tier3.voting import VotingClassifier
    from app.ml.classifiers.tier3.stacking import StackingClassifier
    from app.ml.classifiers.tier3.late_fusion import LateFusionClassifier
    from app.ml.dataset import generate_synthetic_dataset

    config = MLConfig()

    def load_clf(clf, name: str):
        path = model_dir / f"{name}.pkl"
        if not path.exists():
            raise FileNotFoundError(f"Missing: {path}. Run train.py first.")
        clf.load(str(path))
        logger.info(f"  Loaded {name}.pkl")
        return clf

    # Load base estimators (already trained on 9,609 real tasks)
    logger.info("Loading base estimators from disk...")
    svm_v  = load_clf(SVMClassifier(), "svm")
    rf_v   = load_clf(RandomForestClassifier(), "random_forest")
    mlp_v  = load_clf(MLPClassifier(num_classes=config.num_classes), "mlp")

    svm_s  = load_clf(SVMClassifier(), "svm")
    rf_s   = load_clf(RandomForestClassifier(), "random_forest")
    mlp_s  = load_clf(MLPClassifier(num_classes=config.num_classes), "mlp")

    svm_lf = load_clf(SVMClassifier(), "svm")
    rf_lf  = load_clf(RandomForestClassifier(), "random_forest")

    # Small synthetic dataset just to fit the meta-learners
    logger.info("Generating synthetic data for meta-learner fitting...")
    X_syn, y_syn = generate_synthetic_dataset(
        n_samples=1000, n_features=config.n_features, config=config
    )

    tier3 = [
        VotingClassifier(estimators=[svm_v, rf_v, mlp_v], voting="soft"),
        StackingClassifier(base_estimators=[svm_s, rf_s, mlp_s]),
        LateFusionClassifier(branches=[svm_lf, rf_lf]),
    ]

    for clf in tier3:
        logger.info(f"Fitting {clf.name} meta-learner...")
        t0 = time.time()
        clf.fit(X_syn, y_syn)
        elapsed = time.time() - t0

        out = model_dir / f"{clf.name}.pkl"
        clf.save(str(out))

        pred = clf.predict(X_syn)
        f1 = f1_score(y_syn, pred.labels, average="macro", zero_division=0)
        logger.info(f"  {clf.name}: synthetic F1={f1:.4f}, time={elapsed:.1f}s → {out}")

    logger.info("Done. Restart the backend to load the updated models.")


if __name__ == "__main__":
    main()
