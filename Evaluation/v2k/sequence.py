"""Does the order of a recording's segments carry anything?

Every reported number pools a recording's segments by averaging them, which
throws the order away: "open, edit, save" and "save, edit, open" become the same
vector. The repository holds two models written for exactly that signal --
`tier2/workflow_lstm.py` and `tier2/workflow_transformer.py` -- but `MLService`
registers neither, so neither has ever been run. This wires them up.

The expectation is that they lose, and the reason is worth knowing: the median
recording has 3 segments against the models' `max_segments=20` default, so a
typical input is 3 real timesteps followed by 17 of zero padding. If that is
what the numbers show, it also explains why pooling to recording level beats
per-segment classification by 23% -- with three segments, the mean is a fair
summary and there is little order to lose.

Kept out of `evaluate.train` on purpose. The sequence rows are (max_segments x
feature_dim) wide, which `FeatureBuilder` cannot describe, and threading a third
level through the reported path would put every published number at risk for one
experiment.
"""
from __future__ import annotations

import csv
import json
import logging
import time
from collections import Counter
from pathlib import Path

import numpy as np

from v2k.evaluate import _quiet, make_folds, new_run_dir, score, select
from v2k.segments import FeatureBuilder, SegmentTable, load_cached, parse_feature_set, task_labels

log = logging.getLogger("v2k.sequence")

MODELS = ("workflow_lstm", "workflow_transformer")


def build(name: str, n_classes: int, feature_dim: int, max_segments: int, seed: int = 42):
    from app.ml.classifiers.tier2 import WorkflowLSTMClassifier, WorkflowTransformerClassifier

    common = dict(feature_dim=feature_dim, max_segments=max_segments,
                  num_classes=n_classes, seed=seed)
    if name == "workflow_lstm":
        return WorkflowLSTMClassifier(**common)
    if name == "workflow_transformer":
        return WorkflowTransformerClassifier(**common)
    raise SystemExit(f"unknown sequence model '{name}' (have: {', '.join(MODELS)})")


def segments_by_task(table: SegmentTable, rows: np.ndarray) -> dict[int, list[int]]:
    """Row positions of each recording's segments, in the order they happened."""
    by_task: dict[int, list[int]] = {}
    for pos, r in enumerate(rows):
        by_task.setdefault(int(table.task_id[r]), []).append(pos)
    for t, ps in by_task.items():
        ps.sort(key=lambda p: int(table.segment_index[rows[p]]))
    return by_task


def to_sequences(X: np.ndarray, by_task: dict[int, list[int]], tasks: list[int],
                 max_segments: int) -> np.ndarray:
    """(n_tasks, max_segments * dim): each recording's segments in order, zero-padded.

    A recording longer than max_segments keeps its first max_segments segments;
    at p100 = 20 on this dataset nothing is actually truncated.
    """
    dim = X.shape[1]
    out = np.zeros((len(tasks), max_segments, dim), dtype=np.float32)
    for i, t in enumerate(tasks):
        positions = by_task.get(t, [])[:max_segments]
        if positions:
            out[i, : len(positions)] = X[positions]
    return out.reshape(len(tasks), max_segments * dim)


def run(apps, label_source, feature_set, models, folds, min_tasks, max_segments,
        name, seed=42) -> Path:
    table = load_cached(apps)
    labels = task_labels(table, label_source)
    rows, y_seg, dropped = select(table, labels, min_tasks)

    by_task = segments_by_task(table, rows)
    tasks = sorted(by_task)
    y = np.array([labels[t] for t in tasks], dtype=object)
    groups = np.asarray(tasks, dtype=np.int64)
    splits = make_folds(y, groups, folds, seed)
    blocks = parse_feature_set(feature_set)
    dim = FeatureBuilder(blocks).dim

    lengths = np.array([len(v) for v in by_task.values()])
    run_dir = new_run_dir(name or "sequence")
    cfg = {
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "stage": "sequence - are the segments' order worth anything",
        "labels": label_source,
        "feature_set": feature_set,
        "models": list(models),
        "folds": len(splits),
        "min_tasks": min_tasks,
        "max_segments": max_segments,
        "feature_dim": dim,
        "seed": seed,
        "n_tasks": len(tasks),
        "n_segments": int(len(rows)),
        "n_classes": int(len(set(y))),
        "dropped_classes": dropped,
        "segments_per_recording": {
            "median": float(np.median(lengths)), "p90": float(np.percentile(lengths, 90)),
            "max": int(lengths.max()),
            "padded_fraction": round(1 - float(lengths.clip(max=max_segments).mean()) / max_segments, 3),
        },
    }
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    log.info(f"{run_dir.name}: {len(tasks)} recordings, {cfg['n_classes']} classes, "
             f"median {cfg['segments_per_recording']['median']:.0f} segments, "
             f"{cfg['segments_per_recording']['padded_fraction']:.0%} of each input is padding")

    from sklearn.preprocessing import LabelEncoder

    results = []
    for model in models:
        pred = np.empty(len(tasks), dtype=object)
        fit_seconds, failed = [], None
        started = time.time()
        for f, (tr, te) in enumerate(splits):
            train_tasks = [tasks[i] for i in tr]
            test_tasks = [tasks[i] for i in te]
            # The builder is fitted on the training recordings' segments only,
            # so no test-fold token reaches the vocabulary.
            train_rows = rows[[p for t in train_tasks for p in by_task[t]]]
            builder = FeatureBuilder(blocks).fit(table, train_rows)
            X_all = builder.transform(table, rows)
            enc = LabelEncoder().fit(y[tr])
            X_tr = to_sequences(X_all, by_task, train_tasks, max_segments)
            X_te = to_sequences(X_all, by_task, test_tasks, max_segments)
            try:
                clf = build(model, len(enc.classes_), dim, max_segments, seed)
                with _quiet():
                    t0 = time.perf_counter()
                    clf.fit(X_tr, enc.transform(y[tr]))
                    fit_seconds.append(time.perf_counter() - t0)
                    out = clf.predict(X_te)
                pred[te] = enc.inverse_transform(np.asarray(out.labels).astype(int))
            except Exception as e:
                failed = f"fold {f + 1}: {type(e).__name__}: {e}"
                log.warning(f"  {model} failed - {failed}")
                break
            log.info(f"  {model}: fold {f + 1}/{len(splits)} "
                     f"({len(train_tasks)} train / {len(test_tasks)} test recordings)")
        row = {"model": model, "error": failed or ""}
        if not failed:
            row.update(score(y, pred, groups, splits))
            row["fit_seconds"] = round(float(np.mean(fit_seconds)), 3)
        results.append(row)
        log.info(f"  {model}: {row.get('macro_f1', row['error'])} in {time.time() - started:.0f}s")

    columns = ["model", "macro_f1", "macro_f1_fold_sd", "balanced_accuracy",
               "segment_accuracy", "task_accuracy", "fit_seconds", "error"]
    with open(run_dir / "results.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    log.info(f"wrote {run_dir / 'results.csv'}")
    return run_dir


__all__ = ["MODELS", "build", "run", "segments_by_task", "to_sequences"]
