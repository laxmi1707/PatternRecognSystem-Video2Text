"""The whole bare-video SOP detector on one video file: typing + clicks -> steps.

Nothing but the video is read, exactly as for a user's upload:

    typing   v2k.sop_detector on the 1-fps frame grid (extract_video with no
             actions): stage-1 application, growth-rule candidates, that
             application's ranker (run_037 bundle), merged reads
    clicks   5-fps frames; the pointer seen moving by template or self-match
             (pointer_selfmatch_v2), stops by the global rule with recurring
             self-hits dropped; the screen-reaction model fitted on the training
             recordings (threshold 0.16, chosen there); named by OCR within 70 px
             (v2k/sop.py's rule); unnamed stops dropped; repeated reads merged

Coordinates on a frame wider than 2000 px are halved, as Retina recordings were
in training. The run_037 typing bundle was fitted on every recording, so on a
VideoCUA video its typing steps are a demonstration, not an evaluation; the
click models never saw the held-out recordings.

    python bare_sop_v1.py VIDEO [--out steps.json]
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

BUNDLE = ROOT / "runs" / "run_037_sop-detector" / "sop_detector.joblib"
REACTION = CACHE / "bare_sop_v1_reaction.pkl"
FPS = 5.0
THR = 0.16
HALF_W, HALF_H = 260, 150
MERGE_S = 2.0


def reaction_model():
    """(scaler, logistic) fitted on the training recordings' stops, cached."""
    if REACTION.exists():
        return pickle.loads(REACTION.read_bytes())
    import pointer_reaction_v1 as pr
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    recs = pickle.loads((CACHE / "pointer_selfmatch_v2_derived.pkl").read_bytes())
    X, y = [], []
    for r in recs:
        if r["train"]:
            st = r["_stops"]
            _, _, _, used = pr.match(r["clicks"], st, [True] * len(st))
            X += [pr.features(r, s) for s in st]
            y += used
    sc = StandardScaler().fit(np.array(X))
    lr = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(np.array(X)), np.array(y))
    REACTION.write_bytes(pickle.dumps((sc, lr)))
    return sc, lr


def click_steps(video: Path, ocr, progress=lambda pct, stage: None) -> list[dict]:
    import cv2
    import click_labels_v1 as cl
    import pointer_reaction_v1 as pr
    import pointer_selfmatch_v2 as ps
    import pointer_tracker_v1 as pt
    from pointer_motion_v1 import frames

    cap = cv2.VideoCapture(str(video))
    W = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    H = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1)
    cap.release()
    s = 2.0 if W > 2000 else 1.0
    templates = pt.load_templates()
    prev, fr = None, []
    for t, g in frames(video, FPS):
        if prev is not None and prev.shape == g.shape:
            hit, selfs, large = ps.step(g, prev, templates, s)
            fr.append((t, None if hit is None else (hit[1] / s, hit[2] / s),
                       [(x / s, y / s) for _, x, y in selfs],
                       [(x / s, y / s, w / s, h / s, a / (W * H)) for x, y, w, h, a in large]))
            if len(fr) % 25 == 0:
                progress(min(60, 30 + int(30 * t / max(n, 1))), "tracking the mouse pointer")
        prev = g
    r = {"fps": FPS, "frames": fr, "iv": [(t, lg) for t, _, _, lg in fr]}
    stops, _ = ps.make_stops(r, "global", True)
    if not stops:
        return []
    sc, lr = reaction_model()
    p = lr.predict_proba(sc.transform(np.array([pr.features(r, x) for x in stops])))[:, 1]
    kept = [(st, float(pj)) for st, pj in zip(stops, p) if pj >= THR]
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


def typing_steps(video: Path, progress=lambda pct, stage: None) -> dict:
    import joblib
    from v2k import sop_detector as sd
    from v2k.frames import Extractors, extract_video
    bundle = joblib.load(BUNDLE)
    app_bundle = joblib.load(bundle["stage1_bundle"])
    progress(5, "reading the screen (OCR, one frame per second)")
    ex = Extractors(with_cnn="cnn" in app_bundle["blocks"])
    arrays, record = extract_video(video, [], ex, grid=False, grid_ocr=False,
                                   native_ocr=True, parity_ocr="ocr" in app_bundle["blocks"])
    record.update(task_id=0, app="(input)", platform="", instruction="", keyword_label="")
    progress(28, "identifying the application and filtering typed text")
    res = sd.detect(bundle, arrays, record, None, app_bundle)
    res["duration"] = (record.get("video") or {}).get("duration_seconds")
    res["steps"] = [{"t": round(s_["time"], 2), "action": "Type", "text": s_["text"], "score": round(s_["score"], 3)}
                    for s_ in res["steps"]]
    return res


def run(video: Path, progress=lambda pct, stage: None) -> dict:
    use_backend()
    from app.pipeline.ocr_extractor import OCRExtractor
    t0 = time.perf_counter()
    typed = typing_steps(video, progress)
    clicks = click_steps(video, OCRExtractor(), progress)
    progress(90, "writing the SOP")
    return {"video": video.name, "app": typed["app"], "app_confidence": typed["app_confidence"],
            "duration": typed["duration"], "seconds_taken": round(time.perf_counter() - t0, 1),
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
