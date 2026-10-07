from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.data_pipeline.featurize import (
    CHANGE_SCALARS,
    GRID_SHAPE,
    change_feature_dim,
    change_features_from_images,
    extract_change_features,
    frames_to_feature_matrix,
)
from app.data_pipeline.types import Frame

IDX = {name: i for i, name in enumerate(CHANGE_SCALARS)}
N_SCALARS = len(CHANGE_SCALARS)


def _terminal(height: int = 800, width: int = 1900) -> np.ndarray:
    """Dark screen with a prompt line, like the Bash dataset videos."""
    image = np.full((height, width), 30, dtype=np.uint8)
    cv2.rectangle(image, (0, 30), (width // 4, 50), 180, -1)
    return image


def _write_frames(tmp_path: Path, images: list[np.ndarray]) -> list[Frame]:
    frames = []
    for i, image in enumerate(images):
        path = tmp_path / f"frame_{i:06d}.png"
        cv2.imwrite(str(path), image)
        frames.append(Frame(video_id="v", frame_index=i, timestamp_s=i * 0.2, image_path=path))
    return frames


def test_identical_frames_report_no_change():
    image = _terminal()
    feat = change_features_from_images(image, image.copy())

    assert feat.shape == (change_feature_dim(),)
    assert np.all(feat == 0)


def test_typed_character_is_small_change_at_its_location():
    before = _terminal()
    after = before.copy()
    cv2.rectangle(after, (480, 30), (500, 50), 255, -1)  # one glyph after the prompt

    feat = change_features_from_images(before, after)

    assert 0 < feat[IDX["changed_ratio"]] < 0.001
    assert feat[IDX["n_regions"]] * 50 == 1
    assert feat[IDX["bbox_x0"]] == pytest.approx(480 / 1900, abs=0.01)
    assert feat[IDX["bbox_y0"]] == pytest.approx(30 / 800, abs=0.01)
    # the change sits in the top-left quarter of the grid, nowhere else
    cells = feat[N_SCALARS:].reshape(GRID_SHAPE)
    assert cells[0, :3].sum() > 0
    assert cells[1:, :].sum() == 0 and cells[:, 3:].sum() == 0


def test_command_output_is_larger_multi_region_change_than_typing():
    before = _terminal()
    typed = before.copy()
    cv2.rectangle(typed, (480, 30), (500, 50), 255, -1)
    output = typed.copy()
    for x in range(0, 1800, 200):  # a row of file names, like `ls` output
        cv2.rectangle(output, (x, 70), (x + 140, 90), 200, -1)

    typing = change_features_from_images(before, typed)
    execute = change_features_from_images(typed, output)

    assert execute[IDX["changed_ratio"]] > 10 * typing[IDX["changed_ratio"]]
    assert execute[IDX["n_regions"]] > typing[IDX["n_regions"]]
    assert execute[IDX["bbox_y0"]] > typing[IDX["bbox_y0"]]  # output appears below the prompt


def test_change_ratios_do_not_depend_on_resolution():
    def pair(height: int, width: int) -> tuple[np.ndarray, np.ndarray]:
        before = np.full((height, width), 30, dtype=np.uint8)
        after = before.copy()
        cv2.rectangle(after, (width // 2, height // 2), (width // 2 + width // 10, height // 2 + height // 10), 220, -1)
        return before, after

    low = change_features_from_images(*pair(808, 1908))
    high = change_features_from_images(*pair(1912, 2940))

    assert low[: N_SCALARS] == pytest.approx(high[: N_SCALARS], abs=0.01)


def test_extract_change_features_first_row_is_zero_and_rows_follow_time(tmp_path):
    before = _terminal()
    after = before.copy()
    cv2.rectangle(after, (480, 30), (500, 50), 255, -1)
    frames = _write_frames(tmp_path, [before, before, after])

    change = extract_change_features(list(reversed(frames)))  # order must come from timestamps

    assert change.shape == (3, change_feature_dim())
    assert np.all(change[0] == 0)
    assert np.all(change[1] == 0)
    assert change[2, IDX["changed_ratio"]] > 0


def test_frames_to_feature_matrix_default_shape_unchanged(tmp_path):
    frames = _write_frames(tmp_path, [_terminal() for _ in range(4)])

    matrix = frames_to_feature_matrix(frames, n_segments=2)

    assert matrix.shape == (2, GRID_SHAPE[0] * GRID_SHAPE[1])


def test_frames_to_feature_matrix_with_change_keeps_spikes(tmp_path):
    before = _terminal()
    output = before.copy()
    cv2.rectangle(output, (0, 70), (1800, 90), 200, -1)
    # bucket 0: no change; bucket 1: one big change between its two frames
    frames = _write_frames(tmp_path, [before, before, before, output])

    matrix = frames_to_feature_matrix(frames, n_segments=2, include_change=True)

    grid = GRID_SHAPE[0] * GRID_SHAPE[1]
    dim = change_feature_dim()
    assert matrix.shape == (2, grid + 2 * dim)
    mean_ratio = matrix[:, grid + IDX["changed_ratio"]]
    max_ratio = matrix[:, grid + dim + IDX["changed_ratio"]]
    assert max_ratio[0] == 0 and mean_ratio[0] == 0
    assert max_ratio[1] > mean_ratio[1] > 0
