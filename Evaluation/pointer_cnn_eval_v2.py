"""Delivered click steps for the CNN@0.8 pointer rule, with a reaction-filter sweep.

v1 named only template+self, cnn (p>=0.5) and template>cnn>self, but cnn@0.8 had the
better stage numbers. This reuses v1's extraction and OCR cache and scores the delivered
(named, merged) steps for template+self, cnn@0.8 and template>cnn@0.8>self, each at
reaction-filter thresholds keeping 90%, 75% and 60% of the training recall.

    python pointer_cnn_eval_v2.py
"""
from __future__ import annotations

import collections
import pickle
import time
from concurrent.futures import ProcessPoolExecutor

import pointer_cnn_eval_v1 as e1  # caps CPU threads on import, so it comes first
import numpy as np
from pointer_cnn_eval_v1 import OCR, OUT, MERGE_S, features, match, reference_names, stops, pc

RULES = ["template+self", "cnn@0.8", "template>cnn@0.8>self"]
KEEPS = [0.9, 0.75, 0.6]


def main() -> None:
    import click_labels_v1 as cl
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    recs = pickle.loads(OUT.read_bytes())
    tr = [r for r in recs if r["train"]]
    te = [r for r in recs if not r["train"]]
    n_clicks = sum(len(r["clicks"]) for r in te)

    plan = {}
    for rule in RULES:
        X, y, tr_st = [], [], []
        for r in tr:
            st = stops(r, rule)
            _, used = match(r["clicks"], st, [True] * len(st))
            X += [features(r, s_) for s_ in st]
            y += [j in used for j in range(len(st))]
            tr_st.append((r, st))
        sc = StandardScaler().fit(np.array(X))
        lr = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(np.array(X)), np.array(y))
        ptr = lr.predict_proba(sc.transform(np.array(X)))[:, 1]
        k = 0
        tr_p = []
        for r, st in tr_st:
            tr_p.append((r, st, ptr[k:k + len(st)]))
            k += len(st)

        def tr_recall(thr):
            return sum(match(r["clicks"], st, list(p >= thr))[0] for r, st, p in tr_p)
        full = tr_recall(-1)
        thrs = {keep: next(t for t in np.linspace(0.9, 0.0, 181) if tr_recall(t) >= keep * full) for keep in KEEPS}
        te_st = []
        for r in te:
            st = stops(r, rule)
            p = lr.predict_proba(sc.transform(np.array([features(r, s_) for s_ in st])))[:, 1] if st else np.zeros(0)
            te_st.append((r, st, p))
        plan[rule] = (te_st, thrs)
        print(f"{rule}: thresholds " + ", ".join(f"{k:.0%}->{t:.3f}" for k, t in thrs.items()), flush=True)

    jobs = {}
    for rule in RULES:
        te_st, thrs = plan[rule]
        thr = min(thrs.values())
        for r, st, p in te_st:
            pts = [(t, x, y) for j, (t, x, y, _) in enumerate(st) if p[j] >= thr]
            jobs.setdefault((r["app"], r["tid"], r["scale"]), set()).update(pts)
    cache = pickle.loads(OCR.read_bytes()) if OCR.exists() else {}
    todo = [(a, t, s, sorted(p for p in pts if (a, t, *p) not in cache)) for (a, t, s), pts in jobs.items()]
    todo = [j for j in todo if j[3]]
    if todo:
        t0 = time.perf_counter()
        print(f"\nOCR around {sum(len(j[3]) for j in todo)} new stops in {len(todo)} recordings ...", flush=True)
        with ProcessPoolExecutor(max_workers=3, initializer=e1._ocr_worker_init) as ex:
            for k, part in enumerate(ex.map(e1._ocr_one, todo), 1):
                cache.update(part)
                if k % 100 == 0:
                    OCR.write_bytes(pickle.dumps(cache))
                    print(f"  {k}/{len(todo)}, {time.perf_counter() - t0:.0f}s", flush=True)
        OCR.write_bytes(pickle.dumps(cache))

    refs = {(r["app"], r["tid"]): reference_names(r["app"], r["tid"], r["scale"]) for r in te}
    named_clicks = sum(len(r["clicks"]) for r in te if refs[(r["app"], r["tid"])] is not None)
    print(f"\nheld-out: {len(te)} recordings, {n_clicks} clicks; names checked on {named_clicks} clicks")
    print(f"{'rule':<24}{'keep':>6}{'steps':>7}{'real':>8}{'clicks found':>14}{'right name':>12}")
    per_app = {}
    for rule in RULES:
        te_st, thrs = plan[rule]
        for keep, thr in thrs.items():
            steps = real = found = named = matched_named = 0
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
                if ref is not None:
                    for j, ci in used.items():
                        ct, cx, cy = r["clicks"][ci]
                        name = ref.get((round(ct, 2), round(cx), round(cy)), "")
                        if name:
                            matched_named += 1
                            named += cl.agree(merged[j][4], name)
                steps += len(merged)
                real += len(used)
                found += h
                row = app_rows[r["app"]]
                row[0] += len(r["clicks"]); row[1] += h; row[2] += len(merged); row[3] += len(used)
            print(f"{rule:<24}{keep:>6.0%}{steps:>7}{real / max(steps, 1):>8.1%}{found / n_clicks:>14.1%}"
                  f"{named / max(matched_named, 1):>12.1%}", flush=True)
            per_app[(rule, keep)] = app_rows

    rows, base = per_app[("cnn@0.8", 0.9)], per_app[("template+self", 0.9)]
    print("\nby application, cnn@0.8 (template+self in brackets), keep 90%; clicks found / steps real")
    for app_ in sorted(rows, key=lambda a: -rows[a][1] / max(rows[a][0], 1)):
        c, h, s_, u = rows[app_]
        bc, bh, bs, bu = base[app_]
        print(f"  {app_:<28}{c:>5} clicks  {h / max(c, 1):>6.1%} ({bh / max(bc, 1):.0%})  "
              f"{u / max(s_, 1):>6.1%} ({bu / max(bs, 1):.0%})")


if __name__ == "__main__":
    main()
