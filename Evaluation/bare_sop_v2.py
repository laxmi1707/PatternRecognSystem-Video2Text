"""The whole bare-video SOP detector on one video file, v2: clicks from the pointer CNN.

Same as bare_sop_v1 except how the pointer is found:

    typing   unchanged (bare_sop_v1.typing_steps)
    clicks   5-fps frames; in each, the small changed regions are scanned by the
             pointer CNN (pointer_cnn_v1, any pointer shape) and the best hotspot
             at p >= 0.8 is the pointer; stops by the global rule; the
             screen-reaction model refitted for this rule on the 87-application
             training sample (pointer_cnn_eval_v1.pkl), at the threshold keeping
             60% of its training recall (the strict setting); named by OCR within
             70 px; unnamed stops dropped; repeated reads merged

On the 974 held-out recordings of all 87 applications (pointer_cnn_eval_v2.py) the
delivered click steps are 46.5% at a real click and find 29.9% of clicks, against
40.8% and 27.1% for v1's template + self-match pointer.

    python bare_sop_v2.py VIDEO [--out steps.json]
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, use_backend  # noqa: E402

import numpy as np  # noqa: E402

REACTION = CACHE / "bare_sop_v2_reaction.pkl"
RULE = "cnn@0.8"
KEEP = 0.6              # share of the training recall the reaction threshold keeps
P_POINTER = 0.8
FPS = 5.0
STRIDE = 3              # logical px between CNN hotspot candidates
DIFF = 25
HALF_W, HALF_H = 260, 150
MERGE_S = 2.0


def reaction_model():
    """(scaler, logistic, threshold) fitted on the training recordings' cnn@0.8 stops, cached."""
    if REACTION.exists():
        return pickle.loads(REACTION.read_bytes())
    import pointer_cnn_eval_v1 as e1
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    recs = [r for r in pickle.loads(e1.OUT.read_bytes()) if r["train"]]
    X, y, per = [], [], []
    for r in recs:
        st = e1.stops(r, RULE)
        _, used = e1.match(r["clicks"], st, [True] * len(st))
        X += [e1.features(r, s) for s in st]
        y += [j in used for j in range(len(st))]
        per.append((r, st))
    sc = StandardScaler().fit(np.array(X))
    lr = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(np.array(X)), np.array(y))
    p = lr.predict_proba(sc.transform(np.array(X)))[:, 1]
    tr_p, k = [], 0
    for r, st in per:
        tr_p.append((r, st, p[k:k + len(st)]))
        k += len(st)

    def recall(thr):
        return sum(e1.match(r["clicks"], st, list(q >= thr))[0] for r, st, q in tr_p)
    full = recall(-1)
    thr = float(next(t for t in np.linspace(0.9, 0.0, 181) if recall(t) >= KEEP * full))
    REACTION.write_bytes(pickle.dumps((sc, lr, thr)))
    return sc, lr, thr


def pointer_at(model, gl: np.ndarray, blobs):
    """Best (p, x, y) over hotspot candidates around each small changed region, or None."""
    import torch
    import pointer_cnn_v1 as pc
    crops, where = [], []
    H, W = gl.shape
    for bx, by, bw, bh in blobs[:12]:
        for cy in np.arange(by - 4, by + bh + 4, STRIDE):
            for cx in np.arange(bx - 4, bx + bw + 4, STRIDE):
                x0, y0 = int(cx) - pc.HOT, int(cy) - pc.HOT
                if x0 < 0 or y0 < 0 or x0 + pc.SIZE > W or y0 + pc.SIZE > H:
                    continue
                crops.append(gl[y0:y0 + pc.SIZE, x0:x0 + pc.SIZE])
                where.append((int(cx), int(cy)))
    if not crops:
        return None
    with torch.no_grad():
        p = torch.sigmoid(model(pc.to_tensor(np.stack(crops))).squeeze(1)).numpy()
    k = int(p.argmax())
    return (float(p[k]), *where[k]) if p[k] >= P_POINTER else None


def click_steps(video: Path, ocr, progress=lambda pct, stage: None) -> list[dict]:
    import cv2
    import click_labels_v1 as cl
    import pointer_cnn_eval_v1 as e1
    import pointer_cnn_v1 as pc
    from pointer_motion_v1 import frames

    cap = cv2.VideoCapture(str(video))
    W = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    H = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1)
    cap.release()
    s = 2.0 if W > 2000 else 1.0
    model = pc.load_model()
    prev, fr = None, []
    for t, g in frames(video, FPS):
        if prev is not None and prev.shape == g.shape:
            m = cv2.dilate((cv2.absdiff(g, prev) > DIFF).astype(np.uint8), np.ones((5, 5), np.uint8))
            _, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
            small, large = [], []
            for x, y, w, h, a in (tuple(int(v) for v in row) for row in stats[1:]):
                if a < 15:
                    continue
                if w > 70 * s or h > 70 * s:
                    large.append((x / s, y / s, w / s, h / s, a / (W * H)))
                else:
                    small.append((x / s, y / s, w / s, h / s))
            c = None
            if small:
                gl = g if s == 1.0 else cv2.resize(g, (int(W / s), int(H / s)), interpolation=cv2.INTER_AREA)
                c = pointer_at(model, gl, small)
            fr.append((t, None, [], c, large))
            if len(fr) % 25 == 0:
                progress(min(60, 30 + int(30 * t / max(n, 1))), "tracking the mouse pointer")
        prev = g
    r = {"fps": FPS, "frames": fr}
    stops = e1.stops(r, RULE)
    if not stops:
        return []
    sc, lr, thr = reaction_model()
    p = lr.predict_proba(sc.transform(np.array([e1.features(r, x) for x in stops])))[:, 1]
    kept = [(st, float(pj)) for st, pj in zip(stops, p) if pj >= thr]
    progress(62, "reading the controls under the pointer")
    out = []
    cap = cv2.VideoCapture(str(video))
    for i, ((t, x, y, _), pj) in enumerate(kept):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if not ok:
            continue
        X, Y = x * s, y * s
        x0, y0 = int(max(0, X - HALF_W * s)), int(max(0, Y - HALF_H * s))
        crop = f[y0:int(min(f.shape[0], Y + HALF_H * s)), x0:int(min(f.shape[1], X + HALF_W * s))]
        regs = [[g.text, g.bbox[0] + x0, g.bbox[1] + y0, g.bbox[2] + x0, g.bbox[3] + y0, g.confidence]
                for g in ocr.extract_text(crop).regions]
        lab = cl.label_at(regs, X, Y, cl.NEAR_PX * s)
        if lab:
            out.append({"t": round(t, 2), "action": "Click", "text": lab, "x": round(x), "y": round(y),
                        "score": round(pj, 3)})
        progress(62 + int(18 * (i + 1) / max(len(kept), 1)), "reading the controls under the pointer")
    cap.release()
    merged = []
    for k in out:
        if merged and k["t"] - merged[-1]["t"] <= MERGE_S and cl.agree(k["text"], merged[-1]["text"]):
            merged[-1] = k
        else:
            merged.append(k)
    return merged


def run(video: Path, progress=lambda pct, stage: None) -> dict:
    use_backend()
    from app.pipeline.ocr_extractor import OCRExtractor
    from bare_sop_v1 import typing_steps
    t0 = time.perf_counter()
    typed = typing_steps(video, progress)
    t1 = time.perf_counter()
    clicks = click_steps(video, OCRExtractor(), progress)
    progress(90, "writing the SOP")
    return {"video": video.name, "app": typed["app"], "app_confidence": typed["app_confidence"],
            "duration": typed["duration"], "seconds_taken": round(time.perf_counter() - t0, 1),
            "seconds_clicks": round(time.perf_counter() - t1, 1),
            "steps": sorted(typed["steps"] + clicks, key=lambda k: k["t"])}


def main() -> None:
    from v2k.env import limit_cpu
    limit_cpu(12)
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = run(Path(a.video), lambda pct, stage: print(f"  {pct:3d}%  {stage}", flush=True))
    js = json.dumps(res, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(js, encoding="utf-8")
    print(js)


if __name__ == "__main__":
    main()
