from __future__ import annotations

from pathlib import Path

import cv2

from app.data_pipeline.types import VideoRecord

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def discover_videos(raw_video_dir: Path) -> list[VideoRecord]:
    raw_video_dir = Path(raw_video_dir)
    records: list[VideoRecord] = []

    for path in sorted(raw_video_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            cap.release()
            continue

        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        duration_s = (frame_count / fps) if fps > 0 else 0.0
        cap.release()

        records.append(
            VideoRecord(
                video_id=path.stem,
                source_path=path,
                duration_s=duration_s,
                fps=fps,
            )
        )

    return records
