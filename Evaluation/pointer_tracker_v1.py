"""Find the mouse pointer in a bare video, and from its path, the clicks.

cursor_click_probe_v1.py showed that, with the pointer position read from the
log, "the pointer moved in this quarter-second" predicts a click at AUC 0.93.
This replaces the log with pixels.

Step 1  harvest   learn what the pointer looks like. For each logged pointer
                  position, a frame where the pointer rests there minus a frame
                  where it has gone elsewhere leaves only the pointer's own
                  pixels: a sprite and its mask, with no hand labelling. Similar
                  sprites are grouped and each group becomes one masked template.
Step 2  track     masked template matching over each frame; the best match is
                  the pointer, its hotspot the click point.
Step 3  clicks    "moved, then stopped" events from the tracked path.

Recordings are split by task id: templates come only from the train part, and
every figure is measured on the held-out part.

    python pointer_tracker_v1.py harvest <sheet.png>
    python pointer_tracker_v1.py track
    python pointer_tracker_v1.py clicks
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

from v2k.env import frame_cache_dir  # noqa: E402

APPS = ["VSCode", "Bash", "Eclipse", "KDevelop", "NetBeans"]
CLICKS = {"CLICK", "DOUBLE_CLICK", "RIGHT_CLICK"}
POINTER_EVENTS = CLICKS | {"MOVE_TO", "DRAG_TO", "MOUSE_DOWN", "MOUSE_UP"}
TEMPLATES = CACHE / "pointer_templates_v1.pkl"
KEEP = CACHE / "pointer_templates_v1_keep.json"     # ids that passed validation on train
R = 40                 # crop half-size around a logged point, native px
DIFF = 28              # grey-level change that counts as "pointer pixel"


# ------------------------------------------------------------------ data

def video_of(app: str, tid: int) -> Path:
    return ROOT / "data" / "VideoCUA" / app / str(tid) / "video" / "video.mp4"


def recordings() -> list[tuple[str, int]]:
    out = []
    for app in APPS:
        for p in sorted((frame_cache_dir() / app).glob("*.json")):
            if video_of(app, int(p.stem)).exists():
                out.append((app, int(p.stem)))
    return out


def is_train(tid: int) -> bool:
    return (tid * 2654435761 % 10) < 7          # 70 / 30 by task, stable


def pointer_events(app: str, tid: int) -> list[dict]:
    rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
    acts = [a for seg in rec["segments"] for a in seg["actions"]]
    out = []
    for a in acts:
        prm = a.get("action_params") or {}
        if (a.get("action_type") or "").upper() in POINTER_EVENTS and prm.get("x") is not None \
                and a.get("timestamp") is not None:
            out.append({"t": float(a["timestamp"]), "x": float(prm["x"]), "y": float(prm["y"]),
                        "type": (a.get("action_type") or "").upper()})
    return sorted(out, key=lambda e: e["t"])


def coord_scale(events: list[dict], W: float) -> float:
    """Retina recordings log logical points: the frame is twice the logged space."""
    xs = [e["x"] for e in events]
    return 2.0 if xs and W > 2000 and max(xs) < W / 2 + 40 else 1.0


class Video:
    def __init__(self, path: Path):
        import cv2
        self.cap = cv2.VideoCapture(str(path))
        self.W = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.H = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.dur = self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(self.cap.get(cv2.CAP_PROP_FPS), 1)

    def gray(self, t: float):
        import cv2
        self.cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000)
        ok, f = self.cap.read()
        return cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if ok else None

    def close(self):
        self.cap.release()


def crop(g: np.ndarray, x: float, y: float) -> np.ndarray | None:
    xi, yi = int(round(x)), int(round(y))
    if xi - R < 0 or yi - R < 0 or xi + R > g.shape[1] or yi + R > g.shape[0]:
        return None
    return g[yi - R:yi + R, xi - R:xi + R]


# --------------------------------------------------------------- harvest

def rests(events: list[dict], dur: float) -> list[tuple[float, float, float]]:
    """(time, x, y) moments where the pointer sits still at a logged point: the middle
    of the gap before the next pointer event, if the gap is long enough."""
    out = []
    for i, e in enumerate(events):
        nxt = events[i + 1]["t"] if i + 1 < len(events) else dur
        if nxt - e["t"] >= 0.6:
            out.append(((e["t"] + nxt) / 2, e["x"], e["y"]))
    return out


def sprite_from_pair(with_p: np.ndarray, without_p: np.ndarray):
    """Pointer pixels = what differs, as one compact blob touching the centre."""
    import cv2
    d = cv2.absdiff(with_p, without_p)
    m = (d > DIFF).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    best = None
    for k in range(1, n):
        x, y, w, h, area = stats[k]
        # the hotspot sits at the crop centre; the sprite must touch a small box around it
        if not (x <= R + 3 and x + w >= R - 3 and y <= R + 3 and y + h >= R - 3):
            continue
        if 25 <= area <= 900 and w <= 2 * R - 4 and h <= 2 * R - 4:
            if best is None or area > stats[best][4]:
                best = k
    if best is None:
        return None
    x, y, w, h, _ = stats[best]
    mask = (lab[y:y + h, x:x + w] == best).astype(np.uint8)
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))       # keep the outline
    img = with_p[y:y + h, x:x + w]
    return img, mask[:h, :w], (R - x, R - y)                    # hotspot offset within sprite


def harvest(sheet: Path) -> None:
    import cv2
    t0 = time.perf_counter()
    sprites = []
    recs = [r for r in recordings() if is_train(r[1])]
    print(f"{len(recs)} train recordings", flush=True)
    for app, tid in recs:
        ev = pointer_events(app, tid)
        if len(ev) < 2:
            continue
        v = Video(video_of(app, tid))
        s = coord_scale(ev, v.W)
        rs = rests(ev, v.dur)
        for i, (t, x, y) in enumerate(rs):
            x, y = x * s, y * s
            # a frame where the pointer has moved well away from (x, y)
            far = [(t2, x2 * s, y2 * s) for t2, x2, y2 in rs
                   if abs(t2 - t) < 30 and np.hypot(x2 * s - x, y2 * s - y) > 3 * R]
            if not far:
                continue
            g1 = v.gray(t)
            c1 = crop(g1, x, y) if g1 is not None else None
            if c1 is None:
                continue
            # try up to three "pointer elsewhere" frames, nearest in time first: the
            # first one whose difference isolates a clean blob gives the sprite
            for tf, _, _ in sorted(far, key=lambda f: abs(f[0] - t))[:3]:
                g2 = v.gray(tf)
                c2 = crop(g2, x, y) if g2 is not None else None
                got = sprite_from_pair(c1, c2) if c2 is not None else None
                if got is not None:
                    img, mask, hot = got
                    sprites.append({"img": img, "mask": mask, "hot": hot, "app": app, "tid": tid,
                                    "scale": s})
                    break
        v.close()
    print(f"{len(sprites)} sprites harvested in {time.perf_counter() - t0:.0f}s", flush=True)

    # group sprites whose masked pixels agree; a group becomes one template
    groups: list[list[dict]] = []
    for sp in sprites:
        placed = False
        for g in groups:
            ref = g[0]
            if abs(ref["img"].shape[0] - sp["img"].shape[0]) > 3 or \
                    abs(ref["img"].shape[1] - sp["img"].shape[1]) > 3:
                continue
            h = min(ref["img"].shape[0], sp["img"].shape[0])
            w = min(ref["img"].shape[1], sp["img"].shape[1])
            m = (ref["mask"][:h, :w] & sp["mask"][:h, :w]).astype(bool)
            if m.sum() < 20:
                continue
            a = ref["img"][:h, :w][m].astype(float)
            b = sp["img"][:h, :w][m].astype(float)
            if np.abs(a - b).mean() < 24 and \
                    (ref["mask"][:h, :w] ^ sp["mask"][:h, :w]).mean() < 0.35:
                g.append(sp)
                placed = True
                break
        if not placed:
            groups.append([sp])
    groups.sort(key=len, reverse=True)
    templates = []
    for g in groups:
        if len(g) < 2:
            continue
        h = int(np.median([s["img"].shape[0] for s in g]))
        w = int(np.median([s["img"].shape[1] for s in g]))
        same = [s for s in g if s["img"].shape == (h, w)] or g[:1]
        img = np.median(np.stack([s["img"] for s in same if s["img"].shape == (h, w)]), axis=0) \
            if all(s["img"].shape == (h, w) for s in same) else same[0]["img"]
        mask = (np.mean(np.stack([s["mask"] for s in same if s["mask"].shape == (h, w)]), axis=0) >= 0.5) \
            .astype(np.uint8) if all(s["mask"].shape == (h, w) for s in same) else same[0]["mask"]
        hot = tuple(int(np.median([s["hot"][k] for s in same])) for k in (0, 1))
        templates.append({"img": img.astype(np.uint8), "mask": mask, "hot": hot, "n": len(g),
                          "apps": sorted({s["app"] for s in g}),
                          "scale": float(np.median([s["scale"] for s in g]))})
    templates = templates[:24]
    TEMPLATES.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES.write_bytes(pickle.dumps(templates))
    print(f"{len(groups)} groups, {len(templates)} templates kept (groups of 3 or more):")
    for k, tp in enumerate(templates):
        print(f"  {k:2d}  {tp['img'].shape[1]:3d}x{tp['img'].shape[0]:<3d} from {tp['n']:4d} sprites  "
              f"hotspot {tp['hot']}  scale {tp['scale']:.0f}  {', '.join(tp['apps'])}")

    # contact sheet: each template on mid-grey, masked pixels only, enlarged
    tiles = []
    for tp in templates:
        canvas = np.full((2 * R, 2 * R), 128, np.uint8)
        h, w = tp["img"].shape
        canvas[:h, :w] = np.where(tp["mask"][:h, :w] > 0, tp["img"], 128)
        tiles.append(np.pad(canvas, 4, constant_values=255))
    if tiles:
        cv2.imwrite(str(sheet), cv2.resize(np.hstack(tiles), None, fx=3, fy=3,
                                           interpolation=cv2.INTER_NEAREST))
        print(f"wrote {sheet}")


# ----------------------------------------------------------------- track

def load_templates() -> list[dict]:
    """Harvested templates that look like a pointer, plus 2x copies for Retina video.

    A pointer is drawn with a black-and-white outline, so a group whose masked
    pixels lack either very dark or very bright values is UI that changed, not a
    pointer, and is dropped."""
    import cv2
    allowed = None
    if KEEP.exists():
        allowed = set(json.loads(KEEP.read_text(encoding="utf-8")))
    out = []
    for i, tp in enumerate(pickle.loads(TEMPLATES.read_bytes())):
        px = tp["img"][tp["mask"] > 0]
        if not ((px < 60).any() and (px > 190).any()):
            continue
        h, w = tp["img"].shape
        # a pointer is at least ~14 px tall and never a wide strip; smaller or flatter
        # groups are UI fragments, and small templates match almost anywhere
        if h < 14 or w > 1.3 * h:
            continue
        if allowed is not None and i not in allowed:
            continue
        tp = {**tp, "id": i}
        out.append({**tp, "k": 1})
        out.append({"img": cv2.resize(tp["img"], None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST),
                    "mask": cv2.resize(tp["mask"], None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST),
                    "hot": (tp["hot"][0] * 2, tp["hot"][1] * 2), "n": tp["n"], "k": 2, "id": i})
    return out


def find(g: np.ndarray, templates: list[dict], scale: float, near=None, radius: int = 220):
    """Best (score, x, y) for the pointer hotspot; lower score is better (mean squared
    difference over the template's pointer pixels). `near` restricts the search."""
    import cv2
    x0 = y0 = 0
    region = g
    if near is not None:
        cx, cy = int(near[0]), int(near[1])
        x0, y0 = max(0, cx - radius), max(0, cy - radius)
        region = g[y0:min(g.shape[0], cy + radius), x0:min(g.shape[1], cx + radius)]
    best = (np.inf, None, None, None)
    for tp in templates:
        if tp["k"] != (2 if scale == 2.0 else 1):
            continue
        h, w = tp["img"].shape
        if region.shape[0] < h or region.shape[1] < w:
            continue
        res = cv2.matchTemplate(region, tp["img"], cv2.TM_SQDIFF, mask=tp["mask"])
        _, _, mn, _ = cv2.minMaxLoc(res)
        val = res[mn[1], mn[0]] / max(int(tp["mask"].sum()), 1)
        if val < best[0]:
            best = (float(val), x0 + mn[0] + tp["hot"][0], y0 + mn[1] + tp["hot"][1], tp["id"])
    return best


def candidates_in(g: np.ndarray, templates: list[dict], scale: float, k: int = 6):
    """The k best-scoring pointer-like spots per template, after non-maximum suppression."""
    import cv2
    out = []
    for tp in templates:
        if tp["k"] != (2 if scale == 2.0 else 1):
            continue
        h, w = tp["img"].shape
        res = cv2.matchTemplate(g, tp["img"], cv2.TM_SQDIFF, mask=tp["mask"])
        res = res / max(int(tp["mask"].sum()), 1)
        res = np.nan_to_num(res, nan=np.inf, posinf=np.inf)
        for _ in range(k):
            _, _, mn, _ = cv2.minMaxLoc(res)
            v = float(res[mn[1], mn[0]])
            if not np.isfinite(v):
                break
            out.append((v, mn[0], mn[1], tp))
            res[max(0, mn[1] - h):mn[1] + h, max(0, mn[0] - w):mn[0] + w] = np.inf
    return sorted(out, key=lambda c: c[0])


def masked_score(g: np.ndarray, tp: dict, x: int, y: int) -> float:
    h, w = tp["img"].shape
    patch = g[y:y + h, x:x + w]
    if patch.shape != (h, w):
        return np.inf
    m = tp["mask"] > 0
    return float(((patch[m].astype(np.float32) - tp["img"][m].astype(np.float32)) ** 2).mean())


def find_moving(g: np.ndarray, refs: list[np.ndarray], templates: list[dict], scale: float):
    """Best pointer-like spot that is NOT there at some other moment.

    Icons that resemble an arrow sit still for the whole recording; the pointer
    comes and goes. A candidate is accepted when, in at least one reference frame
    from seconds before or after, the same spot matches clearly worse."""
    for v, x, y, tp in candidates_in(g, templates, scale):
        other = [masked_score(r, tp, x, y) for r in refs]
        if other and max(other) > 3 * v + 400:
            return v, x + tp["hot"][0], y + tp["hot"][1], tp["id"]
    return np.inf, None, None, None


def track_eval_moving() -> None:
    if KEEP.exists():
        KEEP.unlink()
    templates = load_templates()
    print(f"{len(templates) // 2} pointer templates (plus their 2x copies), moving-pointer rule")
    t0 = time.perf_counter()
    errs, scores, apps = [], [], []
    recs = [r for r in recordings() if not is_train(r[1])]
    for app, tid in recs:
        ev = pointer_events(app, tid)
        if not ev:
            continue
        v = Video(video_of(app, tid))
        s = coord_scale(ev, v.W)
        for t, x, y in rests(ev, v.dur):
            g = v.gray(t)
            if g is None:
                continue
            refs = [r for r in (v.gray(t + d) for d in (-8, -3, 3, 8) if 0 <= t + d <= v.dur)
                    if r is not None and r.shape == g.shape]
            sc, px, py, _ = find_moving(g, refs, templates, s)
            if px is None:
                errs.append(np.inf)
                scores.append(np.inf)
            else:
                errs.append(float(np.hypot(px - x * s, py - y * s)) / s)
                scores.append(sc)
            apps.append(app)
        v.close()
    errs, scores, apps = np.array(errs), np.array(scores), np.array(apps)
    found = np.isfinite(errs)
    print(f"{len(recs)} held-out recordings, {len(errs)} resting pointers, {time.perf_counter() - t0:.0f}s")
    print(f"  pointer found in {found.mean():.1%} of frames")
    for lim in (10, 25, 50):
        print(f"  within {lim:2d} px, over all frames: {(errs <= lim).mean():.1%}   "
              f"over frames where found: {(errs[found] <= lim).mean():.1%}")
    for a in APPS:
        m = apps == a
        if m.any():
            print(f"   {a:10s} {m.sum():4d} rests   found {found[m].mean():.0%}   "
                  f"within 25 px {(errs[m] <= 25).mean():.1%}")


def validate() -> None:
    """On TRAIN recordings only: when each template wins, how often is it right?
    Templates that win mostly in the wrong place are dropped."""
    if KEEP.exists():
        KEEP.unlink()                                  # judge every candidate template afresh
    templates = load_templates()
    wins: dict[int, list[int]] = {}
    for app, tid in [r for r in recordings() if is_train(r[1])]:
        ev = pointer_events(app, tid)
        if not ev:
            continue
        v = Video(video_of(app, tid))
        s = coord_scale(ev, v.W)
        for t, x, y in rests(ev, v.dur):
            g = v.gray(t)
            if g is None:
                continue
            sc, px, py, tid_ = find(g, templates, s)
            if px is not None:
                wins.setdefault(tid_, []).append(int(np.hypot(px - x * s, py - y * s) / s <= 25))
        v.close()
    keep = []
    print(f"{'template':>9s}{'wins':>6s}{'right':>7s}")
    for k in sorted(wins):
        w = wins[k]
        ok = len(w) >= 2 and np.mean(w) >= 0.5
        print(f"{k:9d}{len(w):6d}{np.mean(w):7.0%}   {'kept' if ok else 'dropped'}")
        if ok:
            keep.append(k)
    KEEP.write_text(json.dumps(keep), encoding="utf-8")
    print(f"kept {len(keep)} templates: {keep}")


def track_eval() -> None:
    """At each moment the pointer rests at a logged point, where does the tracker put it?"""
    templates = load_templates()
    print(f"{len(templates) // 2} pointer templates (plus their 2x copies)")
    t0 = time.perf_counter()
    errs, scores = [], []
    per_app: dict[str, list[float]] = {}
    recs = [r for r in recordings() if not is_train(r[1])]
    for app, tid in recs:
        ev = pointer_events(app, tid)
        if not ev:
            continue
        v = Video(video_of(app, tid))
        s = coord_scale(ev, v.W)
        for t, x, y in rests(ev, v.dur):
            g = v.gray(t)
            if g is None:
                continue
            sc, px, py, _ = find(g, templates, s)
            if px is None:
                continue
            e = float(np.hypot(px - x * s, py - y * s)) / s     # in logged (logical) pixels
            errs.append(e)
            scores.append(sc)
            per_app.setdefault(app, []).append(e)
        v.close()
    errs, scores = np.array(errs), np.array(scores)
    print(f"{len(recs)} held-out recordings, {len(errs)} resting pointers, "
          f"{time.perf_counter() - t0:.0f}s")
    for lim in (10, 25, 50):
        print(f"  within {lim:2d} px of the logged point: {(errs <= lim).mean():.1%}")
    print(f"  median error {np.median(errs):.1f} px")
    for app, e in per_app.items():
        e = np.array(e)
        print(f"   {app:10s} {len(e):4d} rests   within 25 px {(e <= 25).mean():.1%}   median {np.median(e):.1f} px")
    good = errs <= 25
    if good.any() and (~good).any():
        print(f"  match score (lower = surer): hits median {np.median(scores[good]):.0f}, "
              f"misses median {np.median(scores[~good]):.0f}")
    print("\n  if frames scoring above a cut-off are treated as 'pointer not found':")
    print(f"  {'cut-off':>9s}{'found':>9s}{'of found, within 25 px':>25s}")
    for cut in (300, 500, 800, 1200, 2000):
        f = scores <= cut
        if f.any():
            print(f"  {cut:9d}{f.mean():9.1%}{(errs[f] <= 25).mean():25.1%}")
    np.savez_compressed(ROOT / "pointer_track_eval_v1.npz", errs=errs, scores=scores)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "harvest":
        harvest(Path(sys.argv[2]))
    elif cmd == "validate":
        validate()
    elif cmd == "track-moving":
        track_eval_moving()
    elif cmd == "track":
        track_eval()
    else:
        raise SystemExit(__doc__)
