"""Bare-video SOP detector: identify the application, then recover the typed steps.

The committed generator (v2k/sop.py) writes each step by reading
action_log.json. A user uploading a recording has no such file, and the
backend has no fallback. This module reads only the frames.

    stage 1   a saved application classifier (run_029's best model) names
              the application from visual features
    stage 2a  growth rule: an OCR region whose text extends between frames
              at the same screen position is a field being typed into; each
              such run is one candidate step
    stage 2b  that application's LightGBM ranker scores every candidate, and
              those above the threshold become "Type ..." steps

Two scoring decisions, both explained in sop_evaluation_report_v2:

  * Application labels are normalised. VideoCUA ships 107 spellings for 70
    applications (ATOM / Atom, krtia, morzillafirefox ...), so routing by the
    raw string sends a recording to a ranker that does not exist.
  * A logged string must be at least MIN_LEN normalised characters to count
    as a step. One- and two-character keystrokes ("1", "ok") are not
    instructions a reader can follow, and training against them made the
    ranker worse at finding the ones that are.

    python -m v2k.sop_detector train                 # cache, evaluate out of fold, fit, save
    python -m v2k.sop_detector detect --cached Bash 111478
    python -m v2k.sop_detector detect --video data/VideoCUA/Bash/111478/video.mp4

The action log trains and scores the rankers. It is never read at inference.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import logging
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from v2k.env import BACKEND_SNAPSHOT, CACHE, RUNS, frame_cache_dir, limit_cpu

if __name__ == "__main__":
    limit_cpu(16)

import numpy as np  # noqa: E402

log = logging.getLogger("v2k.sop_detector")

STAGE1_RUN = RUNS / "run_029_appid70"
STAGE1_COL = "ocr_native+ui+visual+cnn:mlp"          # best stage 1: 0.9449 normalised
STAGE1_BUNDLE = STAGE1_RUN / "models" / "ocr_native+ui+visual+cnn__mlp.joblib"
CANDIDATES = CACHE / f"sop_candidates_v2_{BACKEND_SNAPSHOT}.npz"   # v2 adds candidate text

MIN_TYPING = 5        # an application needs this many logged typed strings to get a ranker
MIN_LEN = 3           # a logged string shorter than this is not a step
THRESHOLD = 0.5       # the report's headline operating point
MIN_ROWS, MIN_POS = 50, 5
WORKERS = 8           # x 1 thread each, inside the 16-thread budget

CELL = 24             # positional key granularity for tracking a region, pixels
MIN_FINAL = 3         # a candidate must end at least this long
PROMPT_END = re.compile(r"[$#>]\s*$")
FEATURES = ["final_len", "growth", "frames_growing", "conf_mean", "conf_min",
            "x_norm", "y_norm", "frac_digit", "frac_alpha", "n_words",
            "after_prompt", "screen_life", "distinct_states"]

# Spellings that survive lowercasing and stripping but still name one application.
ALIAS = {
    "bravebrowser": "brave",
    "chromiumbrowser": "chromium",
    "krtia": "krita",
    "morzillafirefox": "mozillafirefox",
    "onlyofficecalender": "onlyofficecalendar",
    "onlyofficespreadsheeteditor": "onlyofficespreadsheet",
    "spyderide": "spyder",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def canon_app(name: str) -> str:
    c = norm(name)
    return ALIAS.get(c, c)


def app_dirs() -> dict[str, str]:
    """canonical name -> the cache directory name, which is already canonical."""
    return {canon_app(p.name): p.name for p in frame_cache_dir().iterdir() if p.is_dir()}


# --------------------------------------------------------------------- stage 2a

def _extends(old: str, new: str) -> bool:
    """new reads as old with more typed onto the end, allowing OCR drift."""
    a, b = norm(old), norm(new)
    if not a or len(b) <= len(a):
        return False
    if b.startswith(a):
        return True
    return difflib.SequenceMatcher(None, a, b[:len(a)]).ratio() >= 0.75


def candidates(record: dict) -> list[dict]:
    """One row per grown string, with features computed from the frames alone."""
    frames = record["frames"]
    vid = record.get("video") or {}
    W = float(vid.get("width") or 1920)
    H = float(vid.get("height") or 1080)

    live: dict[tuple[int, int], dict] = {}
    done: list[dict] = []
    for fi, frame in enumerate(frames):
        regs = []
        for r in frame.get("ocr_native_regions") or []:
            if len(r) >= 6 and str(r[0]).strip():
                regs.append((str(r[0]).strip(), float(r[1]), float(r[2]), float(r[3]),
                             float(r[4]), float(r[5])))
        prompts = [r for r in regs if PROMPT_END.search(r[0])]
        seen = {}
        for text, x1, y1, x2, y2, conf in regs:
            key = (int(x1 // CELL), int(y1 // CELL))
            mid = (y1 + y2) / 2
            after = any(x1 >= p[3] - 4 and abs((p[2] + p[4]) / 2 - mid) <= 22 for p in prompts)
            seen[key] = (text, x1, y1, conf, after)

        for key, (text, x1, y1, conf, after) in seen.items():
            cur = live.get(key)
            if cur is None:
                live[key] = {"first": text, "last": text, "confs": [conf], "frames": 1,
                             "x": x1, "y": y1, "after": after, "start": fi, "states": {text}}
            elif _extends(cur["last"], text):
                cur["last"] = text
                cur["confs"].append(conf)
                cur["frames"] += 1
                cur["after"] = cur["after"] or after
                cur["states"].add(text)
            elif norm(cur["last"]) == norm(text):
                cur["confs"].append(conf)
                cur["frames"] += 1
            else:
                done.append({**cur, "end": fi})
                live[key] = {"first": text, "last": text, "confs": [conf], "frames": 1,
                             "x": x1, "y": y1, "after": after, "start": fi, "states": {text}}
        for key in [k for k in live if k not in seen]:
            done.append({**live.pop(key), "end": fi})
    done += [{**v, "end": len(frames)} for v in live.values()]

    rows = []
    for d in done:
        text = d["last"]
        if len(norm(text)) < MIN_FINAL:
            continue
        rows.append({
            "text": text,
            "start": d["start"],
            "final_len": len(text),
            "growth": len(norm(text)) - len(norm(d["first"])),
            "frames_growing": d["frames"],
            "conf_mean": float(np.mean(d["confs"])),
            "conf_min": float(np.min(d["confs"])),
            "x_norm": d["x"] / W,
            "y_norm": d["y"] / H,
            "frac_digit": sum(c.isdigit() for c in text) / len(text),
            "frac_alpha": sum(c.isalpha() for c in text) / len(text),
            "n_words": len(text.split()),
            "after_prompt": int(d["after"]),
            "screen_life": d["end"] - d["start"],
            "distinct_states": len(d["states"]),
        })
    return rows


def logged_typing(record: dict) -> list[str]:
    return [t for seg in record.get("segments", []) for a in seg.get("actions", [])
            if (a.get("action_type") or "").upper() == "TYPING"
            and (t := ((a.get("action_params") or {}).get("text") or "").strip())]


def _matches(cand: str, want: str) -> bool:
    """Lenient on OCR drift; the length floor is applied separately, at scoring."""
    a, b = norm(cand), norm(want)
    return bool(a and b and (b in a or a in b or
                             difflib.SequenceMatcher(None, b, a).ratio() >= 0.80))


# ------------------------------------------------------------- candidate cache

def _rows_for(job: tuple[str, str]):
    """Worker: candidates, their text, and their matches for one cached recording."""
    app, path = job
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    want = logged_typing(record)
    feats, hits, texts = [], [], []
    for row in candidates(record):
        feats.append([row[f] for f in FEATURES])
        hits.append([j for j, w in enumerate(want) if _matches(row["text"], w)])
        texts.append(row["text"])
    return app, int(Path(path).stem), feats, hits, [len(norm(w)) for w in want], texts


def dedupe(order: list[int], texts) -> list[int]:
    """Collapse repeated reads of one typed string into a single step.

    The growth rule often reports the same input more than once - the field is
    re-read a frame later, or OCR drifts by a character ('sudo adduser priya',
    'sudo adduser priyal'). `order` must be best-first; each candidate is kept
    only if it does not match one already kept, so every group is shown as its
    best-scored reading. Reads nothing but the candidates' own text.

    Two alternatives were measured on run_034's out-of-fold scores and rejected.
    Showing each group's LONGEST member scored 0.2 points higher, but only
    because it swapped a correct 'priyanka' for the shell prompt line
    'user@workstation-priyankaj:~$', which the lenient match then credited.
    Grouping only readings of similar length kept fragments and full lines
    apart, and cost 6.6 points of precision.
    """
    kept: list[int] = []
    for i in order:
        if not any(_matches(texts[i], texts[j]) for j in kept):
            kept.append(i)
    return kept


def eligible_apps() -> list[str]:
    out = []
    for sub in sorted(frame_cache_dir().iterdir()):
        if not sub.is_dir():
            continue
        n = sum(len(logged_typing(json.loads(p.read_text(encoding="utf-8"))))
                for p in sub.glob("*.json"))
        if n >= MIN_TYPING:
            out.append(sub.name)
    return out


def build_candidates(rebuild: bool = False) -> dict[str, np.ndarray]:
    """Every candidate over every eligible application, with its logged matches.

    Matches are stored for every logged string, short ones included, together
    with each string's normalised length, so the MIN_LEN floor can be changed
    without re-extracting.
    """
    if CANDIDATES.exists() and not rebuild:
        with np.load(CANDIDATES, allow_pickle=False) as z:
            return {k: z[k] for k in z.files}

    apps = eligible_apps()
    jobs = [(a, str(p)) for a in apps for p in sorted((frame_cache_dir() / a).glob("*.json"))]
    log.info(f"extracting candidates: {len(apps)} applications, {len(jobs)} recordings, "
             f"{WORKERS} workers")
    X, app, tid = [], [], []
    ptr, ids = [0], []
    want_len, want_app, want_tid = [], [], []
    text_parts, text_ptr = [], [0]
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for n, (a, t, feats, hits, lens, texts) in enumerate(
                pool.map(_rows_for, jobs, chunksize=16), 1):
            base = len(want_len)
            want_len += lens
            want_app += [a] * len(lens)
            want_tid += [t] * len(lens)
            for f, h, s in zip(feats, hits, texts):
                X.append(f)
                app.append(a)
                tid.append(t)
                ids += [base + j for j in h]
                ptr.append(len(ids))
                text_parts.append(s)
                text_ptr.append(text_ptr[-1] + len(s))
            if n % 500 == 0:
                log.info(f"  {n}/{len(jobs)} recordings, {len(X)} candidates, "
                         f"{time.perf_counter() - t0:.0f}s")
    data = {
        "X": np.asarray(X, dtype=np.float32),
        "app": np.asarray(app),
        "tid": np.asarray(tid, dtype=np.int64),
        "match_ptr": np.asarray(ptr, dtype=np.int64),
        "match_ids": np.asarray(ids, dtype=np.int64),
        "want_len": np.asarray(want_len, dtype=np.int64),
        "want_app": np.asarray(want_app),
        "want_tid": np.asarray(want_tid, dtype=np.int64),
        # candidate text, packed as one string plus offsets so no pickling is needed
        "text_blob": np.asarray("".join(text_parts)),
        "text_ptr": np.asarray(text_ptr, dtype=np.int64),
    }
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CANDIDATES, **data)
    log.info(f"cached {len(X)} candidates to {CANDIDATES.name} in {time.perf_counter() - t0:.0f}s")
    return data


def texts_of(data: dict) -> list[str]:
    blob, p = str(data["text_blob"]), data["text_ptr"]
    return [blob[p[i]:p[i + 1]] for i in range(len(p) - 1)]


def _dedupe_mask(keep: np.ndarray, scores: np.ndarray, tid: np.ndarray, texts) -> np.ndarray:
    """keep, with repeated reads of one string collapsed per recording, best score first."""
    out = np.zeros(len(keep), dtype=bool)
    by_rec: dict[int, list[int]] = {}
    for i in np.flatnonzero(keep):
        by_rec.setdefault(int(tid[i]), []).append(i)
    for rows in by_rec.values():
        rows.sort(key=lambda i: -scores[i])
        out[dedupe(rows, texts)] = True
    return out


def labels_at(data: dict, min_len: int) -> tuple[np.ndarray, list[np.ndarray]]:
    """Per-candidate label, and the logged strings each candidate covers, under min_len."""
    long_enough = data["want_len"] >= min_len
    ptr, ids = data["match_ptr"], data["match_ids"]
    covers = []
    label = np.zeros(len(data["X"]), dtype=np.int8)
    for i in range(len(data["X"])):
        hit = ids[ptr[i]:ptr[i + 1]]
        hit = hit[long_enough[hit]]
        covers.append(hit)
        label[i] = 1 if len(hit) else 0
    return label, covers


def _recall(keep: np.ndarray, covers: list[np.ndarray], n_targets: int) -> float:
    got = set()
    for i in np.flatnonzero(keep):
        got.update(covers[i].tolist())
    return len(got) / max(n_targets, 1)


def _strict(keep: np.ndarray, covers: list[np.ndarray], tid: np.ndarray,
            n_targets: int) -> tuple[float, float]:
    """One-to-one: each emitted step may claim at most one logged string and vice versa.

    The growth rule often reads one typed string twice ('sudo adduser priya',
    'sudo adduser priyal'), and the default scoring credits both. Here the
    second copy is a false positive and a string typed twice needs two steps,
    which is how a detection benchmark would score it. Maximum bipartite
    matching per recording.
    """
    by_rec: dict[int, list[int]] = {}
    for i in np.flatnonzero(keep):
        by_rec.setdefault(int(tid[i]), []).append(i)
    matched = 0
    for cands in by_rec.values():
        owner: dict[int, int] = {}

        def claim(i: int, seen: set[int]) -> bool:
            for w in covers[i].tolist():
                if w in seen:
                    continue
                seen.add(w)
                if w not in owner or claim(owner[w], seen):
                    owner[w] = i
                    return True
            return False

        matched += sum(1 for i in cands if claim(i, set()))
    kept = int(keep.sum())
    return matched / max(kept, 1), matched / max(n_targets, 1)


# ------------------------------------------------------------------- stage 1

def stage1_oof() -> tuple[dict[int, tuple[str, str]], dict[int, int]]:
    """task_id -> (true app dir, predicted app dir) out of fold, and run_029's fold layout."""
    from v2k.evaluate import make_folds

    dirs = app_dirs()
    rows = list(csv.DictReader(open(STAGE1_RUN / "predictions.csv", encoding="utf-8")))
    y = np.array([r["true"] for r in rows])
    g = np.array([int(r["task_id"]) for r in rows])
    fold_of = {}
    for k, (_, te) in enumerate(make_folds(y, g, 5, 42)):
        for i in te:
            fold_of[int(g[i])] = k
    pred = {int(r["task_id"]): (dirs.get(canon_app(r["true"]), r["true"]),
                                dirs.get(canon_app(r[STAGE1_COL]), r[STAGE1_COL])) for r in rows}
    return pred, fold_of


def stage1_accuracy() -> dict[str, float]:
    rows = list(csv.DictReader(open(STAGE1_RUN / "predictions.csv", encoding="utf-8")))
    n = len(rows)
    raw = sum(r["true"] == r[STAGE1_COL] for r in rows) / n
    cn = sum(canon_app(r["true"]) == canon_app(r[STAGE1_COL]) for r in rows) / n
    return {"raw": raw, "normalised": cn, "n": n,
            "raw_labels": len({r["true"] for r in rows}),
            "canonical_labels": len({canon_app(r["true"]) for r in rows})}


# ------------------------------------------------------------- ranker features
#
# The 13 frame features leave the ranker blind to the text itself, so terminal
# output ('Copying', 'updated successfully') outranked what the user typed.
# Three more kinds of evidence, all computed from the candidates alone (run_033:
# 38.1% -> 47.9% precision at the same recall):
#   lexical   the shape of the string - spaces, = ( / -, a known command first
#   text      a char n-gram model trained across every application, so it can
#             say "this looks typed" even where screen position means nothing
#   context   where the string sits among the recording's other candidates -
#             output arrives as a block of lines, input as one line on its own

COMMANDS = set("""ls cd pwd mkdir rmdir rm cp mv cat head tail grep find touch echo sudo apt
apt-get yum dnf snap git python python3 pip pip3 nano vim vi chmod chown ln tar zip unzip curl
wget ssh scp docker kubectl npm node java javac gcc make cmake man less more sort uniq wc diff
export source alias history kill ps top df du free which whereis useradd adduser passwd su
systemctl service ping ifconfig ip""".split())
LEX = ["has_space", "frac_upper", "frac_punct", "starts_lower", "ends_colon", "has_eq_paren",
       "has_path", "has_flag", "has_dot", "frac_titleword", "max_word", "first_is_command",
       "is_formula"]
CTX = ["n_same_row", "y_rank", "n_reads", "rel_life", "is_lowest"]
ALL_FEATURES = FEATURES + LEX + ["text_score"] + CTX


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


def context(X: np.ndarray, tid: np.ndarray, texts) -> np.ndarray:
    """Features relative to the other candidates of the same recording."""
    y = X[:, FEATURES.index("y_norm")]
    life = X[:, FEATURES.index("screen_life")]
    out = np.zeros((len(X), len(CTX)), dtype=np.float32)
    order = np.argsort(tid, kind="stable")
    for rows in np.split(order, np.flatnonzero(np.diff(tid[order])) + 1):
        if not len(rows):
            continue
        yr, lr = y[rows], life[rows]
        keys = [norm(texts[i]) for i in rows]
        ranks = np.argsort(np.argsort(yr)) / max(len(rows) - 1, 1)
        top = yr.max()
        for j, i in enumerate(rows):
            k = keys[j]
            out[i] = [float((np.abs(yr - yr[j]) < 0.01).sum() - 1),
                      float(ranks[j]),
                      float(sum(1 for q in keys if k and (k in q or q in k)) - 1),
                      float(lr[j] / max(lr.max(), 1)),
                      float(yr[j] >= top - 1e-6)]
    return out


def _vectoriser():
    from sklearn.feature_extraction.text import HashingVectorizer
    # stateless: nothing to fit, so the same transform runs at training and inference
    return HashingVectorizer(analyzer="char_wb", ngram_range=(2, 4), n_features=2 ** 20,
                             alternate_sign=False, norm="l2", lowercase=True)


def fit_text_model(texts, label: np.ndarray, rows: np.ndarray):
    from sklearn.linear_model import SGDClassifier
    return SGDClassifier(loss="log_loss", alpha=2e-6, class_weight="balanced", max_iter=15,
                         tol=None, random_state=0).fit(
        _vectoriser().transform([texts[i] for i in rows]), label[rows])


def text_score(model, strings: list[str]) -> np.ndarray:
    return model.predict_proba(_vectoriser().transform(strings))[:, 1].astype(np.float32)


def _inner(tid: np.ndarray) -> np.ndarray:
    """3 inner folds, grouped by recording, stable across runs."""
    return (tid * 2654435761 % 3).astype(int)


def oof_text_scores(texts, label: np.ndarray, tid: np.ndarray, train: np.ndarray,
                    test: np.ndarray | None = None) -> np.ndarray:
    """Text score for train rows from inner folds, and for test rows from all of train,
    so no row is ever scored by a model that saw it."""
    out = np.zeros(len(texts), dtype=np.float32)
    if test is not None and len(test):
        out[test] = text_score(fit_text_model(texts, label, train), [texts[i] for i in test])
    inner = _inner(tid[train])
    for j in range(3):
        a, b = train[inner != j], train[inner == j]
        out[b] = text_score(fit_text_model(texts, label, a), [texts[i] for i in b])
    return out


def ranker_matrix(X, lex, ts, ctx) -> np.ndarray:
    return np.hstack([X, lex, ts[:, None], ctx]).astype(np.float32)


# ------------------------------------------------------------- rankers

def _fit_app(X, y):
    """One application's ranker. Kept conservative because some applications have
    only a few dozen positives: shallower trees, larger leaves, row and feature
    subsampling. Against the earlier defaults (200 trees, 31 leaves) this raised
    precision in all five folds, by 0.7 to 4.2 points, while recall moved by -0.9
    to +1.5 (run_036). The settings were fixed before scoring, not tuned on test
    folds."""
    import lightgbm as lgb
    return lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15,
                              min_child_samples=40, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, reg_lambda=1.0, verbose=-1,
                              n_jobs=8).fit(X, y)


def _fit_pooled(X, y):
    import lightgbm as lgb
    return lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31,
                              min_child_samples=20, verbose=-1, n_jobs=8).fit(X, y)


def evaluate(data: dict, min_len: int) -> dict:
    """Out-of-fold, with both stages sharing run_029's folds."""
    X, app, tid = data["X"], data["app"], data["tid"]
    label, covers = labels_at(data, min_len)
    n_targets = int((data["want_len"] >= min_len).sum())
    pred, fold_of = stage1_oof()
    fold = np.array([fold_of[int(t)] for t in tid])
    apps = sorted(set(app.tolist()))
    texts = texts_of(data)
    lex = np.array([lexical(t) for t in texts], dtype=np.float32)
    ctx = context(X, tid, texts)

    scores = {v: np.zeros(len(X)) for v in ("predicted", "oracle", "no_routing")}
    rankers_per_fold = []
    for k in range(5):
        tr, te = fold != k, fold == k
        ts = oof_text_scores(texts, label, tid, np.flatnonzero(tr), np.flatnonzero(te))
        M = ranker_matrix(X, lex, ts, ctx)
        scores["no_routing"][te] = _fit_pooled(M[tr], label[tr]).predict_proba(M[te])[:, 1]
        per_app = {}
        for a in apps:
            m = tr & (app == a)
            if m.sum() >= MIN_ROWS and label[m].sum() >= MIN_POS:
                per_app[a] = _fit_app(M[m], label[m])
        rankers_per_fold.append(len(per_app))
        idx = np.flatnonzero(te)
        for variant, pick in (("predicted", 1), ("oracle", 0)):
            routed: dict[str, list[int]] = {}
            for i in idx:
                routed.setdefault(pred[int(tid[i])][pick], []).append(i)
            for a, rows_i in routed.items():
                if a in per_app:
                    rows_i = np.asarray(rows_i)
                    scores[variant][rows_i] = per_app[a].predict_proba(M[rows_i])[:, 1]
        log.info(f"  fold {k}: {len(per_app)}/{len(apps)} applications have a ranker")

    table = []
    for variant in ("predicted", "oracle", "no_routing"):
        for t in (0.3, 0.5):
            s = scores[variant]
            keep = s >= t
            keep_d = _dedupe_mask(keep, s, tid, texts)
            sp, sr = _strict(keep, covers, tid, n_targets)
            dp, dr = _strict(keep_d, covers, tid, n_targets)
            table.append({"variant": variant, "threshold": t, "emitted": int(keep.sum()),
                          "precision": float(label[keep].sum() / max(int(keep.sum()), 1)),
                          "recall": _recall(keep, covers, n_targets),
                          "precision_strict": sp, "recall_strict": sr,
                          "emitted_dedup": int(keep_d.sum()),
                          "precision_dedup": dp, "recall_dedup": dr})
    ceiling = {"emitted": int(len(X)), "precision": float(label.mean()),
               "recall": _recall(np.ones(len(X), bool), covers, n_targets)}

    # precision-recall over thresholds, for the steps a reader actually sees
    curves = {}
    for variant in ("predicted", "oracle", "no_routing"):
        pts = []
        for t in np.round(np.arange(0.05, 0.96, 0.05), 2):
            s = scores[variant]
            keep = s >= t
            if not keep.any():
                continue
            keep_d = _dedupe_mask(keep, s, tid, texts)
            dp, dr = _strict(keep_d, covers, tid, n_targets)
            pts.append({"threshold": float(t), "emitted": int(keep_d.sum()),
                        "precision": dp, "recall": dr})
        curves[variant] = pts

    keep = scores["predicted"] >= THRESHOLD
    keep_d = _dedupe_mask(keep, scores["predicted"], tid, texts)
    per_app_rows = []
    for a in apps:
        m = app == a
        targets = int(((data["want_app"] == a) & (data["want_len"] >= min_len)).sum())
        em = int((keep_d & m).sum())
        dp, dr = _strict(keep_d & m, covers, tid, targets)
        per_app_rows.append({
            "app": a, "targets": targets, "emitted": em,
            "correct": int(round(dp * em)),
            "precision": dp if em else None,
            "recall": dr if targets else None,
        })
    per_app_rows.sort(key=lambda r: -(r["recall"] or 0) * r["targets"])

    return {"min_len": min_len, "threshold": THRESHOLD, "table": table, "ceiling": ceiling,
            "curves": curves, "per_app": per_app_rows, "rankers_per_fold": rankers_per_fold,
            "n_candidates": int(len(X)), "n_recordings": len(set(zip(app.tolist(), tid.tolist()))),
            "n_apps": len(apps), "n_targets": n_targets,
            "n_logged_all": int(len(data["want_len"])),
            "_scores": scores, "_label": label, "_fold": fold}


def fit(data: dict, min_len: int) -> dict:
    """Final rankers on every recording, for inference.

    The rankers train on out-of-fold text scores, the same way they were
    evaluated; inference uses one text model fitted on everything.
    """
    X, app, tid = data["X"], data["app"], data["tid"]
    label, _ = labels_at(data, min_len)
    texts = texts_of(data)
    everything = np.arange(len(X))
    M = ranker_matrix(X, np.array([lexical(t) for t in texts], dtype=np.float32),
                      oof_text_scores(texts, label, tid, everything), context(X, tid, texts))
    per_app = {}
    for a in sorted(set(app.tolist())):
        m = app == a
        if m.sum() >= MIN_ROWS and label[m].sum() >= MIN_POS:
            per_app[a] = _fit_app(M[m], label[m])
    pooled = _fit_pooled(M, label)
    imp = sorted(zip(ALL_FEATURES, pooled.feature_importances_.tolist()), key=lambda t: -t[1])
    return {"per_app": per_app, "pooled": pooled, "text_model": fit_text_model(texts, label, everything),
            "features": FEATURES, "all_features": ALL_FEATURES, "min_len": min_len,
            "threshold": THRESHOLD, "alias": ALIAS,
            "stage1_bundle": STAGE1_BUNDLE.relative_to(RUNS.parent).as_posix(),
            "trained": time.strftime("%Y-%m-%d %H:%M"), "n_rows": int(len(X)),
            "importance": imp}


def length_profile(data: dict) -> list[dict]:
    lens = data["want_len"]
    n = len(lens)
    bands = [(0, 0, "0"), (1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 5, "4-5"),
             (6, 9, "6-9"), (10, 10**9, "10+")]
    return [{"band": lab, "count": int(((lens >= lo) & (lens <= hi)).sum()),
             "share": float(((lens >= lo) & (lens <= hi)).mean())} for lo, hi, lab in bands
            if n]


def _report_md(res: dict, s1: dict, imp: list) -> str:
    L = [f"# SOP detector — {time.strftime('%Y-%m-%d')}", "",
         f"Stage 1 accuracy: raw labels {s1['raw']:.4f}, normalised {s1['normalised']:.4f} "
         f"({s1['raw_labels']} raw spellings -> {s1['canonical_labels']} applications).", "",
         f"{res['n_apps']} applications, {res['n_recordings']} recordings, "
         f"{res['n_candidates']} candidates, {res['n_targets']} logged strings of "
         f">= {res['min_len']} chars. Rankers per fold: {res['rankers_per_fold']}.", "",
         "**SOP as delivered**: repeated reads of one string collapsed into one step, then "
         "scored one-to-one, so a duplicate is a false positive and a string typed twice needs "
         "two steps. **Per candidate**: every emitted candidate credited if it matches any "
         "logged string - the earlier convention, kept for comparison.", "",
         "| variant | threshold | steps | precision | recall | candidates | precision | recall |",
         "|---|---|---|---|---|---|---|---|",
         "| | | *SOP as delivered* | | | *per candidate* | | |"]
    for r in res["table"]:
        L.append(f"| {r['variant']} | {r['threshold']} | {r['emitted_dedup']} | "
                 f"{r['precision_dedup']:.1%} | {r['recall_dedup']:.1%} | {r['emitted']} | "
                 f"{r['precision']:.1%} | {r['recall']:.1%} |")
    c = res["ceiling"]
    L += [f"| ceiling | - | | | | {c['emitted']} | {c['precision']:.1%} | {c['recall']:.1%} |", "",
          f"## Per application, stage 1 routing, threshold {res['threshold']}", "",
          "| application | targets | emitted | correct | precision | recall |",
          "|---|---|---|---|---|---|"]
    for r in res["per_app"][:25]:
        p = f"{r['precision']:.1%}" if r["precision"] is not None else "-"
        rc = f"{r['recall']:.1%}" if r["recall"] is not None else "-"
        L.append(f"| {r['app']} | {r['targets']} | {r['emitted']} | {r['correct']} | {p} | {rc} |")
    L += ["", "Feature importance (pooled ranker): " +
          ", ".join(f"{f} {v}" for f, v in imp[:8]), ""]
    return "\n".join(L)


# -------------------------------------------------------------------- detect

def _fmt(t: float) -> str:
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def stage1_path(bundle: dict) -> Path:
    """The stage-1 classifier a detector bundle names, relative to the harness root.

    Bundles saved before 17 Oct 2026 hold an absolute path on the machine that
    trained them; when that path does not exist here, this checkout's copy is used."""
    p = Path(bundle["stage1_bundle"])
    if not p.is_absolute():
        p = RUNS.parent / p
    return p if p.exists() else STAGE1_BUNDLE


def detect(bundle: dict, arrays: dict, record: dict, threshold: float | None = None,
           app_bundle: dict | None = None) -> dict:
    """Both stages on one recording's frames. Returns the application and the steps."""
    from v2k.predict import _rows
    from v2k.segments import build_table, pool_to_tasks

    threshold = bundle["threshold"] if threshold is None else threshold
    app_bundle = app_bundle or __import__("joblib").load(stage1_path(bundle))
    table = build_table([(arrays, record)])
    if app_bundle.get("level") == "task":
        # run_029 was trained on one row per recording, its segments averaged;
        # applying it per segment would ask a question it was never trained on.
        table = pool_to_tasks(table)
    s1 = _rows(app_bundle, table)
    best = max(s1, key=lambda r: r["confidence"] or 0)
    # The frame cache's directory names give each application's canonical spelling; a
    # deployed detector has no frame cache, and the rankers are keyed by the same names.
    dirs = app_dirs() if frame_cache_dir().is_dir() else {canon_app(a): a for a in bundle["per_app"]}
    app = dirs.get(canon_app(best["label"]), best["label"])

    ranker = bundle["per_app"].get(app)
    steps = []
    if ranker is not None:
        rows = candidates(record)
        if rows:
            X = np.array([[r[f] for f in bundle["features"]] for r in rows], dtype=np.float32)
            texts = [r["text"] for r in rows]
            if "text_model" in bundle:      # bundles from run_033 on; older ones are frame-only
                X = ranker_matrix(X, np.array([lexical(t) for t in texts], dtype=np.float32),
                                  text_score(bundle["text_model"], texts),
                                  context(X, np.zeros(len(rows), dtype=np.int64), texts))
            p = ranker.predict_proba(X)[:, 1]
            ts = np.asarray(arrays.get("timestamp", np.arange(len(record["frames"]))), float)
            above = sorted((i for i in range(len(rows)) if p[i] >= threshold), key=lambda i: -p[i])
            for i in dedupe(above, [r["text"] for r in rows]):
                steps.append({"time": float(ts[min(rows[i]["start"], len(ts) - 1)]),
                              "text": rows[i]["text"], "score": float(p[i])})
    steps.sort(key=lambda s: s["time"])
    return {"app": app, "app_label_raw": best["label"], "app_confidence": best["confidence"],
            "has_ranker": ranker is not None, "threshold": threshold, "steps": steps}


def to_markdown(result: dict, title: str, duration: float | None, source: str) -> str:
    conf = f"{result['app_confidence']:.0%}" if result["app_confidence"] is not None else "?"
    head = [f"# {title}", "",
            f"**Application:** {result['app']} (identified from the screen, {conf} confident)  ·  "
            + (f"**Recording:** {duration:.0f} s  ·  " if duration else "")
            + f"**Source:** {source}", "",
            "Steps are text the user typed, recovered from the screen alone; no action log was "
            "read. Clicks are not detected.", ""]
    if not result["has_ranker"]:
        return "\n".join(head + [f"_No step model for {result['app']}: nothing is emitted rather "
                                 f"than guessing._", ""])
    if not result["steps"]:
        return "\n".join(head + ["_No typed text was found above the threshold._", ""])
    body = ["| | time | step | confidence |", "|---:|---|---|---|"]
    for i, s in enumerate(result["steps"], 1):
        body.append(f"| {i} | {_fmt(s['time'])} | Type `{s['text']}` | {s['score']:.2f} |")
    return "\n".join(head + body + [""])


# ----------------------------------------------------------------------- CLI

def _cmd_train(args) -> None:
    import joblib

    from v2k.evaluate import new_run_dir

    data = build_candidates(rebuild=args.rebuild)
    log.info(f"{len(data['X'])} candidates, {len(data['want_len'])} logged strings")
    s1 = stage1_accuracy()
    log.info(f"stage 1: raw {s1['raw']:.4f} -> normalised {s1['normalised']:.4f}")
    res = evaluate(data, args.min_len)
    bundle = fit(data, args.min_len)
    out = new_run_dir(args.name)
    joblib.dump(bundle, out / "sop_detector.joblib", compress=3)
    # out-of-fold scores, so thresholds and scoring rules can be studied without retraining
    np.savez_compressed(out / "oof_scores.npz", app=data["app"], tid=data["tid"],
                        label=res.pop("_label"), fold=res.pop("_fold"),
                        **{f"score_{k}": v for k, v in res.pop("_scores").items()})
    res.update(stage1=s1, length_profile=length_profile(data), importance=bundle["importance"])
    (out / "results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    (out / "report.md").write_text(_report_md(res, s1, bundle["importance"]), encoding="utf-8")
    print(_report_md(res, s1, bundle["importance"]))
    print(f"saved to {out}")


def _cmd_detect(args) -> None:
    import joblib

    bundle = joblib.load(args.bundle)
    app_bundle = joblib.load(stage1_path(bundle))
    if args.cached:
        from v2k.frames import cache_paths

        npz, js = cache_paths(args.cached[0], int(args.cached[1]))
        record = json.loads(js.read_text(encoding="utf-8"))
        with np.load(npz) as z:
            arrays = {k: z[k] for k in z.files}
        title = record.get("instruction") or f"{args.cached[0]}/{args.cached[1]}"
        source = (f"cached frames of {args.cached[0]}/{args.cached[1]} - both models were fitted "
                  f"on this recording, so this is a demonstration, not an evaluation")
    else:
        from v2k.env import use_backend

        use_backend()
        from v2k.frames import Extractors, extract_video

        ex = Extractors(with_cnn="cnn" in app_bundle["blocks"])
        t0 = time.perf_counter()
        arrays, record = extract_video(Path(args.video), [], ex, grid=False, grid_ocr=False,
                                       native_ocr=True, parity_ocr="ocr" in app_bundle["blocks"])
        record.update(task_id=0, app="(input)", platform="", instruction="", keyword_label="")
        log.info(f"extracted {record['n_frames']} frames in {time.perf_counter() - t0:.0f}s")
        p = Path(args.video)
        # VideoCUA nests recordings as <task>/video/video.mp4: name it by the first real folder
        title = p.stem if p.stem.lower() != "video" else next(
            (q.name for q in p.parents if q.name and q.name.lower() != "video"), p.stem)
        source = f"bare video {Path(args.video).name}, no action log"
    result = detect(bundle, arrays, record, args.threshold, app_bundle)
    duration = (record.get("video") or {}).get("duration_seconds")
    md = to_markdown(result, title, duration, source)
    print(md)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"wrote {args.out}")


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    p = argparse.ArgumentParser(prog="python -m v2k.sop_detector", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train", help="cache candidates, evaluate out of fold, fit and save")
    t.add_argument("--min-len", type=int, default=MIN_LEN)
    t.add_argument("--name", default="sop-detector")
    t.add_argument("--rebuild", action="store_true", help="re-extract the candidate cache")
    t.set_defaults(func=_cmd_train)

    d = sub.add_parser("detect", help="write an SOP for one recording")
    d.add_argument("--bundle", required=True, help="runs/<run>/sop_detector.joblib")
    src = d.add_mutually_exclusive_group(required=True)
    src.add_argument("--video", help="a bare .mp4: frames are extracted, nothing else is read")
    src.add_argument("--cached", nargs=2, metavar=("APP", "TASK_ID"),
                     help="a recording already in the frame cache")
    d.add_argument("--threshold", type=float, default=None)
    d.add_argument("--out", help="also write the SOP to this markdown file")
    d.set_defaults(func=_cmd_detect)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
