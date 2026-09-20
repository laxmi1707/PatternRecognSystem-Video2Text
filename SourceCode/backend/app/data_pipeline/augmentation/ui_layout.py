from __future__ import annotations

from dataclasses import dataclass, field

from app.data_pipeline.types import AugmentedFrame, Frame


@dataclass
class UILayoutVariation:
    name: str = "ui_layout"
    layout_variants: tuple[str, ...] = field(
        default_factory=lambda: ("theme_dark", "theme_light", "font_scale", "panel_resize")
    )

    def apply(self, frame: Frame) -> AugmentedFrame:
        raise NotImplementedError
