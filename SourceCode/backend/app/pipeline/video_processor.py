from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np


@dataclass
class FrameData:
    frame_index: int
    timestamp: float
    image: np.ndarray  # (H, W, 3) BGR


@dataclass
class SegmentData:
    segment_index: int
    start_time: float
    end_time: float
    keyframes: list[FrameData] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)


class VideoProcessor:
    def __init__(
        self,
        sample_fps: float = 1.0,
        target_size: tuple[int, int] = (640, 480),
        cluster_gap: float = 2.0,
    ):
        self._sample_fps = sample_fps
        self._target_size = target_size
        self._cluster_gap = cluster_gap

    def get_metadata(self, video_path: Path) -> dict:
        cap = cv2.VideoCapture(str(video_path))
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0.0
            return {
                "fps": fps,
                "total_frames": total_frames,
                "width": width,
                "height": height,
                "duration_seconds": duration,
            }
        finally:
            cap.release()

    def extract_frame_at(self, video_path: Path, timestamp: float) -> FrameData | None:
        cap = cv2.VideoCapture(str(video_path))
        try:
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            if not ret:
                return None
            frame = cv2.resize(frame, self._target_size)
            frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            return FrameData(frame_index=frame_idx, timestamp=timestamp, image=frame)
        finally:
            cap.release()

    def extract_frames(self, video_path: Path) -> list[FrameData]:
        cap = cv2.VideoCapture(str(video_path))
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                return []
            frame_interval = int(fps / self._sample_fps)
            if frame_interval < 1:
                frame_interval = 1

            frames: list[FrameData] = []
            idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if idx % frame_interval == 0:
                    frame = cv2.resize(frame, self._target_size)
                    timestamp = idx / fps
                    frames.append(FrameData(frame_index=idx, timestamp=timestamp, image=frame))
                idx += 1
            return frames
        finally:
            cap.release()

    def _cluster_actions(self, actions: list[dict]) -> list[list[dict]]:
        if not actions:
            return []

        sorted_actions = sorted(actions, key=lambda a: a.get("timestamp", 0))
        clusters: list[list[dict]] = [[sorted_actions[0]]]

        for action in sorted_actions[1:]:
            prev_ts = clusters[-1][-1].get("timestamp", 0)
            curr_ts = action.get("timestamp", 0)
            if curr_ts - prev_ts > self._cluster_gap:
                clusters.append([action])
            else:
                clusters[-1].append(action)

        return clusters

    def extract_segments(
        self, video_path: Path, actions: list[dict]
    ) -> list[SegmentData]:
        meta = self.get_metadata(video_path)
        duration = meta["duration_seconds"]
        fps = meta["fps"]

        if not actions:
            keyframes = self.extract_frames(video_path)
            return [
                SegmentData(
                    segment_index=0,
                    start_time=0.0,
                    end_time=duration,
                    keyframes=keyframes,
                    actions=[],
                )
            ]

        clusters = self._cluster_actions(actions)
        segments: list[SegmentData] = []

        for i, cluster in enumerate(clusters):
            timestamps = [a.get("timestamp", 0) for a in cluster]
            start = max(0, min(timestamps) - 0.5)
            end = min(duration, max(timestamps) + 0.5)

            keyframes: list[FrameData] = []
            cap = cv2.VideoCapture(str(video_path))
            try:
                for ts in timestamps:
                    cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
                    ret, frame = cap.read()
                    if ret:
                        frame = cv2.resize(frame, self._target_size)
                        frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                        keyframes.append(
                            FrameData(frame_index=frame_idx, timestamp=ts, image=frame)
                        )
            finally:
                cap.release()

            segments.append(
                SegmentData(
                    segment_index=i,
                    start_time=start,
                    end_time=end,
                    keyframes=keyframes,
                    actions=cluster,
                )
            )

        return segments

    def load_video_metadata_file(self, meta_path: Path) -> dict:
        with open(meta_path) as f:
            return json.load(f)
