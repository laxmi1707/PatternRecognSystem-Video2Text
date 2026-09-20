from __future__ import annotations

from pathlib import Path

import cv2

from app.data_pipeline.types import Frame, VideoRecord


def extract_frames(video: VideoRecord, output_dir: Path, sample_rate_hz: float = 1.0) -> list[Frame]:
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")

    output_dir = Path(output_dir) / video.video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video.source_path))
    if not cap.isOpened():
        raise RuntimeError(f"could not open video: {video.source_path}")

    native_fps = cap.get(cv2.CAP_PROP_FPS) or video.fps or 1.0
    step = max(1, round(native_fps / sample_rate_hz))

    frames: list[Frame] = []
    native_index = 0
    sampled_index = 0

    try:
        while True:
            ok, image = cap.read()
            if not ok:
                break

            if native_index % step == 0:
                timestamp_s = native_index / native_fps
                image_path = output_dir / f"frame_{sampled_index:06d}.jpg"
                cv2.imwrite(str(image_path), image)

                frames.append(
                    Frame(
                        video_id=video.video_id,
                        frame_index=sampled_index,
                        timestamp_s=timestamp_s,
                        image_path=image_path,
                    )
                )
                sampled_index += 1

            native_index += 1
    finally:
        cap.release()

    return frames
