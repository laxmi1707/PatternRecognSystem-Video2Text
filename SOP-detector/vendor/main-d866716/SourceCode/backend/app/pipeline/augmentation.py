from __future__ import annotations

import numpy as np


def build_train_augmentation():
    try:
        import albumentations as A

        return A.Compose([
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.3),
            A.GaussNoise(var_limit=(5.0, 25.0), p=0.2),
            A.ImageCompression(quality_lower=70, quality_upper=100, p=0.15),
            A.ShiftScaleRotate(
                shift_limit=0.02, scale_limit=0.05, rotate_limit=2, p=0.2
            ),
        ])
    except ImportError:
        return None


def build_eval_augmentation():
    return None


def augment_features(
    X: np.ndarray,
    y: np.ndarray,
    n_augmented: int = 2,
    noise_std: float = 0.05,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)

    aug_X_parts = [X]
    aug_y_parts = [y]

    for _ in range(n_augmented):
        noise = rng.randn(*X.shape).astype(np.float32) * noise_std
        aug_X_parts.append(X + noise)
        aug_y_parts.append(y.copy())

    X_aug = np.vstack(aug_X_parts)
    y_aug = np.concatenate(aug_y_parts)

    shuffle_idx = rng.permutation(len(y_aug))
    return X_aug[shuffle_idx], y_aug[shuffle_idx]
