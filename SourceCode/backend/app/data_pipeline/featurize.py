from __future__ import annotations

import cv2
import numpy as np

from app.data_pipeline.types import Frame

# NOTE: this is a placeholder featurizer — a small grayscale pixel grid
# (screen state) plus optional frame-to-frame change features,
# not the OCR/UI-detection evidence the real pipeline is designed around
# (see app/data_pipeline/evidence/). It exists so extracted frames can be
# fed through the existing classifiers end-to-end; since those classifiers
# are currently only fit on synthetic data (app.ml.dataset), predictions
# made from these features are not meaningful until real evidence
# extraction and training on labeled data replace both sides.
GRID_SHAPE = (5, 10)  # rows, cols -> 50-d flattened feature vector

# Change features compare each frame with the previous one, so they describe
# what happened (typing, output appearing, pointer moving) rather than what
# the screen looks like. Frames are compared at a fixed width so the mixed
# dataset resolutions (1908x808 ... 2940x1912) produce comparable ratios.
CHANGE_COMPARE_WIDTH = 960
CHANGE_PIXEL_THRESHOLD = 25  # grey-level delta; above JPEG noise, below a typed glyph
CHANGE_DILATE_PX = 7  # merges the glyphs of one typed word / output line into a region
MAX_CHANGE_REGIONS = 50  # region count is divided by this and clipped to [0, 1]
CHANGE_SCALARS = (
    "changed_ratio",  # fraction of pixels that changed
    "mean_abs_diff",  # average intensity change over the whole frame
    "n_regions",  # separate changed areas (many = new output lines / layout change)
    "largest_region_ratio",  # area of the biggest changed region
    "bbox_x0",  # bounding box of all change, normalized to [0, 1]
    "bbox_y0",
    "bbox_x1",
    "bbox_y1",
    "centroid_x",  # centre of mass of the changed pixels
    "centroid_y",
)


def change_feature_dim(grid_shape: tuple[int, int] = GRID_SHAPE) -> int:
    return len(CHANGE_SCALARS) + grid_shape[0] * grid_shape[1]


def _read_gray(frame: Frame) -> np.ndarray:
    image = cv2.imread(str(frame.image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"could not read frame image: {frame.image_path}")
    return image


def _resize_for_compare(image: np.ndarray) -> np.ndarray:
    height, width = image.shape
    new_height = max(1, round(height * CHANGE_COMPARE_WIDTH / width))
    return cv2.resize(image, (CHANGE_COMPARE_WIDTH, new_height), interpolation=cv2.INTER_AREA)


def extract_frame_feature(frame: Frame, grid_shape: tuple[int, int] = GRID_SHAPE) -> np.ndarray:
    image = _read_gray(frame)

    rows, cols = grid_shape
    resized = cv2.resize(image, (cols, rows), interpolation=cv2.INTER_AREA)
    return (resized.astype(np.float32) / 255.0).flatten()


def change_features_from_images(
    prev_image: np.ndarray,
    image: np.ndarray,
    grid_shape: tuple[int, int] = GRID_SHAPE,
) -> np.ndarray:
    """Describe what changed between two grayscale images.

    Returns ``CHANGE_SCALARS`` followed by the changed-pixel ratio of each
    grid cell (row-major), so the vector says how much changed, how it is
    shaped, and where on screen it happened.
    """
    prev_small = _resize_for_compare(prev_image)
    small = _resize_for_compare(image)
    if prev_small.shape != small.shape:
        small = cv2.resize(small, prev_small.shape[::-1], interpolation=cv2.INTER_AREA)

    diff = cv2.absdiff(prev_small, small)
    mask = (diff > CHANGE_PIXEL_THRESHOLD).astype(np.uint8)
    height, width = mask.shape
    n_pixels = height * width

    rows, cols = grid_shape
    cell_ratios = cv2.resize(mask.astype(np.float32), (cols, rows), interpolation=cv2.INTER_AREA)

    changed = int(mask.sum())
    if changed == 0:
        scalars = np.zeros(len(CHANGE_SCALARS), dtype=np.float32)
        scalars[1] = diff.mean() / 255.0
        return np.concatenate([scalars, cell_ratios.flatten()]).astype(np.float32)

    kernel = np.ones((CHANGE_DILATE_PX, CHANGE_DILATE_PX), np.uint8)
    n_labels, _, stats, _ = cv2.connectedComponentsWithStats(cv2.dilate(mask, kernel))
    region_areas = stats[1:, cv2.CC_STAT_AREA]  # label 0 is the background

    ys, xs = np.nonzero(mask)
    scalars = np.array(
        [
            changed / n_pixels,
            diff.mean() / 255.0,
            min(n_labels - 1, MAX_CHANGE_REGIONS) / MAX_CHANGE_REGIONS,
            region_areas.max() / n_pixels,
            xs.min() / width,
            ys.min() / height,
            (xs.max() + 1) / width,
            (ys.max() + 1) / height,
            xs.mean() / width,
            ys.mean() / height,
        ],
        dtype=np.float32,
    )
    return np.concatenate([scalars, cell_ratios.flatten()]).astype(np.float32)


def extract_change_features(
    frames: list[Frame],
    grid_shape: tuple[int, int] = GRID_SHAPE,
) -> np.ndarray:
    """Per-frame change features, ordered by timestamp.

    Row ``i`` describes the change from frame ``i-1`` to frame ``i``; the
    first row is all zeros because there is nothing to compare it with.
    Shape: ``(len(frames), change_feature_dim(grid_shape))``.
    """
    if not frames:
        raise ValueError("no frames to featurize")

    ordered = sorted(frames, key=lambda f: f.timestamp_s)
    features = np.zeros((len(ordered), change_feature_dim(grid_shape)), dtype=np.float32)

    prev_image = _read_gray(ordered[0])
    for i in range(1, len(ordered)):
        image = _read_gray(ordered[i])
        features[i] = change_features_from_images(prev_image, image, grid_shape)
        prev_image = image
    return features


def frames_to_feature_matrix(
    frames: list[Frame],
    n_segments: int = 10,
    grid_shape: tuple[int, int] = GRID_SHAPE,
    include_change: bool = False,
) -> np.ndarray:
    """Bucket frames into ``n_segments`` rows of features.

    Each row is the mean screen-state grid of its frames. With
    ``include_change`` the row also carries the mean and the max of the
    frames' change features: the mean captures sustained activity (typing),
    the max keeps short spikes (command output appearing) from being
    averaged away. Row width is then ``grid + 2 * change_feature_dim``.
    """
    if not frames:
        raise ValueError("no frames to featurize")

    feature_dim = grid_shape[0] * grid_shape[1]
    if include_change:
        feature_dim += 2 * change_feature_dim(grid_shape)
    ordered = sorted(frames, key=lambda f: f.timestamp_s)
    buckets = np.array_split(np.arange(len(ordered)), min(n_segments, len(ordered)))
    change = extract_change_features(ordered, grid_shape) if include_change else None

    rows = []
    for bucket in buckets:
        if len(bucket) == 0:
            continue
        vecs = [extract_frame_feature(ordered[i], grid_shape) for i in bucket]
        row = np.mean(vecs, axis=0)
        if change is not None:
            row = np.concatenate([row, change[bucket].mean(axis=0), change[bucket].max(axis=0)])
        rows.append(row)

    matrix = np.vstack(rows)

    # Pad with repeats of the last segment if the video was too short to
    # fill n_segments buckets, so the shape matches what the classifiers
    # (trained on n_segments x feature_dim synthetic data) expect.
    while matrix.shape[0] < n_segments:
        matrix = np.vstack([matrix, matrix[-1]])

    assert matrix.shape == (n_segments, feature_dim)
    return matrix
