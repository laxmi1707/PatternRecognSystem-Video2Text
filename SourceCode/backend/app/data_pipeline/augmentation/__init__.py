from app.data_pipeline.augmentation.base import Augmentation
from app.data_pipeline.augmentation.brightness_contrast import BrightnessContrast
from app.data_pipeline.augmentation.compression import Compression
from app.data_pipeline.augmentation.crop_scale import CropScale
from app.data_pipeline.augmentation.noise_blur import NoiseBlur
from app.data_pipeline.augmentation.ui_layout import UILayoutVariation

DEFAULT_AUGMENTATIONS: tuple[Augmentation, ...] = (
    CropScale(),
    BrightnessContrast(),
    NoiseBlur(),
    Compression(),
    UILayoutVariation(),
)

__all__ = [
    "Augmentation",
    "BrightnessContrast",
    "Compression",
    "CropScale",
    "NoiseBlur",
    "UILayoutVariation",
    "DEFAULT_AUGMENTATIONS",
]
