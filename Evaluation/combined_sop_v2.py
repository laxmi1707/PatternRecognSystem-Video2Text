"""Typing + clicks from the bare video, merged into one SOP, scored against the log.

v2: two click steps with the same label within MERGE_S seconds are one click
(combined_sop_v1 showed "Select Folder" twice, "Open" then "Onen").

On the 59 held-out pointer recordings (VSCode, Bash, Eclipse, KDevelop, NetBeans):

    typing   run_037's out-of-fold ranker scores (routed by the predicted
             application, threshold 0.5, repeated reads merged), so no recording
             is scored by a ranker that saw it
    clicks   pointer stops kept by the screen-reaction filter and named by OCR
             (click_labels_v1), with the filter fitted on the training recordings

The reference is every step the log-based generator (v2k/sop.py) would write,
MOVE_TO excluded: clicks, typed strings of at least MIN_LEN characters, and the
rest (keys, hotkeys, drags ...) which this detector does not attempt.

    a typed step is right    it matches one logged string (sop_detector._matches),
                             one to one
    a click step is right    its stop matches one logged click (<= 2 s before,
                             <= 40 px) and, strictly, its label agrees with the
                             label v2k/sop.py gives that click

    python combined_sop_v2.py
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import frame_cache_dir, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(8)

import numpy as np  # noqa: E402

import click_labels_v1 as cl  # noqa: E402
import pointer_reaction_v1 as pr  # noqa: E402
import pointer_tracker_v1 as pt  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

OOF = ROOT / "runs" / "run_037_sop-detector" / "oof_scores.npz"
OUT_MD = ROOT / "combined_sop_v2_examples.md"
THR = 0.19
MERGE_S = 2.0         # v2: repeated reads of one click are merged


def reaction_model():
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    recs = pickle.loads(pr.OUT.read_bytes())
    X, y = [], []
    for r in recs:
        if r["train"]:
            st = pr.stops_of(r)
            _, _, _, used = pr.match(r["clicks"], st, [True] * len(st))
            X += [pr.features(r, s) for s in st]
            y += used
    sc = StandardScaler().fit(np.array(X))
    return recs, sc, LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(np.array(X)), np.array(y))


def typed_steps(app: str, tid: int, oof) -> list[dict]:
    rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
    with np.load(frame_cache_dir() / app / f"{tid}.npz") as z:
        ts = z["timestamp"]
    rows = sd.candidates(rec)
    m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
    if len(m) != len(rows):
        raise SystemExit(f"{app}/{tid}: {len(rows)} candidates, {len(m)} scores")
    s = oof["score_predicted"][m]
    above = sorted((i for i in range(len(rows)) if s[i] >= sd.THRESHOLD), key=lambda i: -s[i])
    return [{"t": float(ts[min(rows[i]["start"], len(ts) - 1)]), "action": "Type",
             "text": rows[i]["text"], "score": float(s[i])}
            for i in sd.dedupe(above, [r["text"] for r in rows])]


def reference(app: str, tid: int, s: float) -> list[dict]:
    """The steps v2k/sop.py writes, MOVE_TO excluded, with click labels as it names them."""
    rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
    frames = rec["frames"]
    out = []
    for seg in rec["segments"]:
        refs = seg["keyframes"]
        for pos, a in enumerate(seg["actions"]):
            kind = (a.get("action_type") or "").upper()
            if kind == "MOVE_TO" or a.get("timestamp") is None:
                continue
            prm = a.get("action_params") or {}
            t = float(a["timestamp"])
            if kind in pt.CLICKS and prm.get("x") is not None:
                ref = refs[min(pos, len(refs) - 1)] if refs else None
                regions = frames[ref].get("ocr_native_regions") if ref is not None else []
                x, y = float(prm["x"]), float(prm["y"])
                out.append({"t": t, "kind": "click", "x": x, "y": y,
                            "text": cl.label_at(regions, x * s, y * s, cl.NEAR_PX * s)})
            elif kind == "TYPING":
                txt = (prm.get("text") or "").strip()
                if len(sd.norm(txt)) >= sd.MIN_LEN:
                    out.append({"t": t, "kind": "type", "text": txt})
                elif txt:
                    out.append({"t": t, "kind": "short", "text": txt})
            else:
                out.append({"t": t, "kind": "other", "text": kind.lower()})
    return out


def main() -> None:
    oof = dict(np.load(OOF))
    recs, sc, lr = reaction_model()
    labels = pickle.loads(cl.OCR_CACHE.read_bytes())

    tot = {k: 0 for k in ("click", "type", "short", "other")}
    found = {"click_pos": 0, "click_named": 0, "type": 0}
    emitted = {"click": 0, "type": 0}
    right = {"click_pos": 0, "click_named": 0, "type": 0}
    examples = []
    for r in recs:
        if r["train"]:
            continue
        app, tid = r["app"], r["tid"]
        ev = pt.pointer_events(app, tid)
        v = pt.Video(pt.video_of(app, tid))
        s = pt.coord_scale(ev, v.W)
        v.close()
        ref = reference(app, tid, s)
        for x in ref:
            tot[x["kind"]] += 1

        # clicks: filtered, named stops
        st = pr.stops_of(r)
        p = lr.predict_proba(sc.transform(np.array([pr.features(r, x) for x in st])))[:, 1] if st else []
        clicks = []
        for j, (t, x, y, _) in enumerate(st):
            lab = labels.get((app, tid, t, x, y), "")
            if p[j] >= THR and lab:
                clicks.append({"t": t, "action": "Click", "text": lab, "x": x, "y": y})
        # one press read twice: the same label within MERGE_S seconds is one click, kept at
        # the later stop, which sits closer to the press
        merged = []
        for k in clicks:
            if merged and k["t"] - merged[-1]["t"] <= MERGE_S and cl.agree(k["text"], merged[-1]["text"]):
                merged[-1] = k
            else:
                merged.append(k)
        clicks = merged
        ref_clicks = [c for c in ref if c["kind"] == "click"]
        used = set()
        for ci, c in enumerate(ref_clicks):
            cands = [j for j, k in enumerate(clicks) if j not in used
                     and c["t"] - pr.BEFORE <= k["t"] <= c["t"] + pr.AFTER
                     and np.hypot(k["x"] - c["x"], k["y"] - c["y"]) <= pr.NEAR]
            if cands:
                j = min(cands, key=lambda j: abs(clicks[j]["t"] - c["t"]))
                used.add(j)
                clicks[j]["ok_pos"] = True
                found["click_pos"] += 1
                if c["text"] and cl.agree(clicks[j]["text"], c["text"]):
                    clicks[j]["ok"] = True
                    found["click_named"] += 1
        emitted["click"] += len(clicks)
        right["click_pos"] += sum(1 for k in clicks if k.get("ok_pos"))
        right["click_named"] += sum(1 for k in clicks if k.get("ok"))

        # typing: out-of-fold steps, one-to-one against logged strings
        typed = typed_steps(app, tid, oof)
        want = [x for x in ref if x["kind"] == "type"]
        taken = set()
        for k in sorted(typed, key=lambda k: -k["score"]):
            hit = [i for i, w in enumerate(want) if i not in taken and sd._matches(k["text"], w["text"])]
            if hit:
                taken.add(hit[0])
                k["ok"] = True
        emitted["type"] += len(typed)
        right["type"] += sum(1 for k in typed if k.get("ok"))
        found["type"] += len(taken)

        steps = sorted(clicks + typed, key=lambda k: k["t"])
        examples.append((app, tid, ref, steps, sum(1 for k in steps if k.get("ok"))))

    n_ref = sum(tot.values())
    n_target = tot["click"] + tot["type"]
    n_emit = emitted["click"] + emitted["type"]
    print(f"59 held-out recordings: {n_ref} log-based steps = {tot['click']} clicks, "
          f"{tot['type']} typed strings, {tot['short']} typed under {sd.MIN_LEN} chars, "
          f"{tot['other']} other (keys, hotkeys, drags ...)\n")
    print(f"{'':<34}{'emitted':>8}{'right':>8}{'precision':>11}{'found':>8}{'of':>6}{'recall':>8}")

    def line(name, em, ok, fd, of):
        print(f"{name:<34}{em:>8}{ok:>8}{ok / max(em, 1):>11.1%}{fd:>8}{of:>6}{fd / max(of, 1):>8.1%}")
    line("Type steps", emitted["type"], right["type"], found["type"], tot["type"])
    line("Click steps, right place", emitted["click"], right["click_pos"], found["click_pos"], tot["click"])
    line("Click steps, right place + name", emitted["click"], right["click_named"], found["click_named"], tot["click"])
    line("All steps (place)", n_emit, right["type"] + right["click_pos"],
         found["type"] + found["click_pos"], n_target)
    line("All steps (place + name)", n_emit, right["type"] + right["click_named"],
         found["type"] + found["click_named"], n_target)
    print(f"\nagainst every log-based step, other kinds included: "
          f"{(found['type'] + found['click_pos']) / n_ref:.1%} (place), "
          f"{(found['type'] + found['click_named']) / n_ref:.1%} (place + name)")

    # side-by-side examples: the recordings with most right steps
    md = ["# Bare-video SOP vs log-based SOP — examples (held out)", ""]
    for app, tid, ref, steps, n_ok in sorted(examples, key=lambda e: -e[4])[:6]:
        md += [f"## {app} {tid}", "", "| from the video only | | from the action log |", "|---|---|---|"]
        lv = [f"{k['t']:5.1f}s {k['action']} '{k['text']}'" + (" ✓" if k.get("ok") else "") for k in steps]
        rv = [f"{x['t']:5.1f}s " + {"click": "Click", "type": "Type"}.get(x["kind"], "") +
              (f" '{x['text']}'" if x["kind"] in ("click", "type") else f" ({x['kind']}: {x['text']})")
              for x in ref]
        for i in range(max(len(lv), len(rv))):
            md.append(f"| {lv[i] if i < len(lv) else ''} | | {rv[i] if i < len(rv) else ''} |")
        md.append("")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"examples -> {OUT_MD.name}")


if __name__ == "__main__":
    main()
