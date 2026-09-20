from __future__ import annotations

from dataclasses import dataclass

from app.data_pipeline.types import AugmentedFrame, Frame


@dataclass
class NoiseBlur:
    name: str = "noise_blur"
    noise_std: float = 0.02
    blur_kernel: int = 3

    def apply(self, frame: Frame) -> AugmentedFrame:
        raise NotImplementedError
