"""Incremental OCR (detector/fast_ocr.py) against full OCR, with the shipped typing ranker.

ocr_fast_eval_v1 compared the two with run_037 and lost one typed step in four
recordings (Komodo Edit). Here the reference is bare_check_v2's 16 held-out recordings,
already read the full way at 1 fps (cache/bare_v2). Each is read again with incremental
OCR, and both readings go through run_040's ranker (routed by the true application, so
only the OCR differs):

    same steps      the typed steps written are identical
    right           of the logged typed strings, how many each finds (one to one)
    seconds         reading time, full (from bare_check_v2.log) and incremental

For changed recordings the candidates that differ are printed.

    python ocr_fast_eval_v2.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, limit_cpu, use_backend  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import joblib  # noqa: E402
import numpy as np  # noqa: E402

import bare_check_v2 as bc  # noqa: E402
import combined_sop_v1 as cs  # noqa: E402
import pointer_cnn_v1 as pc  # noqa: E402
from combined_sop_v4 import match_typed  # noqa: E402
from detector import fast_ocr  # noqa: E402
from detector.typed_text import RANKERS  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402
from v2k import sop_extras as sx  # noqa: E402

METHOD = "bands-v2"          # bump when detector/fast_ocr.py changes
FAST = CACHE / "bare_v2_fast" / METHOD


def fast_record(app: str, tid: int) -> tuple[dict, float, str]:
    path = FAST / f"{app}_{tid}.json"
    if path.exists():
        d = json.loads(path.read_text(encoding="utf-8"))
        return d, d["seconds"], d["how"]
    from v2k.frames import Extractors, extract_video
    if not hasattr(fast_record, "ex"):
        fast_record.ex = Extractors(with_cnn=False)
        fast_record.base = fast_record.ex.ocr
    inc = fast_record.ex.ocr = fast_ocr.IncrementalOCR(fast_record.base)
    t0 = time.perf_counter()
    _, rec = extract_video(pc.VIDEOS / app / str(tid) / "video" / "video.mp4", [], fast_record.ex,
                           grid=False, grid_ocr=False, native_ocr=True, parity_ocr=False)
    dt = time.perf_counter() - t0
    how = f"{inc.full_reads} full, {inc.partial_reads} partial, {inc.reused} reused"
    d = {"frames": rec["frames"], "video": rec.get("video"), "seconds": round(dt, 1), "how": how}
    FAST.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d), encoding="utf-8")
    return d, dt, how


def typed(bundle: dict, record: dict, app: str) -> tuple[list[dict], list[dict]]:
    rows = sx.candidates_ext(record)
    if not rows:
        return [], rows
    X = np.array([[r[f] for f in bundle["features"]] for r in rows], dtype=np.float32)
    E = np.array([[r[f] for f in bundle["extra_features"]] for r in rows], dtype=np.float32)
    texts = [r["text"] for r in rows]
    M = sx.matrix(X, E, texts, np.zeros(len(rows), dtype=np.int64), sd.text_score(bundle["text_model"], texts))
    r_ = bundle["per_app"].get(app)
    p = sx.combine(r_.predict_proba(M)[:, 1] if r_ is not None else None, bundle["pooled"].predict_proba(M)[:, 1])
    for r, s in zip(rows, p):
        r["score"] = float(s)
    above = sorted((i for i in range(len(rows)) if p[i] >= bundle["threshold"]), key=lambda i: -p[i])
    return [{"t": rows[i]["start"], "text": rows[i]["text"], "score": float(p[i])}
            for i in sd.dedupe(above, texts)], rows


def main() -> None:
    use_backend()
    bundle = joblib.load(RANKERS)
    full_s = {m.group(1): float(m.group(2)) for m in
              re.finditer(r"extracted (.+?): \d+ frames in (\d+)s", (CACHE / "bare_check_v2.log").read_text(encoding="utf-8"))}
    full_s["OnlyOffice Calendar/69579"] = 218.0          # the smoke run, before the log
    test = bc.pick(16)
    tot = dict(full=0.0, fast=0.0, same=0, ok_full=0, ok_fast=0, want=0, steps_full=0, steps_fast=0)
    for r in test:
        app, tid = r["app"], r["tid"]
        key = f"{app}/{tid}"
        full = json.loads((bc.BARE / f"{app}_{tid}.json").read_text(encoding="utf-8"))
        fast, dt, how = fast_record(app, tid)
        want = [x for x in cs.reference(app, tid, r["scale"]) if x["kind"] == "type"]
        a, ra = typed(bundle, full, app)
        b, rb = typed(bundle, fast, app)
        same = [s["text"] for s in a] == [s["text"] for s in b]
        oa, ob = match_typed(want, a), match_typed(want, b)
        tot.update(full=tot["full"] + full_s.get(key, 0), fast=tot["fast"] + dt, same=tot["same"] + same,
                   ok_full=tot["ok_full"] + oa, ok_fast=tot["ok_fast"] + ob, want=tot["want"] + len(want),
                   steps_full=tot["steps_full"] + len(a), steps_fast=tot["steps_fast"] + len(b))
        print(f"{key:<30} full {full_s.get(key, 0):5.0f}s  fast {dt:5.0f}s ({how})  "
              f"steps {len(a)}->{len(b)} {'same' if same else 'CHANGED'}  right {oa}->{ob} of {len(want)}", flush=True)
        if not same:
            print(f"    logged: {[w['text'] for w in want]}")
            print(f"    full:   {[(s['t'], s['text'], round(s['score'], 2)) for s in a]}")
            print(f"    fast:   {[(s['t'], s['text'], round(s['score'], 2)) for s in b]}")
            ka = {(x['start'], sd.norm(x['text'])) for x in ra}
            kb = {(x['start'], sd.norm(x['text'])) for x in rb}
            print(f"    candidates only in full: {sorted(ka - kb)[:8]}")
            print(f"    candidates only in fast: {sorted(kb - ka)[:8]}")
    n = len(test)
    print(f"\nreading time {tot['full']:.0f}s -> {tot['fast']:.0f}s ({tot['full'] / max(tot['fast'], 1):.1f}x faster); "
          f"identical typed steps {tot['same']}/{n}")
    print(f"typed steps {tot['steps_full']} -> {tot['steps_fast']}; right {tot['ok_full']} -> {tot['ok_fast']} "
          f"of {tot['want']} logged typed strings")


if __name__ == "__main__":
    main()
