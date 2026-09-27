"""Run the local ingestion pipeline (discover -> extract -> clean -> featurize)
on a raw video and classify it with the existing ML registry.

Usage:
    python scripts/analyze_video.py [--video-dir localDataset] [--model svm]

The featurizer is a placeholder (see app/data_pipeline/featurize.py) and the
classifiers are only fit on synthetic data (app/ml/dataset.py), so the
predicted label below is a plumbing check, not a trustworthy result, until
real evidence extraction (OCR / UI detection) and training on a labeled
dataset are wired in.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.data_pipeline.cleaning import clean_frames
from app.data_pipeline.featurize import frames_to_feature_matrix
from app.data_pipeline.frame_extraction import extract_frames
from app.data_pipeline.ingestion import discover_videos
from app.services.ml_service import ml_service


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-dir", default=str(BACKEND_ROOT / "localDataset"))
    parser.add_argument("--model", default="svm", help="registered model name, e.g. svm, random_forest, mlp")
    parser.add_argument("--sample-rate-hz", type=float, default=5.0)
    parser.add_argument("--n-segments", type=int, default=10)
    args = parser.parse_args()

    video_dir = Path(args.video_dir)
    videos = discover_videos(video_dir)
    if not videos:
        print(f"no videos found in {video_dir}")
        return

    with tempfile.TemporaryDirectory(prefix="frames_") as frame_dir:
        for video in videos:
            print(f"\n=== {video.video_id} ({video.source_path.name}) ===")
            print(f"duration: {video.duration_s:.1f}s  fps: {video.fps:.2f}")

            frames = extract_frames(video, Path(frame_dir), sample_rate_hz=args.sample_rate_hz)
            usable = clean_frames(frames)
            print(f"extracted {len(frames)} frames, {len(usable)} usable after cleaning")

            if not usable:
                print("no usable frames, skipping classification")
                continue

            X = frames_to_feature_matrix(usable, n_segments=args.n_segments)
            result = ml_service.classify(X, model_name=args.model)

            print(f"model: {result['model_name']}  latency: {result['latency_ms']:.2f}ms")
            segment_s = video.duration_s / args.n_segments
            for i, pred in enumerate(result["results"]):
                start, end = i * segment_s, (i + 1) * segment_s
                print(f"  segment {i:2d} [{start:5.1f}s-{end:5.1f}s]: {pred['label']:<18} confidence={pred['confidence']:.3f}")


if __name__ == "__main__":
    main()
