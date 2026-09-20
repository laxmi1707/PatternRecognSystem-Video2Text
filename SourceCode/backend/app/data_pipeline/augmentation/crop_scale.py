from __future__ import annotations

from dataclasses import dataclass

from app.data_pipeline.types import AugmentedFrame, Frame


@dataclass
class CropScale:
    name: str = "crop_scale"
    min_scale: float = 0.8
    max_scale: float = 1.0

    def apply(self, frame: Frame) -> AugmentedFrame:
        raise NotImplementedError
