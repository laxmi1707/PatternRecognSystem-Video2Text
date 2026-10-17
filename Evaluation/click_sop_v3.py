"""The merged bare-video SOP with the three fixes from missed_steps_v1, scored once.

Reads the stops chosen by pointer_selfmatch_v2 (template + self-match pointer,
stop rule picked on the training recordings) and adds:

    names     OCR regions are cached per stop (crop +-260 x +-150 px), so the
              naming rule can vary without reading again:
                near70     v2k/sop.py's rule, unnamed stops dropped (as before)
                near120    nearest text within 120 px
                icon       near70, and an unnamed stop becomes "Click (icon)"
    typing    a typed step is timed at the frame BEFORE its text first showed:
              it was typed between the two. On log-timed keyframes the first
              frame showing the text is the next action's, up to tens of
              seconds later; on a 1-fps upload the two differ by at most 1 s.

Scoring as combined_sop_v2 (59 held-out recordings, one to one). A click name
is right when it agrees with v2k/sop.py's label, or both are empty.

    python click_sop_v3.py
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import frame_cache_dir, limit_cpu, use_backend  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

import click_labels_v1 as cl  # noqa: E402
import combined_sop_v1 as cs  # noqa: E402
import pointer_reaction_v1 as pr  # noqa: E402
import pointer_tracker_v1 as pt  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

DERIVED = pt.CACHE / "pointer_selfmatch_v2_derived.pkl"
REGIONS = pt.CACHE / "click_sop_v3_regions.pkl"
HALF_W, HALF_H = 260, 150
MERGE_S = 2.0


def reaction(recs):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    X, y = [], []
    for r in recs:
        if r["train"]:
            st = r["_stops"]
            _, _, _, used = pr.match(r["clicks"], st, [True] * len(st))
            X += [pr.features(r, s) for s in st]
            y += used
    sc = StandardScaler().fit(np.array(X))
    lr = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(np.array(X)), np.array(y))

    def p_of(r):
        st = r["_stops"]
        return lr.predict_proba(sc.transform(np.array([pr.features(r, s) for s in st])))[:, 1] if st else np.zeros(0)
    # threshold: keep 90% of the training recall, as pointer_reaction_v1 did
    tr = [r for r in recs if r["train"]]
    ps = {id(r): p_of(r) for r in tr}

    def recall(thr):
        h = c = 0
        for r in tr:
            hit, _, _, _ = pr.match(r["clicks"], r["_stops"], list(ps[id(r)] >= thr))
            h, c = h + hit, c + len(r["clicks"])
        return h / max(c, 1)
    full = recall(-1)
    thr = next(t for t in np.linspace(0.9, 0.0, 181) if recall(t) >= 0.9 * full)
    return p_of, float(thr)


def regions_for(jobs, ocr) -> dict:
    import cv2
    cache = pickle.loads(REGIONS.read_bytes()) if REGIONS.exists() else {}
    todo = [j for j in jobs if j[:5] not in cache]
    by_video: dict = {}
    for j in todo:
        by_video.setdefault(j[:2], []).append(j)
    t0, done = time.perf_counter(), 0
    for (app, tid), js in by_video.items():
        cap = cv2.VideoCapture(str(pt.video_of(app, tid)))
        for app_, tid_, t, x, y, s in js:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, f = cap.read()
            regs = []
            if ok:
                X, Y = x * s, y * s
                x0, y0 = int(max(0, X - HALF_W * s)), int(max(0, Y - HALF_H * s))
                crop = f[y0:int(min(f.shape[0], Y + HALF_H * s)), x0:int(min(f.shape[1], X + HALF_W * s))]
                regs = [[g.text, (g.bbox[0] + x0) / s, (g.bbox[1] + y0) / s, (g.bbox[2] + x0) / s,
                         (g.bbox[3] + y0) / s, g.confidence] for g in ocr.extract_text(crop).regions]
            cache[(app_, tid_, t, x, y)] = regs       # logged coordinates
            done += 1
        REGIONS.write_bytes(pickle.dumps(cache))
    if todo:
        print(f"  OCR on {done} new stops, {time.perf_counter() - t0:.0f}s")
    return cache


def typed_steps(app: str, tid: int, oof, shift: bool) -> list[dict]:
    rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
    with np.load(frame_cache_dir() / app / f"{tid}.npz") as z:
        ts = z["timestamp"]
    rows = sd.candidates(rec)
    m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
    s = oof["score_predicted"][m]
    above = sorted((i for i in range(len(rows)) if s[i] >= sd.THRESHOLD), key=lambda i: -s[i])
    out = []
    for i in sd.dedupe(above, [r["text"] for r in rows]):
        k = min(rows[i]["start"], len(ts) - 1)
        k = max(k - 1, 0) if shift else k
        out.append({"t": float(ts[k]), "action": "Type", "text": rows[i]["text"], "score": float(s[i])})
    return out


def name(regs, x, y, rule):
    if rule == "near120":
        return cl.label_at(regs, x, y, 120)
    return cl.label_at(regs, x, y, cl.NEAR_PX)


def run(test, regions, oof, rule, shift, show=False):
    tot = {"click": 0, "type": 0, "all": 0}
    em = {"click": 0, "type": 0}
    ok_pos = ok_name = ok_type = 0
    dts = []
    examples = []
    for r, s, p, thr, ref in test:
        app, tid = r["app"], r["tid"]
        tot["all"] += len(ref)
        clicks = []
        for j, (t, x, y, _) in enumerate(r["_stops"]):
            if p[j] < thr:
                continue
            lab = name(regions[(app, tid, t, x, y)], x, y, rule)
            if not lab and rule != "icon":
                continue
            clicks.append({"t": t, "x": x, "y": y, "text": lab, "action": "Click"})
        merged = []
        for k in clicks:
            if merged and k["t"] - merged[-1]["t"] <= MERGE_S and (
                    cl.agree(k["text"], merged[-1]["text"]) or
                    (not k["text"] and not merged[-1]["text"] and
                     np.hypot(k["x"] - merged[-1]["x"], k["y"] - merged[-1]["y"]) <= 20)):
                merged[-1] = k
            else:
                merged.append(k)
        clicks = merged
        rc = [c for c in ref if c["kind"] == "click"]
        tot["click"] += len(rc)
        used = set()
        for c in rc:
            cands = [j for j, k in enumerate(clicks) if j not in used
                     and c["t"] - pr.BEFORE <= k["t"] <= c["t"] + pr.AFTER
                     and np.hypot(k["x"] - c["x"], k["y"] - c["y"]) <= pr.NEAR]
            if cands:
                j = min(cands, key=lambda j: abs(clicks[j]["t"] - c["t"]))
                used.add(j)
                clicks[j]["ok"] = True
                ok_pos += 1
                if (c["text"] and cl.agree(clicks[j]["text"], c["text"])) or (not c["text"] and not clicks[j]["text"]):
                    ok_name += 1
                    clicks[j]["named_ok"] = True
        em["click"] += len(clicks)

        typed = typed_steps(app, tid, oof, shift)
        want = [x for x in ref if x["kind"] == "type"]
        tot["type"] += len(want)
        taken = set()
        for k in sorted(typed, key=lambda k: -k["score"]):
            hit = [i for i, w in enumerate(want) if i not in taken and sd._matches(k["text"], w["text"])]
            if hit:
                taken.add(hit[0])
                k["ok"] = True
                k["named_ok"] = True
                dts.append(k["t"] - want[hit[0]]["t"])
        em["type"] += len(typed)
        ok_type += len(taken)
        examples.append((app, tid, ref, sorted(clicks + typed, key=lambda k: k["t"])))

    n_emit = em["click"] + em["type"]
    tgt = tot["click"] + tot["type"]
    row = {"steps": n_emit, "prec_place": (ok_pos + ok_type) / max(n_emit, 1),
           "prec_name": (ok_name + ok_type) / max(n_emit, 1),
           "rec_place": (ok_pos + ok_type) / tgt, "rec_name": (ok_name + ok_type) / tgt,
           "all_place": (ok_pos + ok_type) / tot["all"], "all_name": (ok_name + ok_type) / tot["all"],
           "click_steps": em["click"], "click_pos": ok_pos, "click_name": ok_name,
           "type_steps": em["type"], "type_ok": ok_type,
           "type_dt": float(np.median(dts)) if dts else float("nan")}
    return row, examples


def main() -> None:
    oof = dict(np.load(cs.OOF))
    recs = pickle.loads(DERIVED.read_bytes())
    p_of, thr = reaction(recs)
    print(f"reaction threshold chosen on train (keeps 90% of train recall): {thr:.3f}")
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
        test.append((r, s, p_of(r), thr, cs.reference(r["app"], r["tid"], s)))
    jobs = [(r["app"], r["tid"], t, x, y, s) for r, s, p, th, _ in test
            for j, (t, x, y, _) in enumerate(r["_stops"]) if p[j] >= th]
    regions = regions_for(jobs, ocr)

    print(f"\n{'variant':<34}{'steps':>6}{'real (place)':>13}{'real (+name)':>13}"
          f"{'found (place)':>14}{'found (+name)':>14}{'of all log':>11}{'type dt':>9}")
    for rule, shift in (("near70", False), ("near70", True), ("near120", True), ("icon", True)):
        row, ex = run(test, regions, oof, rule, shift)
        print(f"{rule + (' + typing time' if shift else ''):<34}{row['steps']:>6}{row['prec_place']:>13.1%}"
              f"{row['prec_name']:>13.1%}{row['rec_place']:>14.1%}{row['rec_name']:>14.1%}"
              f"{row['all_place']:>11.1%}{row['type_dt']:>+8.1f}s")
        print(f"{'':<34}  clicks {row['click_steps']} emitted, {row['click_pos']} at a click, "
              f"{row['click_name']} named right; typing {row['type_steps']} emitted, {row['type_ok']} right")
        if rule == "near70" and shift:
            md = ["# Bare-video SOP vs log-based SOP — click_sop_v3 (held out)", ""]
            for app, tid, ref, steps in sorted(ex, key=lambda e: -sum(1 for k in e[3] if k.get("ok")))[:6]:
                md += [f"## {app} {tid}", "", "| from the video only | | from the action log |", "|---|---|---|"]
                lv = [f"{k['t']:5.1f}s {k['action']} '{k['text']}'" + (" ✓" if k.get("ok") else "") for k in steps]
                rv = [f"{x['t']:5.1f}s " + {"click": "Click", "type": "Type"}.get(x["kind"], "") +
                      (f" '{x['text']}'" if x["kind"] in ("click", "type") else f" ({x['kind']}: {x['text']})")
                      for x in ref]
                for i in range(max(len(lv), len(rv))):
                    md.append(f"| {lv[i] if i < len(lv) else ''} | | {rv[i] if i < len(rv) else ''} |")
                md.append("")
            (ROOT / "click_sop_v3_examples.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
