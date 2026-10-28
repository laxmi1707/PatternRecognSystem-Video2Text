"""More evidence for the typing ranker: how a candidate's text arrived on screen.

run_037's 32 features describe a candidate's final string, where it sits and how it
compares with the recording's other candidates. They do not say whether the string was
on screen before anyone typed it, or whether it grew a few characters at a time. Both
separate typing from text the application drew: a menu label or terminal output is
often already visible elsewhere, or appears whole in one frame and then flickers in OCR.

Per candidate, from the frames alone (so inference computes them the same way):

    seen_before     the final string is already on screen, anywhere, in an earlier frame
    first_before    the first reading (what the field held when tracking began) is too
    seen_after      the final string is still on screen after the candidate ends
    growth_frac     characters added while tracked / final length
    max_jump        the largest single-frame growth / final length (1 = appeared whole)
    chars_per_s     characters added per frame of growth (1 fps)
    start_rel       when the candidate began, as a share of the recording
    n_cands         log(1 + candidates in the recording)

Round 4 (NOVELTY): most typed strings the ranker misses never grow - between two
sampled frames the whole string arrives at once, so it looks like any label. What
differs is what else arrived with it: a new page brings many new lines at once, typing
brings one.

    born_with       log(1 + other candidates that began in the same frame)
    new_frac        share of the start frame's text regions that were not in the frame before
    n_new           log(1 + number of those new regions)

candidates_ext() follows v2k.sop_detector.candidates exactly - the same rows in the
same order - and adds these keys to each row.
"""
from __future__ import annotations

import math

import numpy as np

from v2k import sop_detector as sd

EXTRA = ["seen_before", "first_before", "seen_after", "growth_frac", "max_jump",
         "chars_per_s", "start_rel", "n_cands"]
NOVELTY = ["born_with", "new_frac", "n_new"]


def candidates_ext(record: dict) -> list[dict]:
    frames = record["frames"]
    vid = record.get("video") or {}
    W = float(vid.get("width") or 1920)
    H = float(vid.get("height") or 1080)
    norm = sd.norm

    screen: list[str] = []        # per frame, every region's normalised text joined
    new_frac: list[float] = []    # per frame, share of regions not in the previous frame
    n_new: list[int] = []
    prev_keys: set = set()
    live: dict[tuple[int, int], dict] = {}
    done: list[dict] = []

    def new(text, x1, y1, conf, after, fi):
        return {"first": text, "last": text, "confs": [conf], "frames": 1, "x": x1, "y": y1,
                "after": after, "start": fi, "states": {text}, "jumps": []}

    for fi, frame in enumerate(frames):
        regs = []
        for r in frame.get("ocr_native_regions") or []:
            if len(r) >= 6 and str(r[0]).strip():
                regs.append((str(r[0]).strip(), float(r[1]), float(r[2]), float(r[3]),
                             float(r[4]), float(r[5])))
        screen.append("|".join(norm(r[0]) for r in regs))
        keys = {norm(r[0]) for r in regs}
        fresh = len(keys - prev_keys) if fi else 0
        new_frac.append(fresh / max(len(keys), 1))
        n_new.append(fresh)
        prev_keys = keys
        prompts = [r for r in regs if sd.PROMPT_END.search(r[0])]
        seen = {}
        for text, x1, y1, x2, y2, conf in regs:
            key = (int(x1 // sd.CELL), int(y1 // sd.CELL))
            mid = (y1 + y2) / 2
            after = any(x1 >= p[3] - 4 and abs((p[2] + p[4]) / 2 - mid) <= 22 for p in prompts)
            seen[key] = (text, x1, y1, conf, after)

        for key, (text, x1, y1, conf, after) in seen.items():
            cur = live.get(key)
            if cur is None:
                live[key] = new(text, x1, y1, conf, after, fi)
            elif sd._extends(cur["last"], text):
                cur["jumps"].append(len(norm(text)) - len(norm(cur["last"])))
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
                live[key] = new(text, x1, y1, conf, after, fi)
        for key in [k for k in live if k not in seen]:
            done.append({**live.pop(key), "end": fi})
    done += [{**v, "end": len(frames)} for v in live.values()]

    n = len(frames)
    first_at: dict[str, int] = {}
    last_at: dict[str, int] = {}

    def on_screen(k: str) -> tuple[int, int]:
        """First and last frame whose text contains k (n, -1 when none)."""
        if k not in first_at:
            first_at[k] = next((i for i in range(n) if k in screen[i]), n)
            last_at[k] = next((i for i in range(n - 1, -1, -1) if k in screen[i]), -1)
        return first_at[k], last_at[k]

    rows = []
    for d in done:
        text = d["last"]
        if len(norm(text)) < sd.MIN_FINAL:
            continue
        k, k0 = norm(text), norm(d["first"])
        L = max(len(k), 1)
        growth = len(k) - len(k0)
        rows.append({
            "text": text,
            "start": d["start"],
            "final_len": len(text),
            "growth": growth,
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
            "seen_before": float(on_screen(k)[0] < d["start"]),
            "first_before": float(len(k0) >= sd.MIN_FINAL and on_screen(k0)[0] < d["start"]),
            "seen_after": float(on_screen(k)[1] >= d["end"]),
            "growth_frac": growth / L,
            "max_jump": (max(d["jumps"]) / L) if d["jumps"] else 1.0,
            "chars_per_s": growth / max(d["frames"], 1),
            "start_rel": d["start"] / max(n, 1),
        })
    nc = math.log1p(len(rows))
    born = {}
    for r in rows:
        born[r["start"]] = born.get(r["start"], 0) + 1
    for r in rows:
        r["n_cands"] = nc
        r["born_with"] = math.log1p(born[r["start"]] - 1)
        f = min(r["start"], max(n - 1, 0))
        r["new_frac"] = new_frac[f] if n else 0.0
        r["n_new"] = math.log1p(n_new[f]) if n else 0.0
    return rows


# ------------------------------------------------- round-4 detector (run_039 design)
#
# Ranker input: run_037's 32 features, then EXTRA + NOVELTY, then the text score's rank
# within the recording. A candidate's score is the mean of its application's ranker
# and one pooled ranker; with no ranker for the application, the pooled score alone.

def rank_in_recording(v: np.ndarray, tid: np.ndarray) -> np.ndarray:
    out = np.zeros(len(v), dtype=np.float32)
    order = np.argsort(tid, kind="stable")
    for rows in np.split(order, np.flatnonzero(np.diff(tid[order])) + 1):
        if len(rows):
            out[rows] = np.argsort(np.argsort(-v[rows])) / max(len(rows) - 1, 1)
    return out


def matrix(X: np.ndarray, E: np.ndarray, texts, tid: np.ndarray, ts: np.ndarray) -> np.ndarray:
    lex = np.array([sd.lexical(t) for t in texts], dtype=np.float32).reshape(len(texts), len(sd.LEX))
    M = sd.ranker_matrix(X, lex, ts, sd.context(X, tid, texts))
    return np.hstack([M, E, rank_in_recording(ts, tid)[:, None]]).astype(np.float32)


def combine(per_app: np.ndarray | None, pooled: np.ndarray) -> np.ndarray:
    return pooled if per_app is None else (per_app + pooled) / 2


def fit(data: dict, E: np.ndarray, threshold: float) -> dict:
    """Final rankers on every recording, trained on out-of-fold text scores as evaluated."""
    import time
    X, app, tid = data["X"], data["app"], data["tid"]
    label, _ = sd.labels_at(data, sd.MIN_LEN)
    texts = sd.texts_of(data)
    everything = np.arange(len(X))
    M = matrix(X, E, texts, tid, sd.oof_text_scores(texts, label, tid, everything))
    per_app = {}
    for a in sorted(set(app.tolist())):
        m = app == a
        if m.sum() >= sd.MIN_ROWS and label[m].sum() >= sd.MIN_POS:
            per_app[a] = sd._fit_app(M[m], label[m])
    pooled = sd._fit_pooled(M, label)
    names = sd.ALL_FEATURES + EXTRA + NOVELTY + ["ts_rank"]
    return {"version": 2, "per_app": per_app, "pooled": pooled,
            "text_model": sd.fit_text_model(texts, label, everything),
            "features": sd.FEATURES, "extra_features": EXTRA + NOVELTY, "all_features": names,
            "min_len": sd.MIN_LEN, "threshold": threshold, "alias": sd.ALIAS,
            "stage1_bundle": sd.STAGE1_BUNDLE.relative_to(sd.RUNS.parent).as_posix(),
            "trained": time.strftime("%Y-%m-%d %H:%M"), "n_rows": int(len(X)),
            "importance": sorted(zip(names, pooled.feature_importances_.tolist()), key=lambda t: -t[1])}


def detect(bundle: dict, arrays: dict, record: dict, threshold: float | None = None,
           app_bundle: dict | None = None) -> dict:
    """v2k.sop_detector.detect for a version-2 bundle: the same stage 1, the new ranker."""
    from v2k.predict import _rows
    from v2k.segments import build_table, pool_to_tasks
    from v2k.env import frame_cache_dir

    threshold = bundle["threshold"] if threshold is None else threshold
    app_bundle = app_bundle or __import__("joblib").load(sd.stage1_path(bundle))
    table = build_table([(arrays, record)])
    if app_bundle.get("level") == "task":
        table = pool_to_tasks(table)
    s1 = _rows(app_bundle, table)
    best = max(s1, key=lambda r: r["confidence"] or 0)
    dirs = sd.app_dirs() if frame_cache_dir().is_dir() else {sd.canon_app(a): a for a in bundle["per_app"]}
    app = dirs.get(sd.canon_app(best["label"]), best["label"])

    steps = []
    rows = candidates_ext(record)
    if rows:
        X = np.array([[r[f] for f in bundle["features"]] for r in rows], dtype=np.float32)
        E = np.array([[r[f] for f in bundle["extra_features"]] for r in rows], dtype=np.float32)
        texts = [r["text"] for r in rows]
        M = matrix(X, E, texts, np.zeros(len(rows), dtype=np.int64), sd.text_score(bundle["text_model"], texts))
        ranker = bundle["per_app"].get(app)
        p = combine(ranker.predict_proba(M)[:, 1] if ranker is not None else None,
                    bundle["pooled"].predict_proba(M)[:, 1])
        ts = np.asarray(arrays.get("timestamp", np.arange(len(record["frames"]))), float)
        above = sorted((i for i in range(len(rows)) if p[i] >= threshold), key=lambda i: -p[i])
        for i in sd.dedupe(above, texts):
            steps.append({"time": float(ts[min(rows[i]["start"], len(ts) - 1)]),
                          "text": rows[i]["text"], "score": float(p[i])})
    steps.sort(key=lambda s: s["time"])
    return {"app": app, "app_label_raw": best["label"], "app_confidence": best["confidence"],
            "has_ranker": app in bundle["per_app"], "threshold": threshold, "steps": steps}
