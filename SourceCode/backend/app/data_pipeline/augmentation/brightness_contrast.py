from __future__ import annotations

from dataclasses import dataclass

from app.data_pipeline.types import AugmentedFrame, Frame


@dataclass
class BrightnessContrast:
    name: str = "brightness_contrast"
    brightness_range: tuple[float, float] = (0.7, 1.3)
    contrast_range: tuple[float, float] = (0.7, 1.3)

    def apply(self, frame: Frame) -> AugmentedFrame:
        raise NotImplementedError
