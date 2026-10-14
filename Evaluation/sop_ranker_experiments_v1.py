"""Can a better ranker recover more steps? Four feature sets, one protocol.

The detector finds 90.1% of typed strings among its candidates and delivers
26.6%, so the loss is in the ranker. Its two strongest features are screen
coordinates and it never looks at the text itself, which is why terminal output
('Copying', 'updated successfully') outranks what the user typed. Each variant
adds one kind of evidence:

    A  the 13 frame features the detector ships with
    B  + lexical shape of the text (spaces, = ( / -, a known command first, ...)
    C  + a text score: char n-gram model trained across ALL applications on the
         training fold, nested out-of-fold so a training row's score never comes
         from a model that saw it
    D  + context inside the recording (rows sharing a line, vertical rank, how
         many times the same string was read)

All are scored the way the delivered SOP is: stage-1 routing, repeated reads
merged, one-to-one against the log, on run_029's folds. A second pass holds out
whole applications to test whether text evidence transfers where position did not.

    python sop_ranker_experiments_v1.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(16)

import numpy as np  # noqa: E402

from v2k import sop_detector as sd  # noqa: E402
from v2k.evaluate import new_run_dir  # noqa: E402

COMMANDS = set("""ls cd pwd mkdir rmdir rm cp mv cat head tail grep find touch echo sudo apt
apt-get yum dnf snap git python python3 pip pip3 nano vim vi chmod chown ln tar zip unzip curl
wget ssh scp docker kubectl npm node java javac gcc make cmake man less more sort uniq wc diff
export source alias history kill ps top df du free which whereis useradd adduser passwd su
systemctl service ping ifconfig ip""".split())
LEX = ["has_space", "frac_upper", "frac_punct", "starts_lower", "ends_colon", "has_eq_paren",
       "has_path", "has_flag", "has_dot", "frac_titleword", "max_word", "first_is_command",
       "is_formula"]
CTX = ["n_same_row", "y_rank", "n_reads", "rel_life", "is_lowest"]
THRESHOLDS = (0.3, 0.5)


def lexical(t: str) -> list[float]:
    n = max(len(t), 1)
    words = t.split()
    first = words[0].lower() if words else ""
    return [
        float(" " in t.strip()),
        sum(c.isupper() for c in t) / n,
        sum((not c.isalnum()) and not c.isspace() for c in t) / n,
        float(t[:1].islower()),
        float(t.rstrip().endswith(":")),
        float(any(c in t for c in "=(")),
        float("/" in t or "\\" in t),
        float(" -" in t),
        float("." in t),
        (sum(w[:1].isupper() for w in words) / len(words)) if words else 0.0,
        float(max((len(w) for w in words), default=0)),
        float(first in COMMANDS),
        float(t.lstrip().startswith("=")),
    ]


def context(X: np.ndarray, tid: np.ndarray, texts: list[str]) -> np.ndarray:
    """Features that only make sense relative to the rest of one recording."""
    y = X[:, sd.FEATURES.index("y_norm")]
    life = X[:, sd.FEATURES.index("screen_life")]
    out = np.zeros((len(X), len(CTX)), dtype=np.float32)
    order = np.argsort(tid, kind="stable")
    bounds = np.flatnonzero(np.diff(tid[order])) + 1
    for rows in np.split(order, bounds):
        yr, lr = y[rows], life[rows]
        keys = [sd.norm(texts[i]) for i in rows]
        ranks = np.argsort(np.argsort(yr)) / max(len(rows) - 1, 1)
        top = yr.max()
        for j, i in enumerate(rows):
            k = keys[j]
            out[i] = [
                float((np.abs(yr - yr[j]) < 0.01).sum() - 1),
                float(ranks[j]),
                float(sum(1 for q in keys if k and (k in q or q in k)) - 1),
                float(lr[j] / max(lr.max(), 1)),
                float(yr[j] >= top - 1e-6),
            ]
    return out


def text_scores(texts: list[str], label: np.ndarray, tid: np.ndarray, train: np.ndarray,
                score_rows: np.ndarray) -> np.ndarray:
    """P(typed | text) for score_rows, from a char n-gram model fitted on train only."""
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.linear_model import SGDClassifier

    vec = HashingVectorizer(analyzer="char_wb", ngram_range=(2, 4), n_features=2 ** 20,
                            alternate_sign=False, norm="l2", lowercase=True)
    Xtr = vec.transform([texts[i] for i in train])
    clf = SGDClassifier(loss="log_loss", alpha=2e-6, class_weight="balanced", max_iter=15,
                        tol=None, random_state=0).fit(Xtr, label[train])
    return clf.predict_proba(vec.transform([texts[i] for i in score_rows]))[:, 1]


def nested_text_feature(texts, label, tid, fold, k_outer: int) -> np.ndarray:
    """Text score for every row: test rows from a model on the training fold, training
    rows from inner folds, so no row is scored by a model that saw it."""
    out = np.zeros(len(texts), dtype=np.float32)
    tr, te = np.flatnonzero(fold != k_outer), np.flatnonzero(fold == k_outer)
    out[te] = text_scores(texts, label, tid, tr, te)
    inner = (tid[tr] * 2654435761 % 3).astype(int)          # 3 inner folds, grouped by recording
    for j in range(3):
        a, b = tr[inner != j], tr[inner == j]
        out[b] = text_scores(texts, label, tid, a, b)
    return out


def delivered(scores, tid, texts, covers, n_targets, label, t) -> dict:
    keep = scores >= t
    kd = sd._dedupe_mask(keep, scores, tid, texts)
    p, r = sd._strict(kd, covers, tid, n_targets)
    return {"threshold": t, "steps": int(kd.sum()), "precision": p, "recall": r}


def sweep(scores, tid, texts, covers, n_targets, label) -> list[dict]:
    return [delivered(scores, tid, texts, covers, n_targets, label, float(t))
            for t in np.round(np.arange(0.05, 0.96, 0.05), 2) if (scores >= t).any()]


def at_recall(curve: list[dict], r0: float) -> float | None:
    """Best precision among operating points with recall >= r0."""
    ok = [c["precision"] for c in curve if c["recall"] >= r0]
    return max(ok) if ok else None


def main() -> None:
    t0 = time.perf_counter()
    data = sd.build_candidates()
    X0, app, tid = data["X"], data["app"], data["tid"]
    texts = sd.texts_of(data)
    label, covers = sd.labels_at(data, sd.MIN_LEN)
    n_targets = int((data["want_len"] >= sd.MIN_LEN).sum())
    pred, fold_of = sd.stage1_oof()
    fold = np.array([fold_of[int(t)] for t in tid])
    apps = sorted(set(app.tolist()))
    print(f"{len(X0)} candidates, {n_targets} targets, {len(apps)} apps", flush=True)

    LX = np.array([lexical(t) for t in texts], dtype=np.float32)
    CX = context(X0, tid, texts)
    print(f"lexical + context features in {time.perf_counter() - t0:.0f}s", flush=True)

    variants = {"A": [X0], "B": [X0, LX], "C": [X0, LX, None], "D": [X0, LX, None, CX]}
    names = {"A": "13 frame features (shipped)", "B": "A + lexical shape",
             "C": "B + cross-application text score", "D": "C + recording context"}
    scores = {v: np.zeros(len(X0)) for v in variants}

    for k in range(5):
        tr, te = fold != k, fold == k
        ts = nested_text_feature(texts, label, tid, fold, k)
        for v, blocks in variants.items():
            M = np.hstack([b if b is not None else ts[:, None] for b in blocks])
            per_app = {}
            for a in apps:
                m = tr & (app == a)
                if m.sum() >= sd.MIN_ROWS and label[m].sum() >= sd.MIN_POS:
                    per_app[a] = sd._fit_app(M[m], label[m])
            routed: dict[str, list[int]] = {}
            for i in np.flatnonzero(te):
                routed.setdefault(pred[int(tid[i])][1], []).append(i)
            for a, rows in routed.items():
                if a in per_app:
                    rows = np.asarray(rows)
                    scores[v][rows] = per_app[a].predict_proba(M[rows])[:, 1]
        print(f"  fold {k} done, {time.perf_counter() - t0:.0f}s", flush=True)

    results = {"in_domain": {}, "unseen_apps": {}}
    print(f"\nIN DOMAIN - routed by stage 1, SOP as delivered")
    print(f"{'':4s}{'variant':38s}{'thr':>5s}{'steps':>7s}{'precision':>11s}{'recall':>9s}")
    base_curve = None
    for v in variants:
        curve = sweep(scores[v], tid, texts, covers, n_targets, label)
        rows = [delivered(scores[v], tid, texts, covers, n_targets, label, t) for t in THRESHOLDS]
        results["in_domain"][v] = {"name": names[v], "rows": rows, "curve": curve}
        for r in rows:
            print(f"{v:4s}{names[v]:38s}{r['threshold']:5.1f}{r['steps']:7d}"
                  f"{r['precision']:11.1%}{r['recall']:9.1%}")
        base_curve = base_curve or curve
    ref_r = results["in_domain"]["A"]["rows"][1]["recall"]
    print(f"\nprecision at recall >= {ref_r:.1%} (the shipped operating point):")
    for v in variants:
        p = at_recall(results["in_domain"][v]["curve"], ref_r)
        print(f"   {v}  {p:.1%}" if p is not None else f"   {v}  -")

    # ---- unseen applications: hold out whole applications, one pooled ranker
    print(f"\nUNSEEN APPLICATIONS - 5 folds over applications, pooled ranker, SOP as delivered")
    rng = np.random.RandomState(42)
    app_fold = {a: i % 5 for i, a in enumerate(rng.permutation(apps))}
    afold = np.array([app_fold[a] for a in app.tolist()])
    unseen = {v: np.zeros(len(X0)) for v in ("A", "C", "D")}
    for k in range(5):
        tr, te = afold != k, afold == k
        # the text model never sees the held-out applications, nor (inner folds) the row it scores
        ts = np.zeros(len(X0), dtype=np.float32)
        tr_i, te_i = np.flatnonzero(tr), np.flatnonzero(te)
        ts[te_i] = text_scores(texts, label, tid, tr_i, te_i)
        inner = (tid[tr_i] * 2654435761 % 3).astype(int)
        for j in range(3):
            ts[tr_i[inner == j]] = text_scores(texts, label, tid, tr_i[inner != j], tr_i[inner == j])
        for v in unseen:
            M = np.hstack([b if b is not None else ts[:, None] for b in variants[v]])
            unseen[v][te] = sd._fit_pooled(M[tr], label[tr]).predict_proba(M[te])[:, 1]
        print(f"  application fold {k} done, {time.perf_counter() - t0:.0f}s", flush=True)
    for v, s in unseen.items():
        rows = [delivered(s, tid, texts, covers, n_targets, label, t) for t in THRESHOLDS]
        results["unseen_apps"][v] = {"name": names[v], "rows": rows}
        for r in rows:
            print(f"{v:4s}{names[v]:38s}{r['threshold']:5.1f}{r['steps']:7d}"
                  f"{r['precision']:11.1%}{r['recall']:9.1%}")
        print(f"     ({time.perf_counter() - t0:.0f}s)", flush=True)

    out = new_run_dir("sop-ranker-experiments")
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    np.savez_compressed(out / "oof_scores.npz", **{f"score_{v}": s for v, s in scores.items()})
    print(f"\nsaved to {out}  ({time.perf_counter() - t0:.0f}s total)")


if __name__ == "__main__":
    main()
