"""Does the evaluation borrow timing from the action log?

The frame cache was built with each recording's actions: v2k/frames.py seeks a
keyframe to every action timestamp, and full-resolution OCR runs only on those
keyframes. A real bare video has no actions, so its keyframes are a plain 1-fps
grid. The detector was therefore trained and scored on OCR taken at exactly the
moments the user acted - moments only the log knows.

This measures how much that matters. For a few recordings whose video is still
on disk it re-extracts frames the bare-video way, trains a detector WITHOUT
those recordings, and scores both versions of each recording against the same
logged typing:

    cached   keyframes at action timestamps (what every reported figure used)
    bare     keyframes on the 1-fps grid (what a user's upload gets)

Stage 2 is routed by the true application, so only the keyframe timing differs.

    python bare_vs_cached_v1.py <per_app> [app ...]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

from v2k import sop_detector as sd  # noqa: E402
from v2k.env import frame_cache_dir  # noqa: E402

BARE = CACHE / "bare_v1"


def pick(apps: list[str], per_app: int) -> list[tuple[str, int]]:
    out = []
    for app in apps:
        n = 0
        for p in sorted((frame_cache_dir() / app).glob("*.json")):
            if n >= per_app:
                break
            if not (ROOT / "data" / "VideoCUA" / app / p.stem / "video" / "video.mp4").exists():
                continue
            rec = json.loads(p.read_text(encoding="utf-8"))
            if any(len(sd.norm(w)) >= sd.MIN_LEN for w in sd.logged_typing(rec)):
                out.append((app, int(p.stem)))
                n += 1
    return out


def extract_bare(app: str, tid: int, ex) -> dict:
    """1-fps keyframes, no actions passed: exactly what detect --video does."""
    from v2k.frames import extract_video

    out_json = BARE / app / f"{tid}.json"
    if out_json.exists():
        return json.loads(out_json.read_text(encoding="utf-8"))
    video = ROOT / "data" / "VideoCUA" / app / str(tid) / "video" / "video.mp4"
    t0 = time.perf_counter()
    arrays, record = extract_video(video, [], ex, grid=False, grid_ocr=False,
                                   native_ocr=True, parity_ocr=False)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_json.with_suffix(".npz"), **arrays)
    out_json.write_text(json.dumps(record), encoding="utf-8")
    print(f"    extracted {app}/{tid}: {record['n_frames']} frames, "
          f"{record['n_keyframe_rows']} keyframes, {time.perf_counter() - t0:.0f}s", flush=True)
    return record


def strict(kept: list[str], want: list[str]) -> int:
    """Maximum one-to-one matching between kept step texts and logged strings."""
    owner: dict[int, int] = {}

    def claim(i: int, seen: set[int]) -> bool:
        for j, w in enumerate(want):
            if j in seen or not sd._matches(kept[i], w):
                continue
            seen.add(j)
            if j not in owner or claim(owner[j], seen):
                owner[j] = i
                return True
        return False

    return sum(1 for i in range(len(kept)) if claim(i, set()))


def score_record(rows: list[dict], texts: list[str], model, rankers, app: str) -> tuple[list[str], int]:
    """Steps the detector keeps for one recording, and how many candidates it saw."""
    if not rows or app not in rankers:
        return [], len(rows)
    X = np.array([[r[f] for f in sd.FEATURES] for r in rows], dtype=np.float32)
    M = sd.ranker_matrix(X, np.array([sd.lexical(t) for t in texts], dtype=np.float32),
                         sd.text_score(model, texts),
                         sd.context(X, np.zeros(len(rows), dtype=np.int64), texts))
    p = rankers[app].predict_proba(M)[:, 1]
    above = sorted((i for i in range(len(rows)) if p[i] >= 0.5), key=lambda i: -p[i])
    return [texts[i] for i in sd.dedupe(above, texts)], len(rows)


def main(per_app: int, apps: list[str]) -> None:
    from v2k.env import use_backend

    use_backend()
    from v2k.frames import Extractors

    t0 = time.perf_counter()
    chosen = pick(apps, per_app)
    print(f"{len(chosen)} recordings: {', '.join(f'{a}/{t}' for a, t in chosen)}", flush=True)

    # ---- 1. bare extraction (the expensive part; resumable)
    ex = Extractors(with_cnn=True)
    bare = {(a, t): extract_bare(a, t, ex) for a, t in chosen}
    print(f"extraction done, {time.perf_counter() - t0:.0f}s", flush=True)

    # ---- 2. a detector that never saw the chosen recordings
    data = sd.build_candidates()
    X, app_a, tid = data["X"], data["app"], data["tid"]
    texts = sd.texts_of(data)
    label, _ = sd.labels_at(data, sd.MIN_LEN)
    held = np.isin(tid, [t for _, t in chosen])
    train = np.flatnonzero(~held)
    lex = np.array([sd.lexical(t) for t in texts], dtype=np.float32)
    ctx = sd.context(X, tid, texts)
    ts = sd.oof_text_scores(texts, label, tid, train)
    M = sd.ranker_matrix(X, lex, ts, ctx)
    model = sd.fit_text_model(texts, label, train)
    rankers = {}
    for a in sorted({a for a, _ in chosen}):
        m = (~held) & (app_a == a)
        rankers[a] = sd._fit_app(M[m], label[m])
    print(f"held-out detector trained, {time.perf_counter() - t0:.0f}s", flush=True)

    # ---- 3. score both versions of every chosen recording
    tot = {"cached": [0, 0, 0, 0, 0], "bare": [0, 0, 0, 0, 0]}   # steps, real, targets, ceiling, cands
    print(f"\n{'recording':22s}{'typed':>6s}   {'cached: cands':>14s}{'steps':>6s}{'real':>5s}{'ceil':>5s}"
          f"   {'bare: cands':>12s}{'steps':>6s}{'real':>5s}{'ceil':>5s}")
    for a, t in chosen:
        crec = json.loads((frame_cache_dir() / a / f"{t}.json").read_text(encoding="utf-8"))
        want = [w for w in sd.logged_typing(crec) if len(sd.norm(w)) >= sd.MIN_LEN]
        line = f"{a + '/' + str(t):22s}{len(want):6d}   "
        for name, rec in (("cached", crec), ("bare", bare[(a, t)])):
            rows = sd.candidates(rec)
            rtexts = [r["text"] for r in rows]
            kept, n = score_record(rows, rtexts, model, rankers, a)
            real = strict(kept, want)
            ceil = sum(1 for w in want if any(sd._matches(c, w) for c in rtexts))
            for k, v in enumerate((len(kept), real, len(want), ceil, n)):
                tot[name][k] += v
            line += f"{n:14d}{len(kept):6d}{real:5d}{ceil:5d}   " if name == "cached" else \
                    f"{n:12d}{len(kept):6d}{real:5d}{ceil:5d}"
        print(line)

    print(f"\n{'':10s}{'candidates':>11s}{'steps':>7s}{'precision':>11s}{'recall':>9s}{'ceiling':>9s}")
    for name, (steps, real, targets, ceil, cands) in tot.items():
        print(f"{name:10s}{cands:11d}{steps:7d}{real / max(steps, 1):11.1%}{real / max(targets, 1):9.1%}"
              f"{ceil / max(targets, 1):9.1%}")
    print(f"\n{time.perf_counter() - t0:.0f}s total")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2:] or ["Bash", "VSCode"])
