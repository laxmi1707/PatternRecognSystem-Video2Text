"""Build the SOP detector visualisation from measured files only.

Every number on the page is read here from a run folder, the frame cache or
the stage-1 predictions - nothing is typed into the template. The one exception
is the training-scope experiment, which predates the module and is copied from
ranker_scope_v1.py's printed output; the page labels it as such.

v2 adds the ranker-evidence comparison read from a sop_ranker_experiments run;
v3 appends the conservative-training row from a sop_ranker_experiments_v2 run.

    python viz/build_sop_viz_v3.py runs/<detector run> runs/<experiments run> \
        runs/<experiments-2 run> viz/<page>.html
"""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from v2k import sop_detector as sd  # noqa: E402
from v2k.env import frame_cache_dir  # noqa: E402

TEMPLATE = Path(__file__).with_name("sop_detector_viz_template_v4.html")
ABL_SHORT = {"A": "Frame features only", "B": "+ shape of the text", "C": "+ text model",
             "D": "+ recording context"}
GROWTH = ("OnlyOffice Spreadsheet", 70039)
WORKED = ("Bash", 111478)
N_PERAPP = 16
STAGE1_NAMES = {   # run_029 column -> label on the page
    "ocr_native+ui+visual+cnn:mlp": "OCR + UI + visual + CNN : MLP",
    "ocr_native+ui+visual+cnn:svm": "OCR + UI + visual + CNN : SVM",
    "ocr_native+ui+visual+cnn:random_forest": "OCR + UI + visual + CNN : RF",
    "ocr_native+ui+visual:random_forest": "OCR + UI + visual : RF",
    "cnn:mlp": "CNN : MLP",
    "cnn:svm": "CNN : SVM",
    "ocr_native+ui+visual:mlp": "OCR + UI + visual : MLP",
    "ocr_native+ui+visual:svm": "OCR + UI + visual : SVM",
    "cnn:random_forest": "CNN : RF",
}
# ranker_scope_v1.py, fixed 15 held-out applications, pooled ranker, threshold 0.3,
# match rule before the 3-character floor (printed 2026-10-02).
SCOPE = {
    "points": [{"train_apps": 8, "precision": 0.013, "recall": 0.017},
               {"train_apps": 16, "precision": 0.029, "recall": 0.013},
               {"train_apps": 32, "precision": 0.032, "recall": 0.009}],
    "refs": [{"label": "same ranker on applications it trained on", "value": 0.564},
             {"label": "keeping every candidate", "value": 0.012}],
}


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


def stage1_models() -> list[dict]:
    rows = list(csv.DictReader(open(sd.STAGE1_RUN / "predictions.csv", encoding="utf-8")))
    out = []
    for col, name in STAGE1_NAMES.items():
        raw = sum(r["true"] == r[col] for r in rows) / len(rows)
        canon = sum(sd.canon_app(r["true"]) == sd.canon_app(r[col]) for r in rows) / len(rows)
        out.append({"name": name, "raw": raw, "canon": canon})
    return sorted(out, key=lambda s: -s["canon"])


def action_mix(eligible: set[str]) -> tuple[list[dict], int]:
    c = Counter()
    for sub in frame_cache_dir().iterdir():
        if sub.is_dir() and sub.name in eligible:
            for p in sub.glob("*.json"):
                rec = json.loads(p.read_text(encoding="utf-8"))
                for seg in rec.get("segments", []):
                    for a in seg.get("actions", []):
                        c[(a.get("action_type") or "UNKNOWN").upper()] += 1
    n = sum(c.values())
    named = [("MOVE_TO", "Mouse move"), ("CLICK", "Click"), ("TYPING", "Typing"),
             ("PRESS", "Key press"), ("HOTKEY", "Hotkey")]
    out, used = [], 0
    for key, label in named:
        out.append({"label": label, "count": c[key], "share": c[key] / n,
                    "recovered": key == "TYPING"})
        used += c[key]
    out.append({"label": "Other", "count": n - used, "share": (n - used) / n, "recovered": False})
    return out, n


def rows_of(cache: dict, app: str, tid: int) -> np.ndarray:
    return np.flatnonzero((cache["app"] == app) & (cache["tid"] == tid))


def ablation(exp: Path) -> tuple[dict, float]:
    r = json.loads((exp / "results.json").read_text(encoding="utf-8"))
    ref = r["in_domain"]["A"]["rows"][1]["recall"]          # the first version's recall at 0.5
    rows_in = []
    for v, d in r["in_domain"].items():
        at = [c["precision"] for c in d["curve"] if c["recall"] >= ref]
        rows_in.append({"v": v, "name": d["name"], "short": ABL_SHORT[v], "baseline": v == "A",
                        "precision": d["rows"][1]["precision"], "recall": d["rows"][1]["recall"],
                        "precision_at": max(at) if at else 0.0})
    rows_out = [{"v": v, "name": d["name"], "short": ABL_SHORT[v], "baseline": v == "A",
                 "precision": d["rows"][1]["precision"], "recall": d["rows"][1]["recall"],
                 "precision_at": None} for v, d in r["unseen_apps"].items()]
    return {"in_domain": rows_in, "unseen": rows_out}, ref


def append_conservative(abl: dict, exp2: Path, ref: float) -> None:
    """Round 2's F: same 32 features, per-application rankers trained conservatively."""
    f = json.loads((exp2 / "results.json").read_text(encoding="utf-8"))["F"]
    at = [c["precision"] for c in f["curve"] if c["recall"] >= ref]
    abl["in_domain"].append({"v": "F", "name": f["name"], "short": "+ conservative training",
                             "baseline": False, "precision": f["rows"][1]["precision"],
                             "recall": f["rows"][1]["recall"], "precision_at": max(at) if at else 0.0})


def main(run: Path, exp: Path, exp2: Path, out: Path) -> None:
    res = json.loads((run / "results.json").read_text(encoding="utf-8"))
    abl, abl_ref = ablation(exp)
    append_conservative(abl, exp2, abl_ref)
    oof = np.load(run / "oof_scores.npz")
    cache = sd.build_candidates()
    texts = sd.texts_of(cache)
    label, covers = sd.labels_at(cache, res["min_len"])
    score = oof["score_predicted"]
    assert len(score) == len(texts), "oof scores and candidate cache are out of step"

    head = {r["variant"] + str(r["threshold"]): r for r in res["table"]}
    r05 = head["predicted0.5"]

    # --- growth example: real reads at one position, and the candidate they become
    from v2k.frames import cache_paths

    app, tid = GROWTH
    npz, js = cache_paths(app, tid)
    rec = json.loads(js.read_text(encoding="utf-8"))
    ts = np.load(npz)["timestamp"]
    idx = rows_of(cache, app, tid)
    cand_rows = sd.candidates(rec)
    assert len(cand_rows) == len(idx)
    k = max(range(len(cand_rows)), key=lambda i: (cand_rows[i]["text"].lower().startswith("=textjoin"),
                                                  cand_rows[i]["final_len"]))
    c = cand_rows[k]
    # replay the tracked region's distinct readings
    states, key = [], None
    for fi, fr in enumerate(rec["frames"]):
        for r in fr.get("ocr_native_regions") or []:
            if len(r) >= 6 and str(r[0]).strip() and int(float(r[1]) // sd.CELL) == int(c["x_norm"] * rec["video"]["width"] // sd.CELL) \
                    and int(float(r[2]) // sd.CELL) == int(c["y_norm"] * rec["video"]["height"] // sd.CELL):
                t = str(r[0]).strip()
                if not states or sd.norm(t) != sd.norm(states[-1]["text"]):
                    if not states or sd._extends(states[-1]["text"], t):
                        states.append({"frame": fi, "time": mmss(float(ts[fi])), "text": t})
    growth_instruction = (rec.get("instruction") or "").strip()
    want = [w for w in sd.logged_typing(rec) if len(sd.norm(w)) >= res["min_len"]]
    truth = next((w for w in want if sd._matches(c["text"], w)), want[0] if want else "")
    pred, _ = sd.stage1_oof()
    g_pred = pred[GROWTH[1]][1]
    g_text = c["text"] if len(c["text"]) <= 24 else c["text"][:23] + "…"
    g_step = f"1. Type {g_text}" if float(score[idx[k]]) >= 0.5 else "(not kept)"
    growth = {"states": states,
              "candidate": {"text": c["text"], "growth": c["growth"], "frames_growing": c["frames_growing"],
                            "conf_mean": c["conf_mean"], "x_norm": c["x_norm"], "y_norm": c["y_norm"],
                            "score": float(score[idx[k]]), "truth": truth,
                            "correct": bool(label[idx[k]])}}

    # --- worked example: every candidate's out-of-fold score in one recording
    app, tid = WORKED
    idx = rows_of(cache, app, tid)
    order = sorted(idx.tolist(), key=lambda i: -score[i])
    kept = [i for i in order if score[i] >= 0.5]
    survive = set(sd.dedupe(kept, texts))
    show = order[:16] + [i for i in order[16:] if label[i]][:4]
    worked_rows = [{"text": texts[i], "score": float(score[i]), "correct": bool(label[i]),
                    "merged": i in kept and i not in survive} for i in show]
    n_targets_rec = int(((cache["want_app"] == app) & (cache["want_tid"] == tid)
                         & (cache["want_len"] >= res["min_len"])).sum())
    keep_mask = np.zeros(len(score), bool)
    keep_mask[list(survive)] = True
    sp, sr = sd._strict(keep_mask, covers, cache["tid"], n_targets_rec)
    present = len({int(w) for i in idx for w in covers[i].tolist()})
    real = round(sp * len(survive))
    recovered = round(sr * n_targets_rec)
    worked = {"rows": worked_rows,
              "summary": (f"{len(kept)} candidates pass 0.5; merging repeats leaves {len(survive)} steps, "
                          f"of which {real} {'is' if real == 1 else 'are'} real. "
                          f"{recovered} of the {n_targets_rec} typed strings {'is' if recovered == 1 else 'are'} "
                          f"recovered, although {present} of them were among the {len(idx)} candidates.")}

    # --- funnel
    n_t = res["n_targets"]
    funnel = [{"label": "Typed strings in the action logs", "count": n_t, "share": 1.0},
              {"label": "Present among the candidates", "count": round(res["ceiling"]["recall"] * n_t),
               "share": res["ceiling"]["recall"]},
              {"label": "Recovered as SOP steps, threshold 0.5", "count": round(r05["recall_dedup"] * n_t),
               "share": r05["recall_dedup"]}]

    # --- per application: the ones that contribute most recovered steps
    per = [a for a in res["per_app"] if a["recall"] is not None and a["precision"] is not None]
    per.sort(key=lambda a: -a["recall"] * a["targets"])
    covered_total = sum(a["recall"] * a["targets"] for a in per)
    top8 = sum(a["recall"] * a["targets"] for a in per[:8]) / covered_total
    per_app = sorted(per[:N_PERAPP], key=lambda a: -a["recall"])

    s1 = stage1_models()
    gains = [(s["canon"] - s["raw"]) * 100 for s in s1]
    mix, n_actions = action_mix(set(np.unique(cache["app"]).tolist()))
    typing = next(m for m in mix if m["recovered"])
    xmax = max(p["recall"] for v in res["curves"].values() for p in v)

    data = {
        "growth": growth, "worked": worked, "funnel": funnel, "curves": res["curves"],
        "pr_xmax": float(np.ceil(xmax * 10 + 1e-9) / 10), "per_app": per_app,
        "stage1": s1, "stage1_xmin": float(np.floor(min(s["raw"] for s in s1) * 20) / 20),
        "scope": SCOPE, "mix": mix, "ablation": abl,
        "rule": [r for r in res["table"] if r["variant"] in ("predicted", "no_routing")],
    }
    for r in data["rule"]:
        r["variant"] = {"predicted": "Routed by stage 1", "no_routing": "One pooled ranker"}[r["variant"]]

    subs = {
        "date": time.strftime("%d %B %Y").lstrip("0"),
        "built": time.strftime("%Y-%m-%d %H:%M"),
        "run": f"runs/{run.name}",
        "s1_acc": pct(res["stage1"]["normalised"]),
        "raw_labels": str(res["stage1"]["raw_labels"]),
        "n_recordings_all": f"{res['stage1']['n']:,}",
        "p05": pct(r05["precision_dedup"]),
        "r05": pct(r05["recall_dedup"]),
        "steps05": f"{r05['emitted_dedup']:,}",
        "n_targets": f"{n_t:,}",
        "n_apps": str(res["n_apps"]),
        "n_recordings": f"{res['n_recordings']:,}",
        "n_candidates": f"{res['n_candidates']:,}",
        "n_candidates_short": f"{res['n_candidates'] / 1000:.0f}k",
        "ceiling_p": pct(res["ceiling"]["precision"]),
        "g_app": GROWTH[0], "g_tid": str(GROWTH[1]),
        "g_instruction": growth_instruction,
        "g_x": f"{growth['candidate']['x_norm']:.3f}", "g_y": f"{growth['candidate']['y_norm']:.3f}",
        "g_pred": g_pred,
        "g_step": g_step,
        "n_perapp": str(len(per_app)),
        "top8_share": f"{top8 * 100:.0f}%",
        "gain_min": f"{min(gains):.1f}", "gain_max": f"{max(gains):.1f}",
        "coverage": pct(r05["recall_dedup"] * typing["share"]),
        "typing_share": pct(typing["share"]),
        "n_actions": f"{n_actions:,}",
        "abl_ref_recall": pct(abl_ref),
        "pooled_r05": pct(head["no_routing0.5"]["recall_dedup"]),
        "abl_run": f"runs/{exp.name}",
        "abl_run2": f"runs/{exp2.name}",
    }
    from html import escape

    html = TEMPLATE.read_text(encoding="utf-8")
    for k_, v in subs.items():
        html = html.replace("{{" + k_ + "}}", escape(v, quote=False))
    left = [s for s in set(__import__("re").findall(r"\{\{(\w+)\}\}", html))]
    assert not left, f"unfilled placeholders: {left}"
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/", payload)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size / 1024:.0f} KB)")
    print(f"  headline: precision {subs['p05']}, recall {subs['r05']}, {subs['steps05']} steps")
    print(f"  growth: {len(states)} readings, candidate {growth['candidate']['text']!r} "
          f"score {growth['candidate']['score']:.3f}, correct {growth['candidate']['correct']}")
    print(f"  worked: {worked['summary']}")


if __name__ == "__main__":
    main(ROOT / sys.argv[1], ROOT / sys.argv[2], ROOT / sys.argv[3], ROOT / sys.argv[4])
