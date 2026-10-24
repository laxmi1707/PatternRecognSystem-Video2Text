"""Does the round-4 typing ranker (run_040) hold on real uploads' frame timing?

The frame cache reads the screen at the moments the log says the user acted
(bare_vs_cached_v1.py). Round 4's new features describe what arrived on screen in one
frame, so they may lean on that timing more than the old ones. Here, for held-out
recordings with logged typing (one per application first, as ocr_fast_eval_v1), frames
are re-extracted the bare-video way - 1 fps, full-resolution native OCR, exactly as the
detector reads an upload - and both designs are retrained WITHOUT those recordings:

    old   run_037: 32 features, per-application rankers
    new   run_040: 32 + 12 features, mean of per-application and pooled rankers

Each is scored on the same recordings twice - cache frames (log-timed) and bare frames
(1 fps) - against the logged typed strings: repeats merged, one to one, threshold 0.5,
routed by the true application so only the frames differ.

    python bare_check_v2.py [N]        (default 16 recordings)
"""
from __future__ import annotations

import json
import pickle
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, frame_cache_dir, limit_cpu, use_backend  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

import combined_sop_v1 as cs  # noqa: E402
import pointer_cnn_eval_v1 as e1  # noqa: E402
import pointer_cnn_v1 as pc  # noqa: E402
from combined_sop_v4 import match_typed  # noqa: E402
from sop_ranker_experiments_v4 import EXTRAS  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402
from v2k import sop_extras as sx  # noqa: E402

BARE = CACHE / "bare_v2"
THR = 0.5


def pick(n: int) -> list[dict]:
    oof = dict(np.load(cs.OOF))
    apps = set(oof["app"].tolist())
    recs = [r for r in pickle.loads(e1.OUT.read_bytes()) if not r["train"] and r["app"] in apps
            and (frame_cache_dir() / r["app"] / f"{r['tid']}.json").exists()
            and (pc.VIDEOS / r["app"] / str(r["tid"]) / "video" / "video.mp4").exists()]
    typed = [r for r in recs if any(x["kind"] == "type" for x in cs.reference(r["app"], r["tid"], r["scale"]))]
    random.Random(0).shuffle(typed)
    seen, out = set(), []
    for r in typed:
        if r["app"] not in seen:
            seen.add(r["app"])
            out.append(r)
        if len(out) == n:
            break
    return out


def bare_record(app: str, tid: int) -> dict:
    path = BARE / f"{app}_{tid}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    from v2k.frames import extract_video
    if not hasattr(bare_record, "ex"):
        from v2k.frames import Extractors
        bare_record.ex = Extractors(with_cnn=False)
    t0 = time.perf_counter()
    _, rec = extract_video(pc.VIDEOS / app / str(tid) / "video" / "video.mp4", [], bare_record.ex,
                           grid=False, grid_ocr=False, native_ocr=True, parity_ocr=False)
    BARE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"frames": rec["frames"], "video": rec.get("video")}), encoding="utf-8")
    print(f"  extracted {app}/{tid}: {len(rec['frames'])} frames in {time.perf_counter() - t0:.0f}s", flush=True)
    return rec


def train(data, E, keep):
    """Both designs on the rows in keep (no test recording)."""
    X, app, tid = data["X"], data["app"], data["tid"]
    label, _ = sd.labels_at(data, sd.MIN_LEN)
    texts = sd.texts_of(data)
    rows = np.flatnonzero(keep)
    ts = sd.oof_text_scores(texts, label, tid, rows)
    lex = np.array([sd.lexical(t) for t in texts], dtype=np.float32)
    M = sd.ranker_matrix(X, lex, ts, sd.context(X, tid, texts))
    M2 = np.hstack([M, E, sx.rank_in_recording(ts, tid)[:, None]]).astype(np.float32)
    old, new = {}, {}
    for a in sorted(set(app.tolist())):
        m = keep & (app == a)
        if m.sum() >= sd.MIN_ROWS and label[m].sum() >= sd.MIN_POS:
            old[a] = sd._fit_app(M[m], label[m])
            new[a] = sd._fit_app(M2[m], label[m])
    pooled = sd._fit_pooled(M2[keep], label[keep])
    return sd.fit_text_model(texts, label, rows), old, new, pooled


def steps(record: dict, app: str, text_model, old, new, pooled) -> dict[str, list[dict]]:
    rows = sx.candidates_ext(record)
    out = {"old": [], "new": []}
    if not rows:
        return out
    X = np.array([[r[f] for f in sd.FEATURES] for r in rows], dtype=np.float32)
    E = np.array([[r[f] for f in sx.EXTRA + sx.NOVELTY] for r in rows], dtype=np.float32)
    texts = [r["text"] for r in rows]
    z = np.zeros(len(rows), dtype=np.int64)
    ts = sd.text_score(text_model, texts)
    M = sd.ranker_matrix(X, np.array([sd.lexical(t) for t in texts], dtype=np.float32), ts, sd.context(X, z, texts))
    M2 = sx.matrix(X, E, texts, z, ts)
    p = {"old": old[app].predict_proba(M)[:, 1] if app in old else np.zeros(len(rows)),
         "new": sx.combine(new[app].predict_proba(M2)[:, 1] if app in new else None,
                           pooled.predict_proba(M2)[:, 1])}
    for k, s in p.items():
        above = sorted((i for i in range(len(rows)) if s[i] >= THR), key=lambda i: -s[i])
        out[k] = [{"t": rows[i]["start"], "text": rows[i]["text"]} for i in sd.dedupe(above, texts)]
    return out


def main() -> None:
    use_backend()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    test = pick(n)
    print(f"{len(test)} held-out recordings with logged typing, {len({r['app'] for r in test})} applications", flush=True)
    bare = {}
    for r in test:
        bare[(r["app"], r["tid"])] = bare_record(r["app"], r["tid"])

    data = sd.build_candidates()
    with np.load(EXTRAS) as z:
        E = z["E"]
    out_tids = {(r["app"], r["tid"]) for r in test}
    keep = np.array([(a, int(t)) not in out_tids for a, t in zip(data["app"].tolist(), data["tid"].tolist())])
    print(f"training both designs without them: {int((~keep).sum())} of {len(keep)} candidates left out", flush=True)
    models = train(data, E, keep)

    tot = {f"{d}_{f}_{k}": 0 for d in ("old", "new") for f in ("cache", "bare") for k in ("steps", "ok")}
    want_n = 0
    print(f"\n{'recording':<30}{'typed':>6}   cache old/new   bare old/new   (right/steps)")
    for r in test:
        app, tid = r["app"], r["tid"]
        want = [x for x in cs.reference(app, tid, r["scale"]) if x["kind"] == "type"]
        want_n += len(want)
        cached = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
        line = f"{app + '/' + str(tid):<30}{len(want):>6}"
        for f, rec in (("cache", cached), ("bare", bare[(app, tid)])):
            got = steps(rec, app, *models)
            cells = []
            for d in ("old", "new"):
                ok = match_typed(want, got[d])
                tot[f"{d}_{f}_steps"] += len(got[d])
                tot[f"{d}_{f}_ok"] += ok
                cells.append(f"{ok}/{len(got[d])}")
            line += f"   {cells[0]:>5} {cells[1]:>5}  "
        print(line, flush=True)

    print(f"\n{want_n} logged typed strings")
    for f in ("cache", "bare"):
        for d in ("old", "new"):
            s, ok = tot[f"{d}_{f}_steps"], tot[f"{d}_{f}_ok"]
            print(f"  {f:<6}{d:<4} {s:>4} steps  {ok / max(s, 1):6.1%} real  {ok / max(want_n, 1):6.1%} found")
    (CACHE / "bare_check_v2.json").write_text(json.dumps(tot, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
