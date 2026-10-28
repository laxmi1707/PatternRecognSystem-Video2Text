"""Run the demo videos through a backend once, so the live demo is answered from the cache.

The backend caches each video's extracted features by its SHA-256 (uploads/feature_cache/),
so uploading the same file again skips OCR and returns in seconds. The cache lives inside
the running task: run this after every deploy, before the demo.

    python scripts/prewarm_demo.py --api https://d3aev25xtfpx7z.cloudfront.net/api/v1 \\
        demo1.mp4 demo2.mp4

Set API_KEY (or pass --api-key) if the backend requires one. Needs httpx (dev dependency).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import httpx


def run_one(client: httpx.Client, video: Path, poll_s: float, timeout_s: float) -> bool:
    t0 = time.perf_counter()
    with open(video, "rb") as f:
        r = client.post("/videos/upload", files={"file": (video.name, f, "video/mp4")})
    r.raise_for_status()
    job_id = r.json()["job_id"]
    client.post(f"/jobs/{job_id}/run").raise_for_status()

    last = ""
    while time.perf_counter() - t0 < timeout_s:
        job = client.get(f"/jobs/{job_id}").json()
        line = f"{job['progress_pct']:5.1f}%  {job.get('progress_stage') or ''}"
        if line != last:
            print(f"  [{time.perf_counter() - t0:6.0f}s] {line}", flush=True)
            last = line
        if job["status"] == "completed":
            print(f"  done in {time.perf_counter() - t0:.0f}s (job {job_id})")
            return True
        if job["status"] == "failed":
            print(f"  FAILED: {job.get('error_message')}")
            return False
        time.sleep(poll_s)
    print(f"  gave up after {timeout_s:.0f}s (job {job_id} still running on the server)")
    return False


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("videos", nargs="+", type=Path, help="video files to run")
    p.add_argument("--api", required=True, help="API base URL, ending in /api/v1")
    p.add_argument("--api-key", default=os.environ.get("API_KEY", ""), help="X-API-Key, if required")
    p.add_argument("--poll", type=float, default=5.0, help="seconds between status checks")
    p.add_argument("--timeout", type=float, default=3600.0, help="seconds to wait per video")
    args = p.parse_args()

    missing = [v for v in args.videos if not v.is_file()]
    if missing:
        print("Not found: " + ", ".join(map(str, missing)))
        return 2

    headers = {"X-API-Key": args.api_key} if args.api_key else {}
    ok = True
    with httpx.Client(base_url=args.api.rstrip("/"), headers=headers, timeout=300.0) as client:
        for video in args.videos:
            print(f"{video.name}")
            ok = run_one(client, video, args.poll, args.timeout) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
