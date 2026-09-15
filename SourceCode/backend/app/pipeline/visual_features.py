from __future__ import annotations

import cv2
import numpy as np

VISUAL_FEATURE_DIM = 40


class VisualFeatureExtractor:
    def extract(self, image: np.ndarray) -> np.ndarray:
        features = np.zeros(VISUAL_FEATURE_DIM, dtype=np.float32)

        if image is None or image.size == 0:
            return features

        h, w = image.shape[:2]
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # [0:18] Color histogram features (6 bins per RGB channel)
        for ch_idx in range(3):
            hist = cv2.calcHist([image], [ch_idx], None, [6], [0, 256])
            hist = hist.flatten() / max(h * w, 1)
            features[ch_idx * 6:(ch_idx + 1) * 6] = hist

        # [18:21] Edge density features
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        total_pixels = h * w

        features[18] = np.count_nonzero(edges) / total_pixels  # overall edge density

        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        features[19] = np.mean(np.abs(sobel_x)) / 255.0  # horizontal edge strength
        features[20] = np.mean(np.abs(sobel_y)) / 255.0  # vertical edge strength

        # [21:27] Texture features (Gabor filter at 3 orientations x 2 frequencies)
        idx = 21
        for theta_deg in [0, 60, 120]:
            for frequency in [0.1, 0.3]:
                theta = np.deg2rad(theta_deg)
                kernel = cv2.getGaborKernel(
                    (21, 21), sigma=4.0, theta=theta,
                    lambd=1.0 / frequency, gamma=0.5, psi=0,
                )
                filtered = cv2.filter2D(gray, cv2.CV_64F, kernel)
                features[idx] = np.mean(np.abs(filtered)) / 255.0
                idx += 1

        # [27:32] Scene features
        features[27] = np.mean(gray) / 255.0  # mean intensity
        features[28] = np.std(gray) / 128.0  # intensity variance (normalized)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        features[29] = np.mean(hsv[:, :, 1]) / 255.0  # color saturation mean
        features[30] = np.std(hsv[:, :, 1]) / 128.0  # color saturation std
        features[31] = np.mean(hsv[:, :, 2]) / 255.0  # brightness

        # [32:40] Layout features (2x2 grid: intensity + edge density per quadrant)
        mid_h, mid_w = h // 2, w // 2
        quadrants = [
            gray[:mid_h, :mid_w],
            gray[:mid_h, mid_w:],
            gray[mid_h:, :mid_w],
            gray[mid_h:, mid_w:],
        ]
        edge_quadrants = [
            edges[:mid_h, :mid_w],
            edges[:mid_h, mid_w:],
            edges[mid_h:, :mid_w],
            edges[mid_h:, mid_w:],
        ]
        for i, (q, eq) in enumerate(zip(quadrants, edge_quadrants)):
            features[32 + i] = np.mean(q) / 255.0
            qsize = max(q.shape[0] * q.shape[1], 1)
            features[36 + i] = np.count_nonzero(eq) / qsize

        return features

    def extract_segment(self, keyframes: list) -> np.ndarray:
        if not keyframes:
            return np.zeros(VISUAL_FEATURE_DIM, dtype=np.float32)

        frame_features = [self.extract(kf.image) for kf in keyframes]
        return np.mean(frame_features, axis=0).astype(np.float32)
