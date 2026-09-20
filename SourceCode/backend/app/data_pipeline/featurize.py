from __future__ import annotations

import cv2
import numpy as np

from app.data_pipeline.types import Frame

# NOTE: this is a placeholder featurizer — a small grayscale pixel grid,
# not the OCR/UI-detection evidence the real pipeline is designed around
# (see app/data_pipeline/evidence/). It exists so extracted frames can be
# fed through the existing classifiers end-to-end; since those classifiers
# are currently only fit on synthetic data (app.ml.dataset), predictions
# made from these features are not meaningful until real evidence
# extraction and training on labeled data replace both sides.
GRID_SHAPE = (5, 10)  # rows, cols -> 50-d flattened feature vector


def extract_frame_feature(frame: Frame, grid_shape: tuple[int, int] = GRID_SHAPE) -> np.ndarray:
    image = cv2.imread(str(frame.image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"could not read frame image: {frame.image_path}")

    rows, cols = grid_shape
    resized = cv2.resize(image, (cols, rows), interpolation=cv2.INTER_AREA)
    return (resized.astype(np.float32) / 255.0).flatten()


def frames_to_feature_matrix(
    frames: list[Frame],
    n_segments: int = 10,
    grid_shape: tuple[int, int] = GRID_SHAPE,
) -> np.ndarray:
    if not frames:
        raise ValueError("no frames to featurize")

    feature_dim = grid_shape[0] * grid_shape[1]
    ordered = sorted(frames, key=lambda f: f.timestamp_s)
    buckets = np.array_split(np.arange(len(ordered)), min(n_segments, len(ordered)))

    rows = []
    for bucket in buckets:
        if len(bucket) == 0:
            continue
        vecs = [extract_frame_feature(ordered[i], grid_shape) for i in bucket]
        rows.append(np.mean(vecs, axis=0))

    matrix = np.vstack(rows)

    # Pad with repeats of the last segment if the video was too short to
    # fill n_segments buckets, so the shape matches what the classifiers
    # (trained on n_segments x feature_dim synthetic data) expect.
    while matrix.shape[0] < n_segments:
        matrix = np.vstack([matrix, matrix[-1]])

    assert matrix.shape == (n_segments, feature_dim)
    return matrix
