"""Frame-to-frame change features: what changed on screen, how much, and where.

The other visual extractors describe a single frame (what the screen looks like).
User actions show up as *differences* between frames instead: typing changes a
small area at the text cursor, pressing Enter adds lines of output, a pointer move
changes only the cursor sprite, a click changes the UI near the pointer. These
features describe such a difference so a classifier can tell the actions apart.

Frames are compared at a fixed width so the dataset's mixed resolutions
(1908x808 ... 2940x1912) produce comparable values.
"""
from __future__ import annotations

import cv2
import numpy as np

COMPARE_WIDTH = 640
PIXEL_THRESHOLD = 25  # grey-level delta; above video-compression noise, below a typed glyph
DILATE_PX = 5  # merges the glyphs of one typed word / output line into one region
MAX_REGIONS = 50  # region count is divided by this and clipped to [0, 1]
GRID_SHAPE = (4, 8)  # rows, cols of the "where did it change" map

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
CHANGE_FEATURE_DIM = len(CHANGE_SCALARS) + GRID_SHAPE[0] * GRID_SHAPE[1]


def to_compare_gray(image: np.ndarray) -> np.ndarray:
    """Grayscale, resized to COMPARE_WIDTH keeping the aspect ratio."""
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    new_h = max(1, round(h * COMPARE_WIDTH / w))
    return cv2.resize(gray, (COMPARE_WIDTH, new_h), interpolation=cv2.INTER_AREA)


def change_features(prev_gray: np.ndarray, gray: np.ndarray) -> np.ndarray:
    """Describe the change between two images produced by ``to_compare_gray``.

    Returns ``CHANGE_SCALARS`` followed by the changed-pixel ratio of each grid
    cell (row-major): how much changed, how it is shaped, and where it happened.
    """
    if prev_gray.shape != gray.shape:
        gray = cv2.resize(gray, prev_gray.shape[::-1], interpolation=cv2.INTER_AREA)

    diff = cv2.absdiff(prev_gray, gray)
    mask = (diff > PIXEL_THRESHOLD).astype(np.uint8)
    h, w = mask.shape
    rows, cols = GRID_SHAPE
    cells = cv2.resize(mask.astype(np.float32), (cols, rows), interpolation=cv2.INTER_AREA)

    scalars = np.zeros(len(CHANGE_SCALARS), dtype=np.float32)
    scalars[1] = diff.mean() / 255.0
    changed = int(mask.sum())
    if changed:
        kernel = np.ones((DILATE_PX, DILATE_PX), np.uint8)
        n_labels, _, stats, _ = cv2.connectedComponentsWithStats(cv2.dilate(mask, kernel))
        areas = stats[1:, cv2.CC_STAT_AREA]  # label 0 is the background
        ys, xs = np.nonzero(mask)
        scalars[0] = changed / (h * w)
        scalars[2] = min(n_labels - 1, MAX_REGIONS) / MAX_REGIONS
        scalars[3] = areas.max() / (h * w)
        scalars[4:8] = (xs.min() / w, ys.min() / h, (xs.max() + 1) / w, (ys.max() + 1) / h)
        scalars[8:10] = (xs.mean() / w, ys.mean() / h)

    return np.concatenate([scalars, cells.flatten()]).astype(np.float32)
