from __future__ import annotations

import math

import numpy as np

from app.ml.dataset_loader import ActionRecord

INTERACTION_FEATURE_DIM = 30

ACTION_TYPES = [
    "CLICK", "MOVE_TO", "TYPING", "DRAG_TO",
    "HOTKEY", "PRESS", "MOUSE_DOWN", "MOUSE_UP",
]
_ACTION_INDEX = {a: i for i, a in enumerate(ACTION_TYPES)}


class InteractionFeatureExtractor:
    def __init__(self, screen_width: int = 2940, screen_height: int = 1912):
        self._sw = screen_width
        self._sh = screen_height

    def extract(
        self, actions: list[ActionRecord], segment_start: float, segment_end: float
    ) -> np.ndarray:
        features = np.zeros(INTERACTION_FEATURE_DIM, dtype=np.float32)

        seg_actions = [
            a for a in actions if segment_start <= a.timestamp <= segment_end
        ]

        if not seg_actions:
            return features

        # [0:8] Action type counts (normalized by total)
        total = len(seg_actions)
        for a in seg_actions:
            idx = _ACTION_INDEX.get(a.action_type.upper(), -1)
            if idx >= 0:
                features[idx] += 1
        if total > 0:
            features[:8] /= total

        # [8:12] Click position stats (normalized)
        click_xs: list[float] = []
        click_ys: list[float] = []
        for a in seg_actions:
            x = a.params.get("x")
            y = a.params.get("y")
            if x is not None and y is not None:
                click_xs.append(float(x) / self._sw)
                click_ys.append(float(y) / self._sh)

        if click_xs:
            features[8] = np.mean(click_xs)
            features[9] = np.mean(click_ys)
            features[10] = np.std(click_xs) if len(click_xs) > 1 else 0.0
            features[11] = np.std(click_ys) if len(click_ys) > 1 else 0.0

        # [12:18] Temporal features
        duration = segment_end - segment_start
        features[12] = min(duration / 30.0, 1.0)  # normalized duration
        features[13] = min(total / 20.0, 1.0)  # normalized action count
        features[14] = min(total / max(duration, 0.01), 1.0)  # actions per second

        timestamps = sorted(a.timestamp for a in seg_actions)
        if len(timestamps) > 1:
            intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
            features[15] = min(np.mean(intervals) / 5.0, 1.0)
            features[16] = min(np.std(intervals) / 3.0, 1.0)

        n_typing = sum(1 for a in seg_actions if a.action_type.upper() == "TYPING")
        n_clicks = sum(1 for a in seg_actions if a.action_type.upper() == "CLICK")
        features[17] = n_typing / max(n_clicks, 1)

        # [18:24] Mouse movement features
        pos_with_ts: list[tuple[float, float, float]] = []
        for a in seg_actions:
            x = a.params.get("x")
            y = a.params.get("y")
            if x is not None and y is not None:
                pos_with_ts.append((float(x), float(y), a.timestamp))

        positions = [(p[0], p[1]) for p in pos_with_ts]

        if len(positions) > 1:
            total_dist = 0.0
            speeds: list[float] = []
            dir_changes = 0
            prev_dx, prev_dy = 0.0, 0.0

            for i in range(1, len(positions)):
                dx = positions[i][0] - positions[i - 1][0]
                dy = positions[i][1] - positions[i - 1][1]
                dist = math.sqrt(dx * dx + dy * dy)
                total_dist += dist

                dt = max(pos_with_ts[i][2] - pos_with_ts[i - 1][2], 0.01)
                speeds.append(dist / dt)

                if i > 1 and (dx * prev_dx + dy * prev_dy) < 0:
                    dir_changes += 1
                prev_dx, prev_dy = dx, dy

            max_diag = math.sqrt(self._sw**2 + self._sh**2)
            features[18] = min(total_dist / max_diag, 1.0)
            features[19] = min(np.mean(speeds) / 2000.0, 1.0) if speeds else 0.0
            features[20] = min(max(speeds) / 5000.0, 1.0) if speeds else 0.0
            features[21] = min(dir_changes / 10.0, 1.0)
            displacements_x = [positions[i][0] - positions[i - 1][0] for i in range(1, len(positions))]
            displacements_y = [positions[i][1] - positions[i - 1][1] for i in range(1, len(positions))]
            features[22] = np.mean(displacements_x) / max_diag
            features[23] = np.mean(displacements_y) / max_diag

        # [24:28] Typing features
        total_chars = 0
        text_segments = 0
        for a in seg_actions:
            if a.action_type.upper() == "TYPING":
                text = a.params.get("text", "")
                total_chars += len(text)
                text_segments += 1

        features[24] = min(total_chars / 100.0, 1.0)
        typing_dur = sum(
            (a.t_end or a.timestamp) - a.timestamp
            for a in seg_actions
            if a.action_type.upper() == "TYPING"
        )
        features[25] = min(total_chars / max(typing_dur, 0.01) / 20.0, 1.0)
        features[26] = min(text_segments / 5.0, 1.0)
        features[27] = 1.0 if n_typing > 0 else 0.0

        # [28:30] Keyboard features
        features[28] = min(
            sum(1 for a in seg_actions if a.action_type.upper() == "HOTKEY") / 5.0, 1.0
        )
        features[29] = min(
            sum(1 for a in seg_actions if a.action_type.upper() == "PRESS") / 10.0, 1.0
        )

        return features
