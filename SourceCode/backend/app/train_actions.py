"""Train Level 1 action-type classifiers (Tier 1 + MLP) with a train/val/test split.

Each logged user action (pointer move, click, typing, key press, hotkey, drag) is
one sample, labelled from the action log and described by video-only features
(see app/ml/action_dataset.py). Tasks are split 70/20/10 by recording, so no
recording contributes to more than one split.

For every model, each hyperparameter setting in GRIDS is trained on the train
split and scored on validation (macro F1); the best setting is then scored once
on the test split. Outputs in --model-dir:

    <model>.pkl     best fitted model per algorithm
    scaler.pkl      StandardScaler fitted on the train split (apply before predict)
    labels.json     class names in index order, plus granularity and frame offsets
    split.json      task IDs in each split
    features.npz    feature cache (reuse with --load-features)
    metrics.json    validation and test metrics, best params, confusion matrices
    results.md      the same as readable tables

Usage:
    python -m app.train_actions --dataset-root ../../dataset --model-dir ./models/actions/v1
    python -m app.train_actions --model-dir ./models/actions/v1 --load-features
"""
from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", message=".*pin_memory.*")

from app.ml.action_dataset import FRAME_OFFSETS, build_action_dataset, labels_for  # noqa: E402
from app.ml.base import BaseClassifier  # noqa: E402
from app.ml.dataset_loader import discover_tasks, task_level_split_3way  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SPLITS = ("train", "val", "test")

# Small per-model grids; every setting is fit on train and scored on validation.
GRIDS: dict[str, list[dict]] = {
    "svm": [{"C": c} for c in (0.3, 1.0, 3.0, 10.0)],
    "naive_bayes": [{}],
    "decision_tree": [{"max_depth": d} for d in (8, 16, None)],
    "random_forest": [{"n_estimators": 300, "max_depth": d} for d in (16, None)],
    "knn": [{"n_neighbors": k} for k in (3, 7, 15)],
    "xgboost": [{"n_estimators": 300, "max_depth": d, "learning_rate": 0.1} for d in (4, 8)],
    "lightgbm": [{"n_estimators": 300, "max_depth": d, "learning_rate": 0.05} for d in (-1, 8)],
    "mlp": [{"hidden_dim": h, "num_layers": 2, "dropout": 0.3, "epochs": 40} for h in (128, 256)],
}


def make_model(name: str, params: dict, num_classes: int) -> BaseClassifier:
    from app.ml.classifiers.tier1.decision_tree import DecisionTreeClassifier
    from app.ml.classifiers.tier1.knn import KNNClassifier
    from app.ml.classifiers.tier1.lightgbm_clf import LightGBMClassifier
    from app.ml.classifiers.tier1.naive_bayes import NaiveBayesClassifier
    from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
    from app.ml.classifiers.tier1.svm import SVMClassifier
    from app.ml.classifiers.tier1.xgboost_clf import XGBoostClassifier

    if name == "mlp":
        from app.ml.classifiers.tier2.mlp import MLPClassifier

        return MLPClassifier(num_classes=num_classes, **params)

    classes = {
        "svm": SVMClassifier,
        "naive_bayes": NaiveBayesClassifier,
        "decision_tree": DecisionTreeClassifier,
        "random_forest": RandomForestClassifier,
        "knn": KNNClassifier,
        "xgboost": XGBoostClassifier,
        "lightgbm": LightGBMClassifier,
    }
    clf = classes[name](**params)
    if name == "svm":
        # The wrapper enables libsvm's verbose output, which floods the log.
        clf._model.set_params(verbose=False)
    return clf


def _split_info(task_ids: np.ndarray, y: np.ndarray, labels: tuple[str, ...]) -> dict:
    counts = Counter(int(v) for v in y)
    return {
        "tasks": int(len(np.unique(task_ids))),
        "events": int(len(y)),
        "per_class": {labels[i]: counts.get(i, 0) for i in range(len(labels))},
    }


def _evaluate(clf: BaseClassifier, X: np.ndarray, y: np.ndarray, labels: tuple[str, ...]) -> dict:
    from app.ml.evaluation.confusion import compute_confusion_matrix
    from app.ml.evaluation.metrics import compute_metrics

    pred = clf.predict(X)
    m = compute_metrics(
        model_name=clf.name, tier=clf.tier, y_true=y, y_pred=pred.labels,
        y_proba=pred.probabilities, latency_ms=pred.latency_ms, num_classes=len(labels),
    )
    cm = compute_confusion_matrix(clf.name, y, pred.labels, list(labels))
    f1_per_class = list(m.f1_per_class) + [0.0] * (len(labels) - len(m.f1_per_class))
    return {
        "accuracy": round(float(m.accuracy), 4),
        "precision_macro": round(float(m.precision_macro), 4),
        "recall_macro": round(float(m.recall_macro), 4),
        "f1_macro": round(float(m.f1_macro), 4),
        "auc_macro": round(float(m.auc_macro), 4),
        "latency_ms": round(float(m.latency_ms), 2),
        "f1_per_class": {labels[i]: round(float(f), 4) for i, f in enumerate(f1_per_class)},
        "confusion_matrix": cm.matrix.tolist(),
    }


def _write_results_md(path: Path, meta: dict, results: dict) -> None:
    labels = meta["labels"]
    lines = [
        f"# Action classifier results ({meta['granularity']})",
        "",
        f"Split (by recording, stratified by app): {meta['ratios']}",
        "",
        "| Split | Tasks | Events | " + " | ".join(labels) + " |",
        "|---|---|---|" + "---|" * len(labels),
    ]
    for s in SPLITS:
        info = meta["splits"][s]
        lines.append(
            f"| {s} | {info['tasks']} | {info['events']} | "
            + " | ".join(str(info["per_class"][lab]) for lab in labels) + " |"
        )
    lines += [
        "",
        "## Test results (best setting chosen on validation macro F1)",
        "",
        "| Model | Tier | Best params | Val F1 | Test acc | Test F1 | Test AUC | "
        + " | ".join(f"F1 {lab}" for lab in labels) + " |",
        "|---|---|---|---|---|---|---|" + "---|" * len(labels),
    ]
    ranked = sorted(results.items(), key=lambda kv: -kv[1]["test"]["f1_macro"])
    for name, r in ranked:
        t = r["test"]
        lines.append(
            f"| {name} | {r['tier']} | `{json.dumps(r['best_params'])}` | {r['val']['f1_macro']:.3f} | "
            f"{t['accuracy']:.3f} | {t['f1_macro']:.3f} | {t['auc_macro']:.3f} | "
            + " | ".join(f"{t['f1_per_class'][lab]:.2f}" for lab in labels) + " |"
        )
    if ranked:
        best_name, best = ranked[0]
        lines += ["", f"## Confusion matrix on test: {best_name} (rows = true, cols = predicted)", "",
                  "| | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
        for lab, row in zip(labels, best["test"]["confusion_matrix"]):
            lines.append(f"| **{lab}** | " + " | ".join(str(v) for v in row) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Level 1 action-type classifiers")
    parser.add_argument("--dataset-root", default="./dataset", help="Dataset directory (task folders)")
    parser.add_argument("--model-dir", default="./models/actions/v1", help="Output directory")
    parser.add_argument("--granularity", choices=("fine", "coarse"), default="fine",
                        help="fine: move/click/type/press_key/hotkey/drag; coarse: pointer/click/keyboard/drag")
    parser.add_argument("--ratios", default="0.7,0.2,0.1", help="train,val,test fractions of recordings")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--models", default=",".join(GRIDS), help="Comma-separated subset of models to train")
    parser.add_argument("--load-features", action="store_true",
                        help="Reuse features.npz in --model-dir instead of re-reading the videos")
    args = parser.parse_args()

    ratios = tuple(float(r) for r in args.ratios.split(","))
    model_names = [m.strip() for m in args.models.split(",") if m.strip()]
    unknown = [m for m in model_names if m not in GRIDS]
    if unknown:
        parser.error(f"unknown models {unknown}; choose from {list(GRIDS)}")

    labels = labels_for(args.granularity)
    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    cache = model_dir / "features.npz"

    data: dict[str, np.ndarray] = {}
    if args.load_features:
        if not cache.exists():
            logger.error(f"--load-features given but {cache} does not exist")
            sys.exit(1)
        npz = np.load(cache, allow_pickle=False)
        if str(npz["granularity"]) != args.granularity:
            logger.error(f"cache was built with granularity={npz['granularity']}, not {args.granularity}")
            sys.exit(1)
        data = {k: npz[k] for k in npz.files}
        logger.info(f"Loaded cached features from {cache}")
    else:
        dataset_root = Path(args.dataset_root)
        if not dataset_root.exists():
            logger.error(f"Dataset directory not found: {dataset_root}")
            sys.exit(1)
        tasks = [t for t in discover_tasks(dataset_root) if t.video_path is not None]
        logger.info(f"Discovered {len(tasks)} tasks with video under {dataset_root.resolve()}")
        parts = dict(zip(SPLITS, task_level_split_3way(tasks, ratios=ratios, seed=args.seed)))
        (model_dir / "split.json").write_text(json.dumps(
            {s: sorted(int(t.task_id) for t in parts[s]) for s in SPLITS}, indent=1))

        for s in SPLITS:
            logger.info(f"Featurizing {s}: {len(parts[s])} tasks")
            t0 = time.time()
            X, y, tids, times = build_action_dataset(parts[s], granularity=args.granularity)
            logger.info(f"  {s}: {X.shape[0]} events x {X.shape[1]} features in {time.time() - t0:.0f}s")
            data.update({f"X_{s}": X, f"y_{s}": y, f"task_ids_{s}": tids, f"times_{s}": times})
        np.savez_compressed(cache, granularity=np.array(args.granularity), labels=np.array(labels), **data)
        logger.info(f"Feature cache saved to {cache}")

    # The split must not share recordings, and every class must be learnable.
    tid_sets = {s: set(data[f"task_ids_{s}"].tolist()) for s in SPLITS}
    assert not (tid_sets["train"] & tid_sets["val"] or tid_sets["train"] & tid_sets["test"]
                or tid_sets["val"] & tid_sets["test"]), "a recording appears in more than one split"
    missing = sorted(set(range(len(labels))) - set(data["y_train"].tolist()))
    if missing:
        logger.error(f"classes absent from the train split: {[labels[i] for i in missing]}; "
                     "use more data or --granularity coarse")
        sys.exit(1)

    meta = {
        "granularity": args.granularity,
        "labels": list(labels),
        "ratios": list(ratios),
        "seed": args.seed,
        "frame_offsets": list(FRAME_OFFSETS),
        "n_features": int(data["X_train"].shape[1]),
        "splits": {s: _split_info(data[f"task_ids_{s}"], data[f"y_{s}"], labels) for s in SPLITS},
    }
    (model_dir / "labels.json").write_text(json.dumps(
        {k: meta[k] for k in ("granularity", "labels", "frame_offsets", "n_features")}, indent=1))
    for s in SPLITS:
        info = meta["splits"][s]
        logger.info(f"{s:5s}: {info['tasks']} tasks, {info['events']} events, {info['per_class']}")

    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler().fit(data["X_train"])
    with open(model_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    X = {s: scaler.transform(data[f"X_{s}"]).astype(np.float32) for s in SPLITS}
    Y = {s: data[f"y_{s}"] for s in SPLITS}

    from app.ml.tracking import tracker

    results: dict[str, dict] = {}
    for name in model_names:
        best: tuple[float, dict, BaseClassifier, dict, float] | None = None
        for params in GRIDS[name]:
            clf = make_model(name, params, num_classes=len(labels))
            t0 = time.time()
            try:
                clf.fit(X["train"], Y["train"])
            except Exception as e:  # one failing setting shouldn't stop the run
                logger.warning(f"  {name} {params}: fit failed: {e}")
                continue
            fit_s = time.time() - t0
            val = _evaluate(clf, X["val"], Y["val"], labels)
            logger.info(f"  {name:14s} {json.dumps(params):60s} val F1={val['f1_macro']:.4f} ({fit_s:.1f}s)")
            if best is None or val["f1_macro"] > best[0]:
                best = (val["f1_macro"], params, clf, val, fit_s)
        if best is None:
            continue
        _, params, clf, val, fit_s = best
        test = _evaluate(clf, X["test"], Y["test"], labels)
        clf.save(str(model_dir / f"{name}.pkl"))
        results[name] = {"tier": clf.tier, "best_params": params, "train_time_s": round(fit_s, 2),
                         "val": val, "test": test}
        logger.info(f"{name:14s} best {json.dumps(params)}: val F1={val['f1_macro']:.4f} "
                    f"| TEST acc={test['accuracy']:.4f} F1={test['f1_macro']:.4f}")
        tracker.log_training(
            model_name=f"action_{name}", tier=clf.tier,
            metrics={"val_f1_macro": val["f1_macro"], "test_f1_macro": test["f1_macro"],
                     "test_accuracy": test["accuracy"]},
            params={**params, "granularity": args.granularity},
            tags={"level": "action"},
        )

    (model_dir / "metrics.json").write_text(json.dumps({"meta": meta, "results": results}, indent=1))
    _write_results_md(model_dir / "results.md", meta, results)
    logger.info(f"Done. Models, labels.json, split.json and results.md are in {model_dir.resolve()}")
    print((model_dir / "results.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
