from __future__ import annotations

import numpy as np


class TemporalEncoder:
    def __init__(self, window_size: int = 1):
        self._window = window_size

    def encode_sequence(self, segment_features: np.ndarray) -> np.ndarray:
        if segment_features.ndim != 2 or segment_features.shape[0] <= 1:
            return segment_features.copy()

        n_segments, n_features = segment_features.shape
        encoded = segment_features.copy()

        for i in range(n_segments):
            neighbors: list[np.ndarray] = []
            for offset in range(-self._window, self._window + 1):
                j = i + offset
                if 0 <= j < n_segments and j != i:
                    neighbors.append(segment_features[j])

            if neighbors:
                neighbor_mean = np.mean(neighbors, axis=0)
                encoded[i] = 0.7 * segment_features[i] + 0.3 * neighbor_mean

        return encoded
