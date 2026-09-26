"""Stage 3: cross-validate the 14 classifiers on cached segment vectors.

Folds are split by task (StratifiedGroupKFold), so no recording has segments on
both sides. Everything that is fitted - the OCR TF-IDF vocabulary, the scaler,
the label encoding and the optional noise augmentation - is fitted on the
training fold only. Scores come from the pooled out-of-fold predictions.
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import logging
import time
import warnings
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from v2k.env import BACKEND_SNAPSHOT, RUNS, backend_commit, frame_cache_dir
from v2k.models import TIER, make
from v2k.segments import (FeatureBuilder, SegmentTable, load_cached, parse_feature_set, pool_to_tasks,
                          task_labels)

log = logging.getLogger("v2k.evaluate")

BASELINE = "majority"
LABEL_SOURCE_TEXT = {
    "keyword": "`keyword` - the backend's derive_activity_label, a keyword match on the task instruction",
    "app": "`app` - the application being used (ground truth, not the project's activity classes)",
}


@dataclass
class ModelResult:
    feature_set: str
    model: str
    pred: np.ndarray
    fit_seconds: list[float] = field(default_factory=list)
    predict_ms: list[float] = field(default_factory=list)
    error: str | None = None

    @property
    def tier(self) -> str:
        return TIER.get(self.model, "baseline")


def new_run_dir(name: str) -> Path:
    """runs/run_NNN_<name>: always a new folder, earlier runs are never touched."""
    RUNS.mkdir(parents=True, exist_ok=True)
    taken = [int(p.name[4:7]) for p in RUNS.glob("run_*") if p.name[4:7].isdigit()]
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in name).strip("-")
    path = RUNS / f"run_{max(taken, default=0) + 1:03d}{'_' + slug if slug else ''}"
    path.mkdir()
    return path


def select(table: SegmentTable, labels: dict[int, str], min_tasks: int):
    """Rows to use, their labels, and the classes dropped for having too few tasks.

    A class needs at least two tasks: with one, it is either absent from the
    training fold or absent from the test fold, and can never be scored.
    """
    tasks_per_class = Counter(labels.values())
    dropped = {c: n for c, n in tasks_per_class.items() if n < min_tasks}
    keep = {t for t, c in labels.items() if c not in dropped}
    rows = np.array([i for i, t in enumerate(table.task_id) if int(t) in keep], dtype=np.int64)
    y = np.array([labels[int(table.task_id[i])] for i in rows], dtype=object)
    return rows, y, dropped


def make_folds(y: np.ndarray, groups: np.ndarray, k: int, seed: int):
    from sklearn.model_selection import StratifiedGroupKFold

    k = min(k, len(np.unique(groups)))
    with warnings.catch_warnings():
        # "The least populated class in y has only N members" - the report says so instead.
        warnings.simplefilter("ignore", UserWarning)
        splitter = StratifiedGroupKFold(n_splits=k, shuffle=True, random_state=seed)
        return list(splitter.split(np.zeros(len(y)), y, groups))


@contextlib.contextmanager
def _quiet():
    """LightGBM prints per-iteration warnings to stdout; keep the console readable."""
    with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        yield


def oversample(X: np.ndarray, y: np.ndarray, cap: float, seed: int):
    """Repeat rare classes' rows until every class is within `cap`x the largest.

    The alternative would be class weights, but none of the backend's 14
    classifiers exposes them and `fit(X, y)` takes no sample_weight, so weighting
    would mean changing how the models are built - and then the scores would no
    longer describe the backend. Repeating rows is equivalent in effect for these
    learners and leaves the models untouched.

    Applied to a training fold only, after the split, so nothing leaks: a row may
    appear several times in training, never across the boundary.
    """
    counts = Counter(int(c) for c in y)
    target = max(counts.values()) / max(cap, 1.0)
    rng = np.random.default_rng(seed)
    extra: list[int] = []
    for cls, n in counts.items():
        if n >= target:
            continue
        idx = np.flatnonzero(y == cls)
        extra.extend(rng.choice(idx, size=int(round(target - n)), replace=True).tolist())
    if not extra:
        return X, y
    order = rng.permutation(len(X) + len(extra))
    X_out = np.vstack([X, X[extra]])[order]
    y_out = np.concatenate([y, y[extra]])[order]
    return X_out, y_out


def _fit_matrix(table, rows, y, blocks, augment, seed, balance=0.0):
    from sklearn.preprocessing import LabelEncoder

    builder = FeatureBuilder(blocks).fit(table, rows)
    X = builder.transform(table, rows)
    enc = LabelEncoder().fit(y)
    y_enc = enc.transform(y)
    if augment:
        from app.pipeline.augmentation import augment_features

        X, y_enc = augment_features(X, y_enc, n_augmented=augment, seed=seed)
    if balance:
        X, y_enc = oversample(X, y_enc, balance, seed)
    return builder, enc, X, y_enc


def cross_validate(table, rows, y, splits, feature_sets, model_names, augment, seed, balance=0.0):
    """Returns the results and the folds whose training part held a single class."""
    results: dict[str, dict[str, ModelResult]] = {}
    single_class_folds: set[int] = set()
    for fs in feature_sets:
        blocks = parse_feature_set(fs)
        res = {m: ModelResult(fs, m, np.empty(len(rows), dtype=object)) for m in (BASELINE, *model_names)}
        started = time.time()
        for f, (tr, te) in enumerate(splits):
            builder, enc, X_tr, y_tr = _fit_matrix(table, rows[tr], y[tr], blocks, augment, seed, balance)
            X_te = builder.transform(table, rows[te])
            res[BASELINE].pred[te] = Counter(y[tr]).most_common(1)[0][0]
            if len(enc.classes_) == 1:
                # Nothing to learn from one class; every model can only answer it.
                single_class_folds.add(f + 1)
                for m in model_names:
                    res[m].pred[te] = enc.classes_[0]
                continue
            for m in model_names:
                r = res[m]
                if r.error:
                    continue
                try:
                    clf = make(m, len(enc.classes_))
                    with _quiet():
                        t0 = time.perf_counter()
                        clf.fit(X_tr, y_tr)
                        r.fit_seconds.append(time.perf_counter() - t0)
                        out = clf.predict(X_te)
                    r.predict_ms.append(out.latency_ms / max(len(te), 1))
                    r.pred[te] = enc.inverse_transform(np.asarray(out.labels).astype(int))
                except Exception as e:
                    r.error = f"fold {f + 1}: {type(e).__name__}: {e}"
                    log.warning(f"  {fs} / {m} failed - {r.error}")
            log.info(f"  {fs}: fold {f + 1}/{len(splits)} ({len(tr)} train / {len(te)} test segments)")
        log.info(f"  {fs}: {len(model_names)} models in {time.time() - started:.0f}s")
        results[fs] = res
    return results, sorted(single_class_folds)


def score(y_true: np.ndarray, y_pred: np.ndarray, groups: np.ndarray, splits) -> dict:
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

    labels = sorted(set(y_true))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fold_f1 = [
            f1_score(y_true[te], y_pred[te], labels=sorted(set(y_true[te])), average="macro", zero_division=0)
            for _, te in splits
        ]
        s = {
            "macro_f1": f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0),
            "macro_f1_fold_sd": float(np.std(fold_f1)),
            "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
            "segment_accuracy": accuracy_score(y_true, y_pred),
        }
    hits = []
    for g in np.unique(groups):
        idx = groups == g
        vote = Counter(y_pred[idx]).most_common(1)[0][0]
        hits.append(vote == y_true[idx][0])
    s["task_accuracy"] = float(np.mean(hits))
    return {k: round(float(v), 4) for k, v in s.items()}


def _confusion(y_true, y_pred) -> tuple[list[str], np.ndarray]:
    from sklearn.metrics import confusion_matrix

    labels = sorted(set(y_true) | set(y_pred))
    return labels, confusion_matrix(y_true, y_pred, labels=labels)


def _save_confusion(path_csv: Path, y_true, y_pred) -> None:
    labels, cm = _confusion(y_true, y_pred)
    with open(path_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["true \\ predicted", *labels])
        for lab, row in zip(labels, cm):
            w.writerow([lab, *row.tolist()])


def _plot_confusion(path_png: Path, labels, cm, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    share = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    size = max(4.5, 0.55 * len(labels) + 2.5)
    fig, ax = plt.subplots(figsize=(size, size * 0.85), dpi=150)
    ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if cm[i, j]:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=7,
                        color="white" if share[i, j] > 0.6 else "black")
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(path_png)
    plt.close(fig)


def _warnings(table, rows, y, dropped, splits, summary, min_tasks, single_class_folds) -> list[str]:
    notes = []
    if single_class_folds:
        notes.append(
            f"Fold(s) {', '.join(map(str, single_class_folds))}: the training part held a single class, "
            f"so every model answered that class there. Raise --min-tasks or lower --folds."
        )
    groups = table.task_id[rows]
    n_tasks = len(np.unique(groups))
    tasks_per_class = Counter(y[np.unique(groups, return_index=True)[1]])
    if n_tasks < 100:
        per_fold = n_tasks / len(splits)
        notes.append(
            f"Only {n_tasks} tasks, about {per_fold:.0f} per test fold: one task more or less right "
            f"moves a fold's task accuracy by ~{100 / per_fold:.0f} points. Treat differences of a few "
            f"points between models as noise."
        )
    thin = {c: n for c, n in tasks_per_class.items() if n < 5}
    if thin:
        listed = ", ".join(f"{c} ({n})" for c, n in sorted(thin.items(), key=lambda x: x[1]))
        notes.append(f"Classes with fewer than 5 tasks: {listed}. Their per-class scores rest on a handful of recordings.")
    if dropped:
        listed = ", ".join(f"{c} ({n})" for c, n in dropped.items())
        notes.append(f"Left out for having fewer than {min_tasks} tasks: {listed}.")
    for fs, rows_ in summary.items():
        base = next(r for r in rows_ if r["model"] == BASELINE)
        ok = [r for r in rows_ if r["model"] != BASELINE and not r["error"]]
        if not ok:
            continue
        best = max(ok, key=lambda r: r["macro_f1"])
        margin = best["macro_f1"] - base["macro_f1"]
        if margin < 0.05:
            notes.append(
                f"{fs}: the best model ({best['model']}, macro-F1 {best['macro_f1']:.2f}) is within 0.05 of "
                f"always answering the majority class ({base['macro_f1']:.2f}). These features do not "
                f"separate these labels yet."
            )
        failed = [r["model"] for r in rows_ if r["error"]]
        if failed:
            notes.append(f"{fs}: failed and left out of the ranking - {', '.join(failed)} (error in results.csv).")
    return notes


def _write_report(run_dir, cfg, table, rows, y, dropped, splits, summary, notes, saved) -> None:
    groups = table.task_id[rows]
    first = np.unique(groups, return_index=True)[1]
    tasks_per_class = Counter(y[first])
    segs_per_class = Counter(y)
    apps = sorted({table.tasks[int(t)].app for t in np.unique(groups)})

    L = [f"# {run_dir.name}", ""]
    L.append(f"Created {cfg['created']} · backend {BACKEND_SNAPSHOT} (`{cfg['backend_commit'][:7]}`) · "
             f"frame cache `{frame_cache_dir().name}`")
    L.append("")
    by_task = cfg.get("level") == "task"
    sampled = ("" if cfg.get("sample_tasks", "all") == "all" else
               f" Sampled from the {cfg['tasks_available']} cached recordings that have a label, "
               f"drawn per class so the balance is unchanged; whole recordings, never single rows.")
    L.append(f"**Data.** {len(np.unique(groups))} tasks from {', '.join(apps)}; {len(rows)} rows "
             + ("(one per recording: its segments averaged)." if by_task else
                "(one per segment - the backend's segmentation: actions more than 2 s apart start a "
                "new segment).") + sampled)
    L.append("")
    L.append(f"**Labels.** {LABEL_SOURCE_TEXT.get(cfg['labels'], f'`{cfg['labels']}`')}. "
             + ("One label per recording, and one row per recording, so the row and the label "
                "describe the same thing." if by_task else
                "One label per task, copied to all of its segments - so a segment showing a password "
                "prompt still carries the label of the recording around it."))
    L.append("")
    L.append(f"**Evaluation.** {len(splits)}-fold cross-validation grouped by task (StratifiedGroupKFold, "
             f"seed {cfg['seed']}): "
             + ("one row per recording, so a recording is on one side by construction. "
                if by_task else "all segments of a recording are on the same side. ")
             + "The OCR TF-IDF "
             f"vocabulary, the scaler and the label encoding are fitted on each training fold only. "
             + (f"Noise augmentation x{cfg['augment']} on training folds only." if cfg["augment"] else "No augmentation."))
    L.append("")
    L.append("## Classes")
    L.append("")
    L.append("| class | tasks | segments |")
    L.append("|---|---:|---:|")
    for c, n in tasks_per_class.most_common():
        L.append(f"| {c} | {n} | {segs_per_class[c]} |")
    if dropped:
        L.append("")
        L.append("Left out (fewer than %d tasks): %s" % (cfg["min_tasks"], ", ".join(f"{c} ({n})" for c, n in dropped.items())))
    L.append("")
    L.append("## Results")
    L.append("")
    L.append("Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class "
             "equally, so it is the one to rank by when classes are unbalanced; ± is the spread across "
             "folds. Task accuracy takes a majority vote over each task's segments. `majority` always "
             "answers the training fold's most common class - a model has to beat it to be learning anything.")
    for fs, rows_ in summary.items():
        dims = FeatureBuilder(parse_feature_set(fs)).dim
        L.append("")
        L.append(f"### {fs} ({dims} dims: {' + '.join(parse_feature_set(fs))})")
        L.append("")
        L.append("| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |")
        L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
        ranked = sorted(rows_, key=lambda r: (r["model"] != BASELINE, -(r["macro_f1"] if not r["error"] else -1)))
        for r in ranked:
            if r["error"]:
                L.append(f"| {r['model']} | {r['tier']} | failed | | | | | | |")
                continue
            name = f"**{r['model']}**" if r["model"] == BASELINE else r["model"]
            L.append(
                f"| {name} | {r['tier']} | {r['macro_f1']:.3f} | {r['macro_f1_fold_sd']:.3f} | "
                f"{r['balanced_accuracy']:.3f} | {r['segment_accuracy']:.3f} | {r['task_accuracy']:.3f} | "
                f"{r['fit_seconds']:.2f} | {r['predict_ms_per_segment']:.3f} |"
            )
    if notes:
        L.append("")
        L.append("## Read before quoting a number")
        L.append("")
        L.extend(f"- {n}" for n in notes)
    L.append("")
    L.append("## Files")
    L.append("")
    L.append("- `results.csv` - the tables above, plus any error messages")
    L.append("- `predictions.csv` - every segment's true label and each model's out-of-fold prediction")
    L.append("- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model")
    for fs, path in saved:
        L.append(f"- `models/{path.name}` - {fs}, refitted on all {len(rows)} segments; load it with "
                 f"`python -m v2k predict --bundle ...`")
    L.append("- `config.json` - the exact command-line settings")
    (run_dir / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def subsample_tasks(table: SegmentTable, rows: np.ndarray, y: np.ndarray, n_tasks: int, seed: int):
    """Keep about `n_tasks` recordings, chosen to preserve the class balance.

    Sampling is by recording, never by segment: SVM, KNN and the two ensembles
    are quadratic in the number of training rows, so the full cache puts them
    out of reach, but a segment-level sample would scatter one recording across
    both sides of a fold and inflate every score. A class keeps at least two
    recordings, or it could not be scored at all.
    """
    task_of_row = table.task_id[rows]
    label_of_task: dict[int, str] = {}
    for i, t in enumerate(task_of_row):
        label_of_task.setdefault(int(t), y[i])
    if n_tasks >= len(label_of_task):
        return rows, y, len(label_of_task)

    rng = np.random.default_rng(seed)
    by_class: dict[str, list[int]] = {}
    for t, c in label_of_task.items():
        by_class.setdefault(c, []).append(t)
    share = n_tasks / len(label_of_task)
    keep: set[int] = set()
    for cls, tasks in by_class.items():
        k = min(len(tasks), max(2, round(len(tasks) * share)))
        keep.update(int(t) for t in rng.choice(sorted(tasks), size=k, replace=False))
    mask = np.array([int(t) in keep for t in task_of_row])
    return rows[mask], y[mask], len(keep)


def train(apps, label_source, feature_sets, model_names, folds, min_tasks, augment, name, save_all,
          sample_tasks=0, level="segment", balance=0.0, seed=42) -> Path:
    import joblib

    table = load_cached(apps)
    if level == "task":
        table = pool_to_tasks(table)
    elif level != "segment":
        raise SystemExit(f"unknown --level '{level}' (segment, task)")
    labels = task_labels(table, label_source)
    rows, y, dropped = select(table, labels, min_tasks)
    if len(set(y)) < 2:
        raise SystemExit(
            f"fewer than two classes have >= {min_tasks} tasks under '{label_source}' labels: "
            f"{dict(Counter(labels.values()))}. Nothing to classify."
        )
    for fs in feature_sets:
        parse_feature_set(fs)  # fail on a typo before any work
    n_all_tasks = len(np.unique(table.task_id[rows]))
    if sample_tasks:
        rows, y, n_kept = subsample_tasks(table, rows, y, sample_tasks, seed)
        if n_kept < n_all_tasks:
            log.info(f"sampling {n_kept} of {n_all_tasks} recordings, class balance kept")
    groups = table.task_id[rows]
    splits = make_folds(y, groups, folds, seed)

    run_dir = new_run_dir(name or label_source.split(":")[0])
    cfg = {
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "apps": apps or "all cached",
        "labels": label_source,
        "features": feature_sets,
        "models": model_names,
        "folds": len(splits),
        "min_tasks": min_tasks,
        "augment": augment,
        "balance": balance or "none",
        "sample_tasks": sample_tasks or "all",
        "tasks_available": int(n_all_tasks),
        "level": level,
        "seed": seed,
        "backend_snapshot": BACKEND_SNAPSHOT,
        "backend_commit": backend_commit(),
        "frame_cache": str(frame_cache_dir()),
        "n_tasks": int(len(np.unique(groups))),
        "n_segments": int(len(rows)),
    }
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    log.info(f"{run_dir.name}: {cfg['n_tasks']} tasks, {cfg['n_segments']} segments, "
             f"{len(set(y))} classes, {len(splits)} folds -> {run_dir}")

    results, single_class_folds = cross_validate(table, rows, y, splits, feature_sets, model_names,
                                                 augment, seed, balance)

    (run_dir / "confusion").mkdir()
    summary: dict[str, list[dict]] = {}
    for fs, res in results.items():
        summary[fs] = []
        for m, r in res.items():
            row = {"feature_set": fs, "model": m, "tier": r.tier, "error": r.error or ""}
            if not r.error:
                row.update(score(y, r.pred, groups, splits))
                row["fit_seconds"] = round(float(np.mean(r.fit_seconds)), 3) if r.fit_seconds else 0.0
                row["predict_ms_per_segment"] = round(float(np.mean(r.predict_ms)), 4) if r.predict_ms else 0.0
                _save_confusion(run_dir / "confusion" / f"{fs}__{m}.csv", y, r.pred)
            summary[fs].append(row)

    columns = ["feature_set", "model", "tier", "macro_f1", "macro_f1_fold_sd", "balanced_accuracy",
               "segment_accuracy", "task_accuracy", "fit_seconds", "predict_ms_per_segment", "error"]
    with open(run_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for rows_ in summary.values():
            w.writerows(rows_)

    with open(run_dir / "predictions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        keys = [(fs, m) for fs, res in results.items() for m, r in res.items() if not r.error]
        w.writerow(["task_id", "app", "segment_index", "start_s", "end_s", "true", *[f"{fs}:{m}" for fs, m in keys]])
        for j, i in enumerate(rows):
            tid = int(table.task_id[i])
            w.writerow([tid, table.tasks[tid].app, int(table.segment_index[i]), round(float(table.start[i]), 2),
                        round(float(table.end[i]), 2), y[j], *[results[fs][m].pred[j] for fs, m in keys]])

    saved: list[tuple[str, Path]] = []
    (run_dir / "models").mkdir()
    for fs, rows_ in summary.items():
        ok = [r for r in rows_ if r["model"] != BASELINE and not r["error"]]
        if not ok:
            continue
        best = max(ok, key=lambda r: r["macro_f1"])
        labels_cm, cm = _confusion(y, results[fs][best["model"]].pred)
        _plot_confusion(run_dir / "confusion" / f"{fs}__{best['model']}.png", labels_cm, cm,
                        f"{fs} / {best['model']}  (out-of-fold, macro-F1 {best['macro_f1']:.2f})")
        for r in (ok if save_all else [best]):
            blocks = parse_feature_set(fs)
            builder, enc, X, y_enc = _fit_matrix(table, rows, y, blocks, augment, seed)
            clf = make(r["model"], len(enc.classes_))
            with _quiet():
                clf.fit(X, y_enc)
            bundle = {
                "format": "v2k-bundle/1",
                "model_name": r["model"],
                "feature_set": fs,
                "blocks": blocks,
                "classes": [str(c) for c in enc.classes_],
                "label_source": label_source,
                "level": level,  # a task-level model must not be applied per segment
                "builder": builder,
                "model": clf,
                "cv_scores": {k: r[k] for k in ("macro_f1", "balanced_accuracy", "segment_accuracy", "task_accuracy")},
                "n_train_segments": int(len(rows)),
                "backend_snapshot": BACKEND_SNAPSHOT,
                "backend_commit": backend_commit(),
                "created": cfg["created"],
            }
            path = run_dir / "models" / f"{fs}__{r['model']}.joblib"
            joblib.dump(bundle, path, compress=3)
            saved.append((fs, path))

    notes = _warnings(table, rows, y, dropped, splits, summary, min_tasks, single_class_folds)
    _write_report(run_dir, cfg, table, rows, y, dropped, splits, summary, notes, saved)

    for fs, rows_ in summary.items():
        log.info(f"\n{fs}")
        ranked = sorted(rows_, key=lambda r: (r["model"] != BASELINE, -(r.get("macro_f1") or -1)))
        for r in ranked:
            if r["error"]:
                log.info(f"  {r['model']:<14} failed")
            else:
                log.info(f"  {r['model']:<14} macro-F1 {r['macro_f1']:.3f}  bal-acc {r['balanced_accuracy']:.3f}  "
                         f"task-acc {r['task_accuracy']:.3f}")
    for n in notes:
        log.info(f"note: {n}")
    log.info(f"\nreport: {run_dir / 'report.md'}")
    return run_dir
