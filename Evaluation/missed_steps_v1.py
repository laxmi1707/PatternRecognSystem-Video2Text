"""Where each log-based step is lost, and how accurate the steps that are found are.

Same 59 held-out recordings and detector as combined_sop_v2. Every logged click
is followed through the click pipeline, every typed string through the typing
pipeline, and the first stage that loses it is counted:

    clicks   pointer stop -> screen-reaction filter -> text under the pointer
             -> merging repeated reads -> label agrees with v2k/sop.py
    typing   growing text at all -> ranker above threshold -> merged reads

    python missed_steps_v1.py
"""
from __future__ import annotations

import collections
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
import combined_sop_v1 as cs  # noqa: E402
import pointer_reaction_v1 as pr  # noqa: E402
import pointer_tracker_v1 as pt  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

MERGE_S = 2.0


def greedy(ref_clicks, stops):
    """{click index: stop index}, as in pointer_motion_v1."""
    used, out = set(), {}
    for ci, c in enumerate(ref_clicks):
        cands = [j for j, k in enumerate(stops) if j not in used
                 and c["t"] - pr.BEFORE <= k["t"] <= c["t"] + pr.AFTER
                 and np.hypot(k["x"] - c["x"], k["y"] - c["y"]) <= pr.NEAR]
        if cands:
            j = min(cands, key=lambda j: abs(stops[j]["t"] - c["t"]))
            used.add(j)
            out[ci] = j
    return out


def main() -> None:
    oof = dict(np.load(cs.OOF))
    recs, sc, lr = cs.reaction_model()
    labels = pickle.loads(cl.OCR_CACHE.read_bytes())

    click_loss = collections.Counter()
    type_loss = collections.Counter()
    other = collections.Counter()
    dt_click, dpx_click, dt_type = [], [], []
    wrong_click = collections.Counter()
    for r in recs:
        if r["train"]:
            continue
        app, tid = r["app"], r["tid"]
        ev = pt.pointer_events(app, tid)
        v = pt.Video(pt.video_of(app, tid))
        s = pt.coord_scale(ev, v.W)
        v.close()
        ref = cs.reference(app, tid, s)
        for x in ref:
            if x["kind"] == "other":
                other[x["text"]] += 1
            elif x["kind"] == "short":
                other["typing under 3 chars"] += 1

        # ---- clicks
        st = pr.stops_of(r)
        p = lr.predict_proba(sc.transform(np.array([pr.features(r, x) for x in st])))[:, 1] if st else []
        allst = [{"t": t, "x": x, "y": y, "p": p[j], "text": labels.get((app, tid, t, x, y), "")}
                 for j, (t, x, y, _) in enumerate(st)]
        stage = [allst,
                 [k for k in allst if k["p"] >= cs.THR],
                 [k for k in allst if k["p"] >= cs.THR and k["text"]]]
        merged = []
        for k in stage[2]:
            if merged and k["t"] - merged[-1]["t"] <= MERGE_S and cl.agree(k["text"], merged[-1]["text"]):
                merged[-1] = k
            else:
                merged.append(k)
        stage.append(merged)
        rc = [c for c in ref if c["kind"] == "click"]
        maps = [greedy(rc, sset) for sset in stage]
        moves = r["moves"]
        for ci, c in enumerate(rc):
            if ci not in maps[0]:
                prev = [d for d in rc[:ci] if c["t"] - d["t"] <= 5 and np.hypot(d["x"] - c["x"], d["y"] - c["y"]) <= pr.NEAR]
                seen = any(c["t"] - pr.BEFORE <= t <= c["t"] + pr.AFTER for t, _, _ in moves)
                click_loss["a. no pointer stop: clicked again in the same place" if prev else
                           "b. no pointer stop: pointer seen moving, stop elsewhere / >40 px" if seen else
                           "c. no pointer stop: pointer not seen moving at all"] += 1
            elif ci not in maps[1]:
                click_loss["d. stop found, screen-reaction filter dropped it"] += 1
            elif ci not in maps[2]:
                click_loss["e. no text under the pointer"] += 1
            elif ci not in maps[3]:
                click_loss["f. merged into a neighbouring click"] += 1
            else:
                k = stage[3][maps[3][ci]]
                dt_click.append(k["t"] - c["t"])
                dpx_click.append(np.hypot(k["x"] - c["x"], k["y"] - c["y"]))
                if not c["text"]:
                    click_loss["g. found; the log-based SOP has no name to compare"] += 1
                elif cl.agree(k["text"], c["text"]):
                    click_loss["h. found, same name"] += 1
                else:
                    click_loss["i. found, different name"] += 1
                    wrong_click[(k["text"], c["text"])] += 1

        # ---- typing
        rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
        rows = sd.candidates(rec)
        typed = cs.typed_steps(app, tid, oof)
        m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
        score = oof["score_predicted"][m]
        for w in (x for x in ref if x["kind"] == "type"):
            any_c = [i for i, row in enumerate(rows) if sd._matches(row["text"], w["text"])]
            if not any_c:
                type_loss["a. never appeared as growing text"] += 1
            elif not any(score[i] >= sd.THRESHOLD for i in any_c):
                type_loss["b. appeared, ranker scored it below 0.5"] += 1
            else:
                hit = [k for k in typed if sd._matches(k["text"], w["text"])]
                if hit:
                    type_loss["c. found"] += 1
                    dt_type.append(hit[0]["t"] - w["t"])
                else:
                    type_loss["d. merged away"] += 1

    def show(title, cnt):
        n = sum(cnt.values())
        print(f"\n{title} ({n})")
        for k in sorted(cnt):
            print(f"  {k:<62}{cnt[k]:>5}{cnt[k] / n:>8.1%}")
    show("logged clicks, where each one ends up", click_loss)
    show("logged typed strings (>= 3 chars)", type_loss)
    show("steps not attempted", other)
    print(f"\nfound clicks: step time - click time median {np.median(dt_click):+.1f} s "
          f"(IQR {np.percentile(dt_click, 25):+.1f} .. {np.percentile(dt_click, 75):+.1f}); "
          f"position error median {np.median(dpx_click):.1f} px, 90th pct {np.percentile(dpx_click, 90):.1f} px")
    if dt_type:
        print(f"found typing: step time - logged time median {np.median(dt_type):+.1f} s")
    print("\ndifferent names (detector | log-based):")
    for (a, b), n in wrong_click.most_common(20):
        print(f"  {a!r:<40} | {b!r}")


if __name__ == "__main__":
    main()
