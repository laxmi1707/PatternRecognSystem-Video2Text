"""The whole SOP detector on one video: typing + clicks -> steps in time order.

    python -m detector VIDEO [--out steps.json]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from v2k.env import use_backend

from detector.clicks import click_steps
from detector.typed_text import typing_steps


def run(video: Path, progress=lambda pct, stage: None) -> dict:
    """{video, app, app_confidence, duration, seconds_taken, seconds_clicks, steps}."""
    use_backend()
    from app.pipeline.ocr_extractor import OCRExtractor
    t0 = time.perf_counter()
    typed = typing_steps(video, progress)
    t1 = time.perf_counter()
    clicks = click_steps(video, OCRExtractor(), progress)
    progress(90, "writing the SOP")
    return {"video": video.name, "app": typed["app"], "app_confidence": typed["app_confidence"],
            "duration": typed["duration"], "seconds_taken": round(time.perf_counter() - t0, 1),
            "seconds_clicks": round(time.perf_counter() - t1, 1),
            "steps": sorted(typed["steps"] + clicks, key=lambda k: k["t"])}


def main() -> None:
    from v2k.env import limit_cpu
    limit_cpu(12)
    ap = argparse.ArgumentParser(prog="python -m detector")
    ap.add_argument("video")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = run(Path(a.video), lambda pct, stage: print(f"  {pct:3d}%  {stage}", flush=True))
    js = json.dumps(res, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(js, encoding="utf-8")
    print(js)
