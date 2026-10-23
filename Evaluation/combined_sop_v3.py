"""The whole SOP detector v2 (typing + pointer-CNN clicks), scored on many applications.

combined_sop_v2 / click_sop_v3 scored the merged SOP on 59 held-out recordings of 5
applications. This scores bare_sop_v2's steps on the held-out recordings of
pointer_cnn_eval_v1's 87-application sample that also have a frame cache and run_037
typing scores (61 applications):

    clicks   cnn@0.8 stops, bare_sop_v2's reaction filter (strict, thr fitted on the
             training recordings), named from pointer_cnn_eval_v1's OCR cache
             (70 px rule), unnamed dropped, same name within 2 s merged
    typing   run_037 out-of-fold scores, deduped, timed at the frame before the text
             showed (click_sop_v3.typed_steps)
    target   the steps v2k/sop.py writes from the log (combined_sop_v1.reference)

Scoring as click_sop_v3: one to one; a click within 2 s before / 0.3 s after and
40 px; a typed string by sop_detector's text match.

    python combined_sop_v3.py
"""
from __future__ import annotations

import collections
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import frame_cache_dir, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

import bare_sop_v2 as b2  # noqa: E402
import click_labels_v1 as cl  # noqa: E402
import click_sop_v3 as c3  # noqa: E402
import combined_sop_v1 as cs  # noqa: E402
import pointer_cnn_eval_v1 as e1  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

BEFORE, AFTER, NEAR = 2.0, 0.3, 40


def main() -> None:
    oof = dict(np.load(cs.OOF))
    typed_apps = set(oof["app"].tolist())
    sc, lr, thr = b2.reaction_model()
    ocr = pickle.loads(e1.OCR.read_bytes())
    recs = [r for r in pickle.loads(e1.OUT.read_bytes()) if not r["train"]]
    recs = [r for r in recs if r["app"] in typed_apps
            and (frame_cache_dir() / r["app"] / f"{r['tid']}.json").exists()]
    print(f"{len(recs)} held-out recordings, {len({r['app'] for r in recs})} applications "
          f"(reaction threshold {thr:.3f})")

    tot = collections.Counter()
    emit = collections.Counter()
    ok = collections.Counter()
    per_app = collections.defaultdict(lambda: collections.Counter())
    for r in recs:
        app, tid, s = r["app"], r["tid"], r["scale"]
        ref = cs.reference(app, tid, s)
        st = e1.stops(r, b2.RULE)
        p = lr.predict_proba(sc.transform(np.array([e1.features(r, x) for x in st])))[:, 1] if st else []
        clicks = []
        for j, (t, x, y, _) in enumerate(st):
            if p[j] < thr:
                continue
            lab = cl.label_at(ocr.get((app, tid, t, x, y), []), x, y, cl.NEAR_PX)
            if lab:
                clicks.append({"t": t, "x": x, "y": y, "text": lab})
        merged = []
        for k in clicks:
            if merged and k["t"] - merged[-1]["t"] <= b2.MERGE_S and cl.agree(k["text"], merged[-1]["text"]):
                merged[-1] = k
            else:
                merged.append(k)
        rc = [c for c in ref if c["kind"] == "click"]
        used = set()
        n_pos = n_name = 0
        for c in rc:
            cands = [j for j, k in enumerate(merged) if j not in used
                     and c["t"] - BEFORE <= k["t"] <= c["t"] + AFTER
                     and np.hypot(k["x"] - c["x"], k["y"] - c["y"]) <= NEAR]
            if cands:
                j = min(cands, key=lambda j: abs(merged[j]["t"] - c["t"]))
                used.add(j)
                n_pos += 1
                if (c["text"] and cl.agree(merged[j]["text"], c["text"])) or (not c["text"] and not merged[j]["text"]):
                    n_name += 1
        typed = c3.typed_steps(app, tid, oof, shift=True)
        want = [x for x in ref if x["kind"] == "type"]
        taken = set()
        for k in sorted(typed, key=lambda k: -k["score"]):
            hit = [i for i, w in enumerate(want) if i not in taken and sd._matches(k["text"], w["text"])]
            if hit:
                taken.add(hit[0])
        row = {"ref_click": len(rc), "ref_type": len(want), "ref_all": len(ref),
               "emit_click": len(merged), "emit_type": len(typed),
               "ok_click": n_pos, "ok_click_name": n_name, "ok_type": len(taken)}
        for k, v in row.items():
            tot[k] += v
            per_app[app][k] += v

    def line(c):
        emitted = c["emit_click"] + c["emit_type"]
        real = c["ok_click"] + c["ok_type"]
        target = c["ref_click"] + c["ref_type"]
        return emitted, real / max(emitted, 1), real / max(target, 1), real / max(c["ref_all"], 1)

    e, pr_, rc_, al = line(tot)
    print(f"\nlog steps: {tot['ref_all']} ({tot['ref_click']} clicks, {tot['ref_type']} typed strings, "
          f"{tot['ref_all'] - tot['ref_click'] - tot['ref_type']} other)")
    print(f"{'':<10}{'steps':>7}{'real':>8}{'found':>8}")
    print(f"{'clicks':<10}{tot['emit_click']:>7}{tot['ok_click'] / max(tot['emit_click'], 1):>8.1%}"
          f"{tot['ok_click'] / max(tot['ref_click'], 1):>8.1%}   right name {tot['ok_click_name'] / max(tot['ok_click'], 1):.1%}")
    print(f"{'typing':<10}{tot['emit_type']:>7}{tot['ok_type'] / max(tot['emit_type'], 1):>8.1%}"
          f"{tot['ok_type'] / max(tot['ref_type'], 1):>8.1%}")
    print(f"{'whole SOP':<10}{e:>7}{pr_:>8.1%}{rc_:>8.1%}   of every log step {al:.1%}")
    print(f"typing alone would find {tot['ok_type'] / max(tot['ref_all'], 1):.1%} of every log step")

    print("\nby application: steps / real / found (click+type)")
    rows = sorted(per_app.items(), key=lambda kv: -line(kv[1])[2])
    for app, c in rows:
        e, pr_, rc_, _ = line(c)
        print(f"  {app:<28}{e:>5}{pr_:>8.1%}{rc_:>8.1%}")


if __name__ == "__main__":
    main()
