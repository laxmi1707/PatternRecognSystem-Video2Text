from __future__ import annotations

from dataclasses import dataclass

from app.data_pipeline.types import AugmentedFrame, Frame


@dataclass
class Compression:
    name: str = "compression"
    quality_range: tuple[int, int] = (40, 90)

    def apply(self, frame: Frame) -> AugmentedFrame:
        raise NotImplementedError
