"""A small CNN that recognises the mouse pointer, in any shape, on any background.

Template matching misses about a third of clicks because the harvested templates
are nearly all arrows, while over a button the pointer is a hand and over text
an I-beam (pointer_miss_diag_v1.py). Every logged click is a free, exact label:
at the click's time the pointer's hotspot is at the logged point. So:

    positive    a 32x32 crop (logical px) with the logged click point at (12, 12)
    negatives   per positive: 3 crops elsewhere in the same frame, 2 crops offset
                10-24 px from the hotspot (teaches it to find the tip), and 1 crop
                at the same point in a frame where the pointer is >= 100 px away
                (the same background without the pointer - the hard case)

Crops are grey, taken at logical scale (Retina frames halved). Harvested from the
training split (pointer_tracker_v1.is_train, by task id) of all 87 applications;
the held-out split gives the validation crops.

    python pointer_cnn_v1.py harvest      -> cache/pointer_cnn_v1_crops.npz
    python pointer_cnn_v1.py train        -> cache/pointer_cnn_v1.pt, held-out crop accuracy
"""
from __future__ import annotations

import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

VIDEOS = ROOT / "data" / "VideoCUA"
CROPS = CACHE / "pointer_cnn_v1_crops.npz"
MODEL = CACHE / "pointer_cnn_v1.pt"
SIZE, HOT = 32, 12            # crop size and hotspot position, logical px
CLICKS = {"CLICK", "DOUBLE_CLICK", "RIGHT_CLICK"}
POINTER = CLICKS | {"MOVE_TO", "DRAG_TO", "MOUSE_DOWN", "MOUSE_UP"}
PER_APP = 60                  # recordings per application and split
PER_REC = 4                   # clicks per recording
WORKERS = 6


def is_train(tid: int) -> bool:
    return (tid * 2654435761 % 10) < 7          # as pointer_tracker_v1


def recordings() -> list[tuple[str, int]]:
    out = []
    for a in sorted(p for p in VIDEOS.iterdir() if p.is_dir()):
        for log in sorted(a.glob("*/action_log.json")):
            if (log.parent / "video" / "video.mp4").exists() and log.parent.name.isdigit():
                out.append((a.name, int(log.parent.name)))
    return out


def events(app: str, tid: int) -> list[dict]:
    """Pointer events with coordinates, from action_log.json (works for all 87 apps)."""
    log = json.loads((VIDEOS / app / str(tid) / "action_log.json").read_text(encoding="utf-8"))
    out = []
    for a in log.get("action_log", []):
        prm = a.get("action_params") or {}
        kind = (a.get("action_type") or "").upper()
        if kind in POINTER and prm.get("x") is not None and a.get("timestamp") is not None:
            out.append({"t": float(a["timestamp"]), "x": float(prm["x"]), "y": float(prm["y"]), "type": kind})
    return sorted(out, key=lambda e: e["t"])


def coord_scale(ev: list[dict], W: float) -> float:
    xs = [e["x"] for e in ev]
    return 2.0 if xs and W > 2000 and max(xs) < W / 2 + 40 else 1.0


def crop(g: np.ndarray, X: float, Y: float, s: float) -> np.ndarray | None:
    """SIZE x SIZE logical-px crop of grey frame g with native point (X, Y) at (HOT, HOT)."""
    import cv2
    x0, y0 = int(round(X - HOT * s)), int(round(Y - HOT * s))
    w = int(round(SIZE * s))
    if x0 < 0 or y0 < 0 or x0 + w > g.shape[1] or y0 + w > g.shape[0]:
        return None
    c = g[y0:y0 + w, x0:x0 + w]
    return c if s == 1.0 else cv2.resize(c, (SIZE, SIZE), interpolation=cv2.INTER_AREA)


def _harvest_one(job):
    import cv2
    cv2.setNumThreads(1)
    app, tid = job
    rng = random.Random(tid)
    ev = events(app, tid)
    clicks = [e for e in ev if e["type"] in CLICKS]
    if not clicks:
        return app, tid, [], []
    cap = cv2.VideoCapture(str(VIDEOS / app / str(tid) / "video" / "video.mp4"))
    W, H = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    s = coord_scale(ev, W)

    def gray(t):
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000)
        ok, f = cap.read()
        return cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if ok else None

    X_, y_ = [], []
    for c in rng.sample(clicks, min(PER_REC, len(clicks))):
        g = gray(c["t"])
        if g is None:
            continue
        X, Y = c["x"] * s, c["y"] * s
        pos = crop(g, X, Y, s)
        if pos is None:
            continue
        X_.append(pos), y_.append(1)
        for _ in range(3):                                   # elsewhere in the frame
            for _try in range(10):
                rx, ry = rng.uniform(0, W), rng.uniform(0, H)
                if np.hypot(rx - X, ry - Y) > 60 * s:
                    n = crop(g, rx, ry, s)
                    if n is not None:
                        X_.append(n), y_.append(0)
                        break
        for _ in range(2):                                   # near, but not on, the hotspot
            r, a = rng.uniform(10, 24) * s, rng.uniform(0, 2 * np.pi)
            n = crop(g, X + r * np.cos(a), Y + r * np.sin(a), s)
            if n is not None:
                X_.append(n), y_.append(0)
        far = [e for e in ev if abs(e["t"] - c["t"]) < 20 and np.hypot(e["x"] - c["x"], e["y"] - c["y"]) > 100]
        if far:                                              # same place, pointer elsewhere
            g2 = gray(rng.choice(far)["t"])
            n = crop(g2, X, Y, s) if g2 is not None else None
            if n is not None:
                X_.append(n), y_.append(0)
    cap.release()
    return app, tid, X_, y_


def harvest() -> None:
    recs = recordings()
    rng = random.Random(0)
    jobs = []
    for app in sorted({a for a, _ in recs}):
        for split in (True, False):
            pool = [r for r in recs if r[0] == app and is_train(r[1]) == split]
            jobs += rng.sample(pool, min(PER_APP if split else PER_APP // 4, len(pool)))
    t0 = time.perf_counter()
    X, y, train, app_of = [], [], [], []
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        for i, (app, tid, xs, ys) in enumerate(ex.map(_harvest_one, jobs, chunksize=4), 1):
            X += xs
            y += ys
            train += [is_train(tid)] * len(xs)
            app_of += [app] * len(xs)
            if i % 300 == 0:
                print(f"  {i}/{len(jobs)} recordings, {len(X)} crops, {time.perf_counter() - t0:.0f}s", flush=True)
    np.savez_compressed(CROPS, X=np.stack(X).astype(np.uint8), y=np.array(y, np.int8),
                        train=np.array(train), app=np.array(app_of))
    y = np.array(y)
    tr = np.array(train)
    print(f"{len(jobs)} recordings -> {len(y)} crops ({y.sum()} pointer), train {tr.sum()}, "
          f"held-out {(~tr).sum()}, {time.perf_counter() - t0:.0f}s")


# ---------------------------------------------------------------- model

def net():
    import torch.nn as nn

    def block(i, o):
        return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(),
                             nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(2))
    return nn.Sequential(block(1, 16), block(16, 32), block(32, 64),       # 32 -> 4
                         nn.Flatten(), nn.Linear(64 * 4 * 4, 64), nn.ReLU(), nn.Dropout(0.2),
                         nn.Linear(64, 1))


def to_tensor(X: np.ndarray):
    import torch
    return torch.from_numpy(X.astype(np.float32) / 255.0).unsqueeze(1)


def load_model():
    import torch
    m = net()
    m.load_state_dict(torch.load(MODEL, map_location="cpu"))
    m.eval()
    return m


def train() -> None:
    import torch
    torch.set_num_threads(12)
    torch.manual_seed(0)
    z = np.load(CROPS)
    X, y, tr, app = z["X"], z["y"].astype(np.float32), z["train"], z["app"]
    Xtr, ytr = to_tensor(X[tr]), torch.from_numpy(y[tr])
    Xte, yte = to_tensor(X[~tr]), y[~tr]
    m = net()
    opt = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=1e-4)
    pos_w = torch.tensor([(ytr == 0).sum() / max((ytr == 1).sum(), 1)])
    lossf = torch.nn.BCEWithLogitsLoss(pos_weight=pos_w)
    EPOCHS, B = 8, 256
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=EPOCHS * (len(ytr) // B + 1))
    t0 = time.perf_counter()
    for ep in range(EPOCHS):
        m.train()
        perm = torch.randperm(len(ytr))
        tot = 0.0
        for i in range(0, len(ytr), B):
            idx = perm[i:i + B]
            xb = Xtr[idx]
            # brightness / contrast jitter: themes and compression differ between recordings
            xb = (xb - 0.5) * torch.empty(len(idx), 1, 1, 1).uniform_(0.7, 1.3) + 0.5 \
                + torch.empty(len(idx), 1, 1, 1).uniform_(-0.1, 0.1)
            loss = lossf(m(xb.clamp(0, 1)).squeeze(1), ytr[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            tot += loss.item() * len(idx)
        p = predict(m, Xte)
        print(f"epoch {ep + 1}: loss {tot / len(ytr):.4f}, held-out AUC {auc(p, yte):.4f}, "
              f"{time.perf_counter() - t0:.0f}s", flush=True)
    torch.save(m.state_dict(), MODEL)
    p = predict(m, Xte)
    print(f"\nheld-out crops: {len(yte)} ({int(yte.sum())} pointer), AUC {auc(p, yte):.4f}")
    for thr in (0.5, 0.8, 0.9):
        k = p >= thr
        print(f"  p >= {thr}: pointer crops found {k[yte == 1].mean():.1%}, "
              f"non-pointer crops passed {k[yte == 0].mean():.2%}")
    # per kind of negative is not stored; per application, the pointer recall at 0.5
    apps, k = app[~tr], p >= 0.5
    worst = sorted((k[(apps == a) & (yte == 1)].mean(), a)
                   for a in set(apps.tolist()) if ((apps == a) & (yte == 1)).sum() >= 10)[:8]
    print("  lowest pointer recall at 0.5 by application:", ", ".join(f"{a} {r:.0%}" for r, a in worst))
    print(f"saved {MODEL.name}")


def predict(m, X) -> np.ndarray:
    import torch
    m.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(X), 4096):
            out.append(torch.sigmoid(m(X[i:i + 4096]).squeeze(1)).numpy())
    return np.concatenate(out)


def auc(score: np.ndarray, label: np.ndarray) -> float:
    order = np.argsort(score, kind="stable")
    ranks = np.empty(len(score))
    ranks[order] = np.arange(1, len(score) + 1)
    n1 = label.sum()
    n0 = len(label) - n1
    return float((ranks[label == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


if __name__ == "__main__":
    {"harvest": harvest, "train": train}[sys.argv[1]]()
