"""From pointer stops to "Click 'Save'" steps, scored against the log-based SOP.

The log-based generator (v2k/sop.py) names a click by the OCR text under the
logged click point, or the nearest text within 70 px. Here the same rule runs
at a detected pointer stop instead, on the frame where the pointer came to rest,
so the two can be compared step for step:

    stops        Plan A stops (pointer_reaction_v1 cache), optionally filtered by
                 the screen-reaction model fitted on the training recordings
    label        easyocr (the backend's OCRExtractor) on a crop around the stop,
                 the nearest text box within 70 px
    reference    the label v2k/sop.py writes for each logged click, read from
                 the full-resolution OCR of the cached keyframe at the click

A click step is right when its stop matches a logged click (at most 2 s before,
within 40 px, as before) and its label agrees with that click's reference label.
Held-out recordings only.

    python click_labels_v1.py
"""
from __future__ import annotations

import difflib
import json
import pickle
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import frame_cache_dir, limit_cpu, use_backend  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

import pointer_reaction_v1 as pr  # noqa: E402
import pointer_tracker_v1 as pt  # noqa: E402

NEAR_PX = 70           # as v2k/sop.py, in logged pixels
HALF_W, HALF_H = 260, 90
OCR_CACHE = pt.CACHE / "click_labels_v1_ocr.pkl"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def agree(a: str, b: str) -> bool:
    a, b = norm(a), norm(b)
    return bool(a and b and (a == b or a in b or b in a or difflib.SequenceMatcher(None, a, b).ratio() >= 0.8))


def label_at(regions, x: float, y: float, near: float) -> str:
    """v2k/sop.py's _label_at, with the distance limit in the regions' own pixels."""
    best, best_d = "", float("inf")
    for text, x1, y1, x2, y2, conf in regions or []:
        if not text or conf < 0.4:
            continue
        if x1 <= x <= x2 and y1 <= y <= y2:
            return text
        d = float(np.hypot((x1 + x2) / 2 - x, (y1 + y2) / 2 - y))
        if d < best_d:
            best, best_d = text, d
    return best if best_d <= near else ""


def reference_labels(app: str, tid: int, s: float) -> list[tuple[float, float, float, str]]:
    """(t, x, y, label) for each logged click, as v2k/sop.py would name it."""
    rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
    frames = rec["frames"]
    out = []
    for seg in rec["segments"]:
        refs = seg["keyframes"]
        for pos, a in enumerate(seg["actions"]):
            if (a.get("action_type") or "").upper() not in pt.CLICKS:
                continue
            prm = a.get("action_params") or {}
            if prm.get("x") is None or a.get("timestamp") is None:
                continue
            ref = refs[min(pos, len(refs) - 1)] if refs else None
            regions = frames[ref].get("ocr_native_regions") if ref is not None else []
            x, y = float(prm["x"]), float(prm["y"])
            out.append((float(a["timestamp"]), x, y, label_at(regions, x * s, y * s, NEAR_PX * s)))
    return out


def ocr_crops(jobs, ocr) -> dict:
    """{(app, tid, t, x, y): label} for stops, reading only a crop around each."""
    import cv2
    cache = pickle.loads(OCR_CACHE.read_bytes()) if OCR_CACHE.exists() else {}
    todo = [j for j in jobs if j[:5] not in cache]
    t0 = time.perf_counter()
    by_video: dict = {}
    for j in todo:
        by_video.setdefault(j[:2], []).append(j)
    done = 0
    for (app, tid), js in by_video.items():
        cap = cv2.VideoCapture(str(pt.video_of(app, tid)))
        for app_, tid_, t, x, y, s in js:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, f = cap.read()
            lab = ""
            if ok:
                X, Y = x * s, y * s
                x0, y0 = int(max(0, X - HALF_W * s)), int(max(0, Y - HALF_H * s))
                crop = f[y0:int(min(f.shape[0], Y + HALF_H * s)), x0:int(min(f.shape[1], X + HALF_W * s))]
                res = ocr.extract_text(crop)
                regs = [[g.text, g.bbox[0] + x0, g.bbox[1] + y0, g.bbox[2] + x0, g.bbox[3] + y0, g.confidence]
                        for g in res.regions]
                lab = label_at(regs, X, Y, NEAR_PX * s)
            cache[(app_, tid_, t, x, y)] = lab
            done += 1
        cap.release()
        print(f"  OCR {done}/{len(todo)} stops, {time.perf_counter() - t0:.0f}s", flush=True)
        OCR_CACHE.write_bytes(pickle.dumps(cache))
    return cache


def main() -> None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    recs = pickle.loads(pr.OUT.read_bytes())
    # the screen-reaction filter, fitted on training recordings exactly as in pointer_reaction_v1
    Xtr, ytr = [], []
    for r in recs:
        if not r["train"]:
            continue
        st = pr.stops_of(r)
        _, _, _, used = pr.match(r["clicks"], st, [True] * len(st))
        Xtr += [pr.features(r, s) for s in st]
        ytr += used
    sc = StandardScaler().fit(np.array(Xtr))
    lr = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(np.array(Xtr)), np.array(ytr))
    THR = 0.19            # "keeps 90% of train recall" in pointer_reaction_v1

    use_backend()
    from app.pipeline.ocr_extractor import OCRExtractor
    ocr = OCRExtractor()

    test = []
    for r in recs:
        if r["train"]:
            continue
        ev = pt.pointer_events(r["app"], r["tid"])
        v = pt.Video(pt.video_of(r["app"], r["tid"]))
        s = pt.coord_scale(ev, v.W)
        v.close()
        st = pr.stops_of(r)
        p = lr.predict_proba(sc.transform(np.array([pr.features(r, x) for x in st])))[:, 1] if st else []
        test.append((r, s, st, np.asarray(p), reference_labels(r["app"], r["tid"], s)))
    jobs = [(r["app"], r["tid"], t, x, y, s) for r, s, st, _, _ in test for t, x, y, _ in st]
    labels = ocr_crops(jobs, ocr)

    n_clicks = sum(len(ref) for *_, ref in test)
    n_ref_lab = sum(sum(1 for c in ref if c[3]) for *_, ref in test)
    print(f"\n{len(test)} held-out recordings, {n_clicks} logged clicks, "
          f"{n_ref_lab} of them named by the log-based SOP ({n_ref_lab / n_clicks:.0%})")

    def score(name, keep_fn):
        steps = right = matched = lab_steps = matched_agree_den = 0
        found_right = 0
        for r, s, st, p, ref in test:
            keep = [keep_fn(p[j], labels[(r["app"], r["tid"], *st[j][:3])]) for j in range(len(st))]
            used_by = {}
            for ci, (ct, cx, cy, _) in enumerate(ref):
                cands = [j for j, (ts, x, y, _) in enumerate(st)
                         if keep[j] and j not in used_by and ct - pr.BEFORE <= ts <= ct + pr.AFTER
                         and np.hypot(x - cx, y - cy) <= pr.NEAR]
                if cands:
                    used_by[min(cands, key=lambda j: abs(st[j][0] - ct))] = ci
            for j in range(len(st)):
                if not keep[j]:
                    continue
                lab = labels[(r["app"], r["tid"], *st[j][:3])]
                steps += 1
                lab_steps += bool(lab)
                if j in used_by:
                    matched += 1
                    reflab = ref[used_by[j]][3]
                    ok = agree(lab, reflab) if reflab else not lab
                    right += ok
                    found_right += ok
                    matched_agree_den += 1
        print(f"{name:<40}{steps:>6}{lab_steps / max(steps, 1):>9.0%}{matched / max(steps, 1):>10.1%}"
              f"{right / max(steps, 1):>10.1%}{right / max(matched_agree_den, 1):>10.1%}"
              f"{found_right / n_clicks:>10.1%}")

    print(f"\n{'':<40}{'steps':>6}{'named':>9}{'at click':>10}{'right':>10}{'label ok':>10}{'recall':>10}")
    print(f"{'':<40}{'':>6}{'':>9}{'(prec.)':>10}{'(prec.)':>10}{'|matched':>10}{'(right)':>10}")
    score("all stops (Plan A)", lambda p, lab: True)
    score("reaction filter (p>=0.19)", lambda p, lab: p >= THR)
    score("named stops only", lambda p, lab: bool(lab))
    score("reaction filter + named", lambda p, lab: p >= THR and bool(lab))

    # examples
    print("\nexamples, reaction filter + named (stop label  |  log-based label):")
    shown = 0
    for r, s, st, p, ref in test:
        for j, (ts, x, y, _) in enumerate(st):
            lab = labels[(r["app"], r["tid"], ts, x, y)]
            if p[j] < THR or not lab:
                continue
            near = [c for c in ref if ts - pr.AFTER <= c[0] and c[0] - pr.BEFORE <= ts
                    and np.hypot(x - c[1], y - c[2]) <= pr.NEAR]
            print(f"  {r['app']:<9}{ts:6.1f}s  Click '{lab}'  |  {repr(near[0][3]) if near else '(no click)'}")
            shown += 1
            if shown >= 25:
                return


if __name__ == "__main__":
    main()
