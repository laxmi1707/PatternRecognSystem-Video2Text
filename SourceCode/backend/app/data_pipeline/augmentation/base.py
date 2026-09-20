from __future__ import annotations

from typing import Protocol

from app.data_pipeline.types import AugmentedFrame, Frame


class Augmentation(Protocol):
    name: str

    def apply(self, frame: Frame) -> AugmentedFrame: ...
