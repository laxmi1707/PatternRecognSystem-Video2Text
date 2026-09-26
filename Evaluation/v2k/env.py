"""Where things live, which backend snapshot is used, and how much CPU we take."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIPS = ROOT / "data" / "zips"
VIDEOS = ROOT / "data" / "VideoCUA"
WEIGHTS = ROOT / "weights"
CACHE = ROOT / "cache"
RUNS = ROOT / "runs"

# Features are only comparable when the same backend code computed them, so the
# snapshot id is part of the cache path: a new snapshot starts a fresh cache.
BACKEND_SNAPSHOT = os.environ.get("V2K_BACKEND_SNAPSHOT", "main-d866716")
BACKEND = ROOT / "vendor" / BACKEND_SNAPSHOT / "SourceCode" / "backend"

# Bump when the per-frame record written by frames.py changes shape.
FRAME_SCHEMA = 1

# Half of the workstation by default; V2K_MAX_THREADS raises it for the hours
# the user has said the machine is free (it belongs to his team lead).
MAX_THREADS = int(os.environ.get("V2K_MAX_THREADS", "16"))


def frame_cache_dir() -> Path:
    return CACHE / f"frames_v{FRAME_SCHEMA}_{BACKEND_SNAPSHOT}"


def backend_commit() -> str:
    marker = BACKEND.parent.parent / "COMMIT"
    return marker.read_text().strip() if marker.exists() else "unknown"


def use_backend() -> None:
    """Make the team's backend importable as `app`."""
    if not BACKEND.is_dir():
        raise SystemExit(f"backend snapshot not found: {BACKEND}")
    path = str(BACKEND)
    if path not in sys.path:
        sys.path.insert(0, path)


def limit_cpu(threads: int) -> None:
    """Cap math-library threads and drop to below-normal priority.

    Must run before numpy or torch is imported for the caps to apply. Worker
    processes inherit both the environment and the priority class.
    """
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[var] = str(threads)
    # RandomForest and KNN pass n_jobs=-1, which asks joblib for every core and
    # so ignores the caps above. joblib reads this one, so the cap holds for
    # them too - it matters most when several tuning shards run side by side.
    os.environ["LOKY_MAX_CPU_COUNT"] = str(threads)
    try:
        import psutil

        proc = psutil.Process()
        proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if sys.platform == "win32" else 10)
    except Exception:
        pass
