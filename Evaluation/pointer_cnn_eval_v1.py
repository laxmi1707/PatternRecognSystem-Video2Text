"""Clicks on all 87 applications, with the pointer CNN beside templates and self-match.

Until now clicks were measured on 5 programming tools. This samples every
application in data/VideoCUA - up to PER_APP training and PER_APP held-out
recordings each (split by task id, as everywhere) - and records, for every frame
pair at 5 fps, three independent ways of seeing the pointer:

    template     pointer_tracker_v1 templates inside small changed regions
    self         a small changed region matching itself one frame earlier
    cnn          pointer_cnn_v1 scored over each small changed region; the best
                 hotspot and its probability

Pointer moves are then formed under four rules - template; template + self (the
delivered click_sop_v3 rule); cnn; template, else cnn, else self - and each is
carried through the same chain: stops (global rule), the reaction filter fitted
on that rule's training-recording stops (threshold keeping 90% of training
recall), OCR names within 70 px, repeats merged. Scored on held-out recordings
against the logged clicks; names against v2k/sop.py's label where the frame cache
has full-resolution OCR (70 applications), position only for the other 17.

    python pointer_cnn_eval_v1.py extract     decode the sample -> cache/pointer_cnn_eval_v1.pkl
    python pointer_cnn_eval_v1.py eval        stops, filter, names, per-application table
"""
from __future__ import annotations

import collections
import json
import pickle
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, frame_cache_dir, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

import pointer_cnn_v1 as pc  # noqa: E402

OUT = CACHE / "pointer_cnn_eval_v1.pkl"
OCR = CACHE / "pointer_cnn_eval_v1_ocr.pkl"
PER_APP = 12
FPS = 5.0
WORKERS = 6
CNN_STRIDE = 3          # logical px between hotspot candidates
CNN_KEEP = 0.5          # store a CNN hit at or above this probability
RULES = ["template", "template+self", "cnn", "cnn@0.8", "template>cnn>self", "template>cnn@0.8>self"]
NEAR, BEFORE, AFTER = 40, 2.0, 0.3
MERGE_S = 2.0


def sample() -> list[tuple[str, int]]:
    rng = random.Random(1)
    recs = pc.recordings()
    jobs = []
    for app in sorted({a for a, _ in recs}):
        for split in (True, False):
            pool = [r for r in recs if r[0] == app and pc.is_train(r[1]) == split]
            jobs += rng.sample(pool, min(PER_APP, len(pool)))
    return jobs


# ---------------------------------------------------------------- extraction

_state = {}


def _init():
    import cv2
    import torch
    cv2.setNumThreads(1)
    torch.set_num_threads(2)
    import pointer_tracker_v1 as pt
    _state["templates"] = pt.load_templates()
    _state["cnn"] = pc.load_model()


def cnn_hit(gl: np.ndarray, blobs: list[tuple[float, float, float, float]]):
    """Best (p, x, y) over hotspot candidates around each small changed region, logical px."""
    import torch
    crops, where = [], []
    H, W = gl.shape
    for bx, by, bw, bh in blobs[:12]:
        for cy in np.arange(by - 4, by + bh + 4, CNN_STRIDE):
            for cx in np.arange(bx - 4, bx + bw + 4, CNN_STRIDE):
                x0, y0 = int(cx) - pc.HOT, int(cy) - pc.HOT
                if x0 < 0 or y0 < 0 or x0 + pc.SIZE > W or y0 + pc.SIZE > H:
                    continue
                crops.append(gl[y0:y0 + pc.SIZE, x0:x0 + pc.SIZE])
                where.append((int(cx), int(cy)))
    if not crops:
        return None
    with torch.no_grad():
        p = torch.sigmoid(_state["cnn"](pc.to_tensor(np.stack(crops))).squeeze(1)).numpy()
    k = int(p.argmax())
    return (float(p[k]), *where[k]) if p[k] >= CNN_KEEP else None


def _extract_one(job):
    import cv2
    import pointer_selfmatch_v2 as ps
    from pointer_motion_v1 import DIFF
    app, tid = job
    ev = pc.events(app, tid)
    video = pc.VIDEOS / app / str(tid) / "video" / "video.mp4"
    cap = cv2.VideoCapture(str(video))
    W, H = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    native = cap.get(cv2.CAP_PROP_FPS) or 30
    s = pc.coord_scale(ev, W)
    step = max(1, int(round(native / FPS)))
    prev, fr, i = None, [], 0
    while True:
        if not cap.grab():
            break
        if i % step == 0:
            ok, f = cap.retrieve()
            if ok:
                g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                t = i / native
                if prev is not None and prev.shape == g.shape:
                    hit, selfs, large = ps.step(g, prev, _state["templates"], s)
                    m = cv2.dilate((cv2.absdiff(g, prev) > DIFF).astype(np.uint8), np.ones((5, 5), np.uint8))
                    n, _, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
                    small = [(x / s, y / s, w / s, h / s) for x, y, w, h, a in st[1:]
                             if a >= 15 and w <= 70 * s and h <= 70 * s]
                    c = None
                    if small:
                        gl = g if s == 1.0 else cv2.resize(g, (int(W / s), int(H / s)), interpolation=cv2.INTER_AREA)
                        c = cnn_hit(gl, small)
                    fr.append((t, None if hit is None else (hit[1] / s, hit[2] / s),
                               [(x / s, y / s) for _, x, y in selfs], c,
                               [(x / s, y / s, w / s, h / s, a / (W * H)) for x, y, w, h, a in large]))
                prev = g
        i += 1
    cap.release()
    return {"app": app, "tid": tid, "train": pc.is_train(tid), "fps": FPS, "scale": s,
            "clicks": [(e["t"], e["x"], e["y"]) for e in ev if e["type"] in pc.CLICKS], "frames": fr}


def extract() -> None:
    jobs = sample()
    print(f"{len(jobs)} recordings from {len({a for a, _ in jobs})} applications", flush=True)
    t0 = time.perf_counter()
    recs = []
    with ProcessPoolExecutor(max_workers=WORKERS, initializer=_init) as ex:
        for k, r in enumerate(ex.map(_extract_one, jobs, chunksize=2), 1):
            recs.append(r)
            if k % 100 == 0:
                print(f"  {k}/{len(jobs)}, {time.perf_counter() - t0:.0f}s", flush=True)
    OUT.write_bytes(pickle.dumps(recs))
    print(f"-> {OUT.name}, {time.perf_counter() - t0:.0f}s")


# ---------------------------------------------------------------- evaluation

def moves(r: dict, rule: str) -> list[tuple[float, float, float]]:
    cnt = collections.Counter((int(x // 8), int(y // 8)) for _, _, ss, _, _ in r["frames"] for x, y in ss)
    bad = {c for c, n in cnt.items() if n >= 3}
    out = []
    for t, tmpl, ss, c, _ in r["frames"]:
        selfs = [(x, y) for x, y in ss if (int(x // 8), int(y // 8)) not in bad]
        pick = None
        if rule.startswith("template") and tmpl is not None:
            pick = tmpl
        need = 0.8 if "@0.8" in rule else 0.0
        if pick is None and "cnn" in rule and c is not None and c[0] >= need:
            pick = (c[1], c[2])
        if pick is None and rule.endswith("self") and selfs:
            pick = selfs[0]
        if pick is not None:
            out.append((t, *pick))
    return out


def stops(r: dict, rule: str) -> list[tuple[float, float, float, float]]:
    mv = moves(r, rule)
    dt = 1.0 / r["fps"]
    out = []
    for j, (t, x, y) in enumerate(mv):
        nxt = mv[j + 1][0] if j + 1 < len(mv) else None
        if nxt is None or nxt - t > 1.5 * dt:
            out.append((t, x, y, (nxt - t) if nxt is not None else 10.0))
    return out


def features(r: dict, stop) -> list[float]:
    """pointer_reaction_v1.features on this cache's layout."""
    import pointer_reaction_v1 as pr
    return pr.features({"iv": [(t, lg) for t, _, _, _, lg in r["frames"]]}, stop)


def match(clicks, st, keep):
    used, hit = {}, 0
    for ci, (ct, cx, cy) in enumerate(clicks):
        cands = [j for j, (ts, x, y, _) in enumerate(st) if keep[j] and j not in used
                 and ct - BEFORE <= ts <= ct + AFTER and np.hypot(x - cx, y - cy) <= NEAR]
        if cands:
            j = min(cands, key=lambda j: abs(st[j][0] - ct))
            used[j] = ci
            hit += 1
    return hit, used


def reference_names(app: str, tid: int, s: float) -> dict | None:
    """{(t, x, y): v2k/sop.py's name} for each logged click; None without a frame cache."""
    import click_labels_v1 as cl
    js = frame_cache_dir() / app / f"{tid}.json"
    if not js.exists():
        return None
    rec = json.loads(js.read_text(encoding="utf-8"))
    frames = rec["frames"]
    out = {}
    for seg in rec["segments"]:
        refs = seg["keyframes"]
        for pos, a in enumerate(seg["actions"]):
            prm = a.get("action_params") or {}
            if (a.get("action_type") or "").upper() in pc.CLICKS and prm.get("x") is not None \
                    and a.get("timestamp") is not None:
                ref = refs[min(pos, len(refs) - 1)] if refs else None
                regions = frames[ref].get("ocr_native_regions") if ref is not None else []
                key = (round(float(a["timestamp"]), 2), round(float(prm["x"])), round(float(prm["y"])))
                out[key] = cl.label_at(regions, float(prm["x"]) * s, float(prm["y"]) * s, cl.NEAR_PX * s)
    return out


def _ocr_worker_init():
    from v2k.env import use_backend
    use_backend()
    from app.pipeline.ocr_extractor import OCRExtractor
    import torch
    torch.set_num_threads(4)
    _state["ocr"] = OCRExtractor()


def _ocr_one(job):
    """OCR regions around each stop of one recording, logical coordinates."""
    import cv2
    app, tid, s, pts = job
    cap = cv2.VideoCapture(str(pc.VIDEOS / app / str(tid) / "video" / "video.mp4"))
    out = {}
    for t, x, y in pts:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        regs = []
        if ok:
            X, Y = x * s, y * s
            x0, y0 = int(max(0, X - 260 * s)), int(max(0, Y - 150 * s))
            crop = f[y0:int(min(f.shape[0], Y + 150 * s)), x0:int(min(f.shape[1], X + 260 * s))]
            regs = [[g.text, (g.bbox[0] + x0) / s, (g.bbox[1] + y0) / s, (g.bbox[2] + x0) / s,
                     (g.bbox[3] + y0) / s, g.confidence] for g in _state["ocr"].extract_text(crop).regions]
        out[(app, tid, t, x, y)] = regs
    cap.release()
    return out


def evaluate() -> None:
    import click_labels_v1 as cl
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    recs = pickle.loads(OUT.read_bytes())
    tr = [r for r in recs if r["train"]]
    te = [r for r in recs if not r["train"]]
    n_clicks = sum(len(r["clicks"]) for r in te)
    print(f"{len(recs)} recordings, {len({r['app'] for r in recs})} applications; held-out {len(te)} "
          f"recordings with {n_clicks} clicks\n")

    plan = {}
    print(f"{'rule':<20}{'stops':>7}{'clicks with a stop':>20}{'stops at a click':>18}"
          f"{'filter AUC':>12}{'kept':>7}{'found':>8}{'real':>8}")
    for rule in RULES:
        X, y = [], []
        for r in tr:
            st = stops(r, rule)
            _, used = match(r["clicks"], st, [True] * len(st))
            X += [features(r, s_) for s_ in st]
            y += [j in used for j in range(len(st))]
        sc = StandardScaler().fit(np.array(X))
        lr = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(np.array(X)), np.array(y))
        ptr = lr.predict_proba(sc.transform(np.array(X)))[:, 1]
        # threshold: keep 90% of the training recall
        tr_st = []
        k = 0
        for r in tr:
            st = stops(r, rule)
            tr_st.append((r, st, ptr[k:k + len(st)]))
            k += len(st)

        def tr_recall(thr):
            return sum(match(r["clicks"], st, list(p >= thr))[0] for r, st, p in tr_st) / max(
                sum(len(r["clicks"]) for r in tr), 1)
        full = tr_recall(-1)
        thr = next(t for t in np.linspace(0.9, 0.0, 181) if tr_recall(t) >= 0.9 * full)
        te_st, all_st, hit_all, kept, hit_k, used_k = [], 0, 0, 0, 0, 0
        Xte, yte = [], []
        for r in te:
            st = stops(r, rule)
            p = lr.predict_proba(sc.transform(np.array([features(r, s_) for s_ in st])))[:, 1] if st else np.zeros(0)
            h, used = match(r["clicks"], st, [True] * len(st))
            hk, usedk = match(r["clicks"], st, list(p >= thr))
            all_st += len(st)
            hit_all += h
            kept += int((p >= thr).sum())
            hit_k += hk
            used_k += len(usedk)
            Xte += list(p)
            yte += [j in used for j in range(len(st))]
            te_st.append((r, st, p))
        a = pc.auc(np.array(Xte), np.array(yte, int)) if Xte else float("nan")
        print(f"{rule:<20}{all_st:>7}{hit_all / n_clicks:>20.1%}{len([1 for v in yte if v]) / max(all_st, 1):>18.1%}"
              f"{a:>12.3f}{kept:>7}{hit_k / n_clicks:>8.1%}{used_k / max(kept, 1):>8.1%}")
        plan[rule] = (te_st, thr)

    # names, for the delivered rule and the best rule by kept-stop recall
    jobs = {}
    for rule in ("template+self", "template>cnn>self", "cnn"):
        te_st, thr = plan[rule]
        for r, st, p in te_st:
            pts = [(t, x, y) for j, (t, x, y, _) in enumerate(st) if p[j] >= thr]
            jobs.setdefault((r["app"], r["tid"], r["scale"]), set()).update(pts)
    cache = pickle.loads(OCR.read_bytes()) if OCR.exists() else {}
    todo = [(a, t, s, sorted(p for p in pts if (a, t, *p) not in cache)) for (a, t, s), pts in jobs.items()]
    todo = [j for j in todo if j[3]]
    if todo:
        t0 = time.perf_counter()
        print(f"\nOCR around {sum(len(j[3]) for j in todo)} stops in {len(todo)} recordings ...", flush=True)
        with ProcessPoolExecutor(max_workers=3, initializer=_ocr_worker_init) as ex:
            for k, part in enumerate(ex.map(_ocr_one, todo), 1):
                cache.update(part)
                if k % 100 == 0:
                    OCR.write_bytes(pickle.dumps(cache))
                    print(f"  {k}/{len(todo)}, {time.perf_counter() - t0:.0f}s", flush=True)
        OCR.write_bytes(pickle.dumps(cache))

    refs = {(r["app"], r["tid"]): reference_names(r["app"], r["tid"], r["scale"]) for r in te}
    named_clicks = sum(len(r["clicks"]) for r in te if refs[(r["app"], r["tid"])] is not None)
    print(f"\ndelivered click steps (named, repeats merged); names checked on {named_clicks} clicks "
          f"of the {len({r['app'] for r in te if refs[(r['app'], r['tid'])] is not None})} cached applications")
    print(f"{'rule':<20}{'steps':>7}{'real':>8}{'clicks found':>14}{'... same name':>15}")
    per_app = {}
    for rule in ("template+self", "cnn", "template>cnn>self"):
        te_st, thr = plan[rule]
        steps = real = found = named = 0
        app_rows = collections.defaultdict(lambda: [0, 0, 0, 0])
        for r, st, p in te_st:
            cl_steps = []
            for j, (t, x, y, _) in enumerate(st):
                if p[j] < thr:
                    continue
                lab = cl.label_at(cache.get((r["app"], r["tid"], t, x, y), []), x, y, cl.NEAR_PX)
                if lab:
                    cl_steps.append((t, x, y, 0.0, lab))
            merged = []
            for k_ in cl_steps:
                if merged and k_[0] - merged[-1][0] <= MERGE_S and cl.agree(k_[4], merged[-1][4]):
                    merged[-1] = k_
                else:
                    merged.append(k_)
            h, used = match(r["clicks"], [m[:4] for m in merged], [True] * len(merged))
            ref = refs[(r["app"], r["tid"])]
            nm = 0
            if ref is not None:
                for j, ci in used.items():
                    ct, cx, cy = r["clicks"][ci]
                    name = ref.get((round(ct, 2), round(cx), round(cy)), "")
                    if name and cl.agree(merged[j][4], name):
                        nm += 1
            steps += len(merged)
            real += len(used)
            found += h
            named += nm
            row = app_rows[r["app"]]
            row[0] += len(r["clicks"]); row[1] += h; row[2] += len(merged); row[3] += len(used)
        print(f"{rule:<20}{steps:>7}{real / max(steps, 1):>8.1%}{found / n_clicks:>14.1%}"
              f"{named / max(named_clicks, 1):>15.1%}")
        per_app[rule] = app_rows

    rows = per_app["template>cnn>self"]
    base = per_app["template+self"]
    print(f"\nby application, rule template>cnn>self (template+self in brackets); clicks found / steps real")
    for app_ in sorted(rows, key=lambda a: -rows[a][1] / max(rows[a][0], 1)):
        c, h, s_, u = rows[app_]
        bc, bh, bs, bu = base[app_]
        print(f"  {app_:<28}{c:>5} clicks  {h / max(c, 1):>6.1%} ({bh / max(bc, 1):.0%})  "
              f"{u / max(s_, 1):>6.1%} ({bu / max(bs, 1):.0%})")


if __name__ == "__main__":
    {"extract": extract, "eval": evaluate}[sys.argv[1]]()
