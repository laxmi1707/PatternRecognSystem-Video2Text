"""Stage A: a grid search over the hyperparameters the backend's classes expose.

The backend's constructors already take their hyperparameters as arguments --
`LightGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1)` and so on
-- but nothing ever passes them, so every number reported so far comes from the
library defaults. This searches them, and nothing in the team's code changes.

Selection is on the pooled out-of-fold macro-F1 of the same StratifiedGroupKFold
split `train` uses, with the same seed. There is no separate test set to leak
into: a configuration is chosen on cross-validated folds and reported as such.

Two stages, because loading the frame cache costs three minutes and the fits
themselves cost seconds:

    prepare   load the cache once, build each fold's matrices once, save them
    shard     load those matrices in a second, run 1/N of the grid
    collect   merge the shards into one table

Feature building is fold-local and hyperparameter-independent, so doing it once
up front is the same computation the per-config loop would have repeated.
"""
from __future__ import annotations

import csv
import json
import logging
import time
from collections import Counter
from itertools import product
from pathlib import Path

import numpy as np

from v2k.evaluate import _fit_matrix, _quiet, make_folds, new_run_dir, score, select
from v2k.segments import load_cached, parse_feature_set, pool_to_tasks, task_labels

log = logging.getLogger("v2k.tune")

# One grid per model. Each grid contains the library default, so the report can
# state what tuning actually bought rather than only what the best config scored.
GRIDS: dict[str, dict[str, list]] = {
    "lightgbm": {
        "n_estimators": [100, 300, 600],
        "max_depth": [4, 6, 10],
        "learning_rate": [0.03, 0.1, 0.2],
    },
    "xgboost": {
        "n_estimators": [100, 300, 600],
        "max_depth": [4, 6, 10],
        "learning_rate": [0.03, 0.1, 0.2],
    },
    "random_forest": {
        "n_estimators": [100, 300, 600],
        "max_depth": [10, 20, 40],
    },
    "stacking": {
        # The base list is an argument of the backend's StackingClassifier, so
        # varying it stays inside its API rather than redefining the model.
        "bases": ["svm+random_forest+mlp", "svm+random_forest+mlp+lightgbm",
                  "random_forest+mlp+lightgbm", "svm+lightgbm+xgboost"],
        "meta_C": [0.1, 1.0, 10.0],
    },
}

DEFAULTS: dict[str, dict] = {
    "lightgbm": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1},
    "xgboost": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1},
    "random_forest": {"n_estimators": 100, "max_depth": 20},
    "stacking": {"bases": "svm+random_forest+mlp", "meta_C": 1.0},
}


def build(model: str, n_classes: int, params: dict):
    """The backend's own class, with the searched arguments passed in."""
    from app.ml.classifiers.tier1.lightgbm_clf import LightGBMClassifier
    from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
    from app.ml.classifiers.tier1.svm import SVMClassifier
    from app.ml.classifiers.tier1.xgboost_clf import XGBoostClassifier
    from app.ml.classifiers.tier2 import MLPClassifier
    from app.ml.classifiers.tier3 import StackingClassifier

    base = {
        "svm": lambda: SVMClassifier(),
        "random_forest": lambda: RandomForestClassifier(),
        "mlp": lambda: MLPClassifier(num_classes=n_classes),
        "lightgbm": lambda: LightGBMClassifier(),
        "xgboost": lambda: XGBoostClassifier(),
    }
    if model == "lightgbm":
        return LightGBMClassifier(**params)
    if model == "xgboost":
        return XGBoostClassifier(**params)
    if model == "random_forest":
        return RandomForestClassifier(**params)
    if model == "stacking":
        return StackingClassifier(
            base_estimators=[base[b]() for b in params["bases"].split("+")],
            meta_C=params["meta_C"],
        )
    raise SystemExit(f"no grid for '{model}' (have: {', '.join(GRIDS)})")


def expand(models: list[str]) -> list[dict]:
    """Every combination in each model's grid, as a flat numbered list."""
    grid: list[dict] = []
    for m in models:
        if m not in GRIDS:
            raise SystemExit(f"no grid for '{m}' (have: {', '.join(GRIDS)})")
        keys = list(GRIDS[m])
        for values in product(*(GRIDS[m][k] for k in keys)):
            params = dict(zip(keys, values))
            grid.append({"model": m, "params": params, "is_default": params == DEFAULTS[m]})
    for i, c in enumerate(grid):
        c["id"] = i
    return grid


def prepare(apps, label_source, feature_set, models, folds, min_tasks, augment,
            level, balance, name, seed, split="grouped") -> Path:
    """Load the cache once and freeze the folds, so the shards start instantly."""
    table = load_cached(apps)
    if level == "task":
        table = pool_to_tasks(table)
    elif level != "segment":
        raise SystemExit(f"unknown --level '{level}' (segment, task)")

    labels = task_labels(table, label_source)
    rows, y, dropped = select(table, labels, min_tasks)
    groups = table.task_id[rows]
    if split == "random":
        # Deliberately leaky, for the comparison only: segments of one recording
        # land on both sides, so the test fold is scored on near-copies of its own
        # training rows. This is what an ungrouped train_test_split does.
        from sklearn.model_selection import StratifiedKFold

        splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
        splits = list(splitter.split(np.zeros(len(y)), y))
    elif split == "grouped":
        splits = make_folds(y, groups, folds, seed)
    else:
        raise SystemExit(f"unknown --split '{split}' (grouped, random)")
    blocks = parse_feature_set(feature_set)

    run_dir = new_run_dir(name or "tune")
    grid = expand(models)
    (run_dir / "grid.json").write_text(json.dumps(grid, indent=2), encoding="utf-8")

    arrays: dict[str, np.ndarray] = {
        "y": np.asarray(y, dtype=str),
        "groups": np.asarray(groups),
    }
    started = time.time()
    for f, (tr, te) in enumerate(splits):
        builder, enc, X_tr, y_tr = _fit_matrix(table, rows[tr], y[tr], blocks, augment, seed, balance)
        arrays[f"X_tr_{f}"] = X_tr.astype(np.float32)
        arrays[f"y_tr_{f}"] = np.asarray(y_tr, dtype=np.int32)
        arrays[f"X_te_{f}"] = builder.transform(table, rows[te]).astype(np.float32)
        arrays[f"classes_{f}"] = np.asarray(enc.classes_, dtype=str)
        arrays[f"te_{f}"] = np.asarray(te, dtype=np.int64)
    np.savez_compressed(run_dir / "folds.npz", **arrays)

    cfg = {
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "stage": "A - hyperparameter grid search",
        "labels": label_source,
        "feature_set": feature_set,
        "models": models,
        "folds": len(splits),
        "level": level,
        "split": split,
        "balance": balance or "none",
        "augment": augment,
        "min_tasks": min_tasks,
        "seed": seed,
        "n_tasks": int(len(np.unique(groups))),
        "n_rows": int(len(rows)),
        "n_classes": int(len(set(y))),
        "dropped_classes": dropped,
        "configs": len(grid),
    }
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    log.info(f"{run_dir.name}: {cfg['n_tasks']} tasks, {cfg['n_classes']} classes, "
             f"{len(splits)} folds frozen in {time.time() - started:.0f}s")
    log.info(f"{len(grid)} configurations over {', '.join(models)} -> {run_dir}")
    return run_dir


def _folds(run_dir: Path):
    d = np.load(run_dir / "folds.npz")
    n = sum(1 for k in d.files if k.startswith("X_tr_"))
    folds = [(d[f"X_tr_{f}"], d[f"y_tr_{f}"], d[f"X_te_{f}"], d[f"classes_{f}"], d[f"te_{f}"])
             for f in range(n)]
    return d["y"], d["groups"], folds


def evaluate_config(cfg: dict, y, groups, folds) -> tuple[dict, np.ndarray | None]:
    """One configuration, cross-validated on the frozen folds.

    Returns its row and its out-of-fold predictions; the predictions are kept
    because a headline macro-F1 cannot say whether a rare class recovered, and
    re-fitting the chosen configuration later just to find out wastes the run.
    """
    pred = np.empty(len(y), dtype=object)
    fit_seconds: list[float] = []
    row = {"id": cfg["id"], "model": cfg["model"], "default": "yes" if cfg["is_default"] else "",
           **{f"p_{k}": v for k, v in cfg["params"].items()}}
    try:
        for X_tr, y_tr, X_te, classes, te in folds:
            clf = build(cfg["model"], len(classes), cfg["params"])
            with _quiet():
                t0 = time.perf_counter()
                clf.fit(X_tr, y_tr)
                fit_seconds.append(time.perf_counter() - t0)
                out = clf.predict(X_te)
            pred[te] = classes[np.asarray(out.labels).astype(int)]
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"
        return row, None
    row.update(score(y, pred, groups, list((np.empty(0, dtype=np.int64), te) for *_, te in folds)))
    row["fit_seconds"] = round(float(np.mean(fit_seconds)), 3)
    row["error"] = ""
    return row, pred


COLUMNS = ["id", "model", "default", "macro_f1", "macro_f1_fold_sd", "balanced_accuracy",
           "segment_accuracy", "task_accuracy", "fit_seconds",
           "p_n_estimators", "p_max_depth", "p_learning_rate", "p_bases", "p_meta_C", "error"]


def run_shard(run_dir: Path, shard: int, n_shards: int, ids: list[int] | None = None) -> Path:
    """Configurations shard, shard+n, shard+2n ... so any shard sees a mix of costs."""
    grid = json.loads((run_dir / "grid.json").read_text(encoding="utf-8"))
    mine = [c for c in grid if c["id"] % n_shards == shard and (ids is None or c["id"] in ids)]
    y, groups, folds = _folds(run_dir)

    out_dir = run_dir / "shards"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"shard_{shard}.csv"
    preds: dict[str, np.ndarray] = {}
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for n, cfg in enumerate(mine, 1):
            t0 = time.time()
            row, pred = evaluate_config(cfg, y, groups, folds)
            w.writerow(row)
            fh.flush()
            if pred is not None:
                preds[f"pred_{cfg['id']}"] = np.asarray(pred, dtype=str)
            log.info(f"  [{shard}] {n}/{len(mine)} {cfg['model']} {cfg['params']} -> "
                     f"{row.get('macro_f1', row.get('error', '?'))} ({time.time() - t0:.0f}s)")
    if preds:
        np.savez_compressed(out_dir / f"preds_{shard}.npz", y=np.asarray(y, dtype=str), **preds)
    return out


def _per_class_section(run_dir: Path, ok: list[dict]) -> list[str]:
    """Per-class F1 for the best configuration of each model.

    A headline macro-F1 can rise while the rare class it was supposed to help
    stays at zero, so the winner is reported class by class or not at all.
    """
    from sklearn.metrics import f1_score

    store: dict[int, np.ndarray] = {}
    y = None
    for path in sorted((run_dir / "shards").glob("preds_*.npz")):
        d = np.load(path)
        y = d["y"] if y is None else y
        for key in d.files:
            if key.startswith("pred_"):
                store[int(key[5:])] = d[key]
    if not store or y is None:
        return ["", "_No stored predictions in this run; per-class F1 needs a re-run._"]

    best = {}
    for r in ok:
        best.setdefault(r["model"], r)
    winners = {m: r for m, r in best.items() if int(r["id"]) in store}
    if not winners:
        return ["", "_Stored predictions do not cover the winning configurations._"]

    classes = sorted(set(y.tolist()))
    counts = Counter(y.tolist())
    order = sorted(winners, key=lambda m: -float(winners[m]["macro_f1"]))
    lines = ["", "## Per-class F1 of each model's best configuration", "",
             "| class | recordings | " + " | ".join(order) + " |",
             "|---" * (len(order) + 2) + "|"]
    f1s = {m: dict(zip(classes, f1_score(y, store[int(winners[m]["id"])], labels=classes,
                                         average=None, zero_division=0))) for m in order}
    for c in sorted(classes, key=lambda c: -counts[c]):
        cells = " | ".join(f"{f1s[m][c]:.3f}" for m in order)
        lines.append(f"| {c} | {counts[c]} | {cells} |")
    return lines


def collect(run_dir: Path) -> Path:
    """Merge the shards, rank by macro-F1, and say what tuning bought per model."""
    rows: list[dict] = []
    for path in sorted((run_dir / "shards").glob("shard_*.csv")):
        with open(path, newline="", encoding="utf-8") as fh:
            rows.extend(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"no shard results under {run_dir / 'shards'}")
    ok = [r for r in rows if not r["error"]]
    ok.sort(key=lambda r: -float(r["macro_f1"]))

    merged = run_dir / "tuning.csv"
    with open(merged, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(ok + [r for r in rows if r["error"]])

    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    lines = [f"# Hyperparameter search - {run_dir.name}", "",
             f"{cfg['n_tasks']} recordings, {cfg['n_classes']} classes, {cfg['folds']} folds, "
             f"feature set `{cfg['feature_set']}`, level `{cfg['level']}`, "
             f"balance `{cfg['balance']}`, labels `{cfg['labels']}`, "
             f"split `{cfg.get('split', 'grouped')}`.", "",
             f"{len(rows)} configurations, {len(rows) - len(ok)} failed. Selection is on the pooled "
             "out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so "
             "nothing is chosen on data a reported score is computed from.", "",
             "## What tuning bought", "",
             "| model | default macro-F1 | best macro-F1 | gain | best configuration |",
             "|---|---|---|---|---|"]
    for model in sorted({r["model"] for r in ok}):
        got = [r for r in ok if r["model"] == model]
        best = got[0]
        base = next((r for r in got if r["default"] == "yes"), None)
        params = ", ".join(f"{k[2:]}={v}" for k, v in best.items()
                           if k.startswith("p_") and v not in ("", None))
        d = float(base["macro_f1"]) if base else float("nan")
        gain = f"{float(best['macro_f1']) - d:+.4f}" if base else "-"
        lines.append(f"| {model} | {d:.4f} | {float(best['macro_f1']):.4f} | {gain} | {params} |")

    lines += ["", "## Top 15 overall", "",
              "| rank | model | macro-F1 | fold sd | balanced acc | task acc | fit s | configuration |",
              "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(ok[:15], 1):
        params = ", ".join(f"{k[2:]}={v}" for k, v in r.items()
                           if k.startswith("p_") and v not in ("", None))
        lines.append(f"| {i} | {r['model']} | {float(r['macro_f1']):.4f} | "
                     f"{float(r['macro_f1_fold_sd']):.4f} | {float(r['balanced_accuracy']):.4f} | "
                     f"{float(r['task_accuracy']):.4f} | {float(r['fit_seconds']):.1f} | {params} |")
    lines += _per_class_section(run_dir, ok)
    if len(rows) - len(ok):
        lines += ["", "## Failures", ""]
        lines += [f"- `{r['model']}` id {r['id']}: {r['error']}" for r in rows if r["error"]]

    report = run_dir / "tuning.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info(f"wrote {merged} and {report}")
    print("\n".join(lines[:40]))
    return report


__all__ = ["GRIDS", "build", "collect", "expand", "prepare", "run_shard"]
