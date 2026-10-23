"""Every number for the report, for the detector as now shipped (detector/clicks.py):
pointer CNN, the 17-feature LightGBM click filter, same-place merging, and icon clicks
(stops with no text kept as "Click (icon)"; the right-name rate counts named steps only).

Same held-out recordings and rules as before:

    clicks      974 recordings of all 87 applications: steps, real, found, right name
    whole SOP   the 720 with typing scores (61 applications): totals, per application,
                and the two chance baselines of combined_sop_v4 (same step counts,
                20 seeds)

    python combined_sop_v9.py
"""
from __future__ import annotations

import collections
import json
import pickle
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import frame_cache_dir, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

import click_labels_v1 as cl  # noqa: E402
import combined_sop_v1 as cs  # noqa: E402
import pointer_cnn_eval_v1 as e1  # noqa: E402
from click_variants_v1 import steps_of  # noqa: E402
from combined_sop_v4 import match_clicks, match_typed, typed_from  # noqa: E402
from detector.clicks import load_reaction_model  # noqa: E402
from reaction_features_v1 import screen_sizes, table  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

SEEDS = 20


def main() -> None:
    score, thr = load_reaction_model()
    ocr = pickle.loads(e1.OCR.read_bytes())
    recs = [r for r in pickle.loads(e1.OUT.read_bytes()) if not r["train"]]
    sizes = screen_sizes(recs)
    rows = []
    for r, st, X, _ in table(recs, sizes):
        p = score(X) if len(st) else np.zeros(0)
        rows.append((r, st, steps_of(r, st, p, thr, ocr, True, True)))

    # clicks, 87 applications
    n_clicks = sum(len(r["clicks"]) for r, *_ in rows)
    n = hit = matched = right = 0
    for r, st, s_ in rows:
        ref = [{"t": t, "x": x, "y": y} for t, x, y in r["clicks"]]
        n, hit = n + len(s_), hit + match_clicks(ref, s_)
        names = e1.reference_names(r["app"], r["tid"], r["scale"])
        if names is not None:
            _, used = e1.match(r["clicks"], [(k["t"], k["x"], k["y"], 0) for k in s_], [True] * len(s_))
            for j, ci in used.items():
                ct, cx, cy = r["clicks"][ci]
                name = names.get((round(ct, 2), round(cx), round(cy)), "")
                if name and s_[j]["text"]:
                    matched, right = matched + 1, right + cl.agree(s_[j]["text"], name)
    icons = sum(1 for _, _, s_ in rows for k in s_ if not k["text"])
    print(f"clicks, {len(rows)} held-out recordings of 87 applications ({n_clicks} clicks): {n} steps "
          f"({icons} on icons), "
          f"{hit / n:.1%} real, {hit / n_clicks:.1%} found, right name {right / matched:.1%} of {matched}")

    # whole SOP, 61 applications
    oof = dict(np.load(cs.OOF))
    apps = set(oof["app"].tolist())
    sub = [x for x in rows if x[0]["app"] in apps
           and (frame_cache_dir() / x[0]["app"] / f"{x[0]['tid']}.json").exists()]
    tot = collections.Counter()
    per_app = collections.defaultdict(collections.Counter)
    base = {name: collections.Counter() for name in ("random", "random candidate")}
    rngs = [random.Random(seed) for seed in range(SEEDS)]
    for r, st, s_ in sub:
        app, tid = r["app"], r["tid"]
        rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
        with np.load(frame_cache_dir() / app / f"{tid}.npz") as z:
            ts = z["timestamp"]
        cand = sd.candidates(rec)
        m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
        sc_ = oof["score_predicted"][m]
        above = sorted((i for i in range(len(cand)) if sc_[i] >= sd.THRESHOLD), key=lambda i: -sc_[i])
        typed = typed_from(cand, ts, above)
        ref = cs.reference(app, tid, r["scale"])
        rc = [c for c in ref if c["kind"] == "click"]
        want = [x for x in ref if x["kind"] == "type"]
        row = {"ref_c": len(rc), "ref_t": len(want), "ref_all": len(ref), "emit_c": len(s_),
               "emit_t": len(typed), "ok_c": match_clicks(rc, s_), "ok_t": match_typed(want, typed)}
        tot.update(row)
        per_app[app].update(row)
        dur = max((f[0] for f in r["frames"]), default=1.0)
        W, H = sizes[f"{app}/{tid}"]
        for rng in rngs:
            rnd = sorted(({"t": rng.uniform(0, dur), "x": rng.uniform(0, W), "y": rng.uniform(0, H)}
                          for _ in range(len(s_))), key=lambda k: k["t"])
            base["random"].update(emit=len(s_) + len(typed), ok=match_clicks(rc, rnd))
            pick = sorted(rng.sample(st, min(len(s_), len(st))))
            order = list(range(len(cand)))
            rng.shuffle(order)
            rt = typed_from(cand, ts, order)[:len(typed)]
            base["random candidate"].update(
                emit=len(pick) + len(rt),
                ok=match_clicks(rc, [{"t": t, "x": x, "y": y} for t, x, y, _ in pick]) + match_typed(want, rt))
    target = tot["ref_c"] + tot["ref_t"]
    print(f"\nwhole SOP, {len(sub)} recordings of {len(per_app)} applications; logged {tot['ref_c']} clicks, "
          f"{tot['ref_t']} typed, {tot['ref_all']} steps in all")
    print(f"  clicks  {tot['emit_c']:>5} steps  {tot['ok_c'] / tot['emit_c']:.1%} real  {tot['ok_c'] / tot['ref_c']:.1%} found")
    print(f"  typing  {tot['emit_t']:>5} steps  {tot['ok_t'] / tot['emit_t']:.1%} real  {tot['ok_t'] / tot['ref_t']:.1%} found")
    ok = tot["ok_c"] + tot["ok_t"]
    emit = tot["emit_c"] + tot["emit_t"]
    print(f"  whole   {emit:>5} steps  {ok / emit:.1%} real  {ok / target:.1%} found  "
          f"({ok / tot['ref_all']:.1%} of every logged step)")
    for name, c in base.items():
        print(f"  baseline {name:<17} {c['ok'] / c['emit']:.1%} real  {c['ok'] / SEEDS / target:.1%} found")
    print("\nby application: steps / real / found")
    order = sorted(per_app, key=lambda a: -(per_app[a]["ok_c"] + per_app[a]["ok_t"]) /
                   max(per_app[a]["ref_c"] + per_app[a]["ref_t"], 1))
    for a in order:
        c = per_app[a]
        e, o, t = c["emit_c"] + c["emit_t"], c["ok_c"] + c["ok_t"], c["ref_c"] + c["ref_t"]
        print(f"  {a:<28}{e:>5}{o / max(e, 1):>8.1%}{o / max(t, 1):>8.1%}")


if __name__ == "__main__":
    main()
