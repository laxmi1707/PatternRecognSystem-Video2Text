from __future__ import annotations

import cv2

from app.data_pipeline.types import Frame

MIN_INTENSITY_STD = 4.0  # near-uniform (blank/black/frozen) frames fall below this


def is_usable_frame(frame: Frame) -> bool:
    image = cv2.imread(str(frame.image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return False

    return bool(image.std() >= MIN_INTENSITY_STD)


def clean_frames(frames: list[Frame]) -> list[Frame]:
    return [frame for frame in frames if is_usable_frame(frame)]
