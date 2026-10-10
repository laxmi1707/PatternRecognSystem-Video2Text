from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from app.ml.config import ACTIVITY_LABELS
from app.ml.dataset_loader import ActionRecord, TaskMetadata
from app.pipeline.interaction_features import INTERACTION_FEATURE_DIM, InteractionFeatureExtractor
from app.pipeline.ocr_extractor import OCR_FEATURE_DIM, OCRExtractor
from app.pipeline.ui_detector import UI_FEATURE_DIM, UIDetector
from app.pipeline.video_processor import SegmentData, VideoProcessor
from app.pipeline.visual_features import VISUAL_FEATURE_DIM, VisualFeatureExtractor

logger = logging.getLogger(__name__)

_BASE_FEATURES = OCR_FEATURE_DIM + UI_FEATURE_DIM + VISUAL_FEATURE_DIM + INTERACTION_FEATURE_DIM
TOTAL_FEATURES = _BASE_FEATURES + 1  # +1 for has_action_log flag

MODALITY_MAP: dict[str, tuple[int, int]] = {
    "ocr_text": (0, OCR_FEATURE_DIM),
    "ui_elements": (OCR_FEATURE_DIM, OCR_FEATURE_DIM + UI_FEATURE_DIM),
    "visual": (
        OCR_FEATURE_DIM + UI_FEATURE_DIM,
        OCR_FEATURE_DIM + UI_FEATURE_DIM + VISUAL_FEATURE_DIM,
    ),
    "interaction": (
        OCR_FEATURE_DIM + UI_FEATURE_DIM + VISUAL_FEATURE_DIM,
        _BASE_FEATURES,
    ),
    # Index _BASE_FEATURES: 1.0 if action log present, 0.0 if absent.
    # Lets models learn to discount zero interaction features at inference time.
    "has_action_log": (_BASE_FEATURES, TOTAL_FEATURES),
}

_LABEL_TO_IDX = {label: i for i, label in enumerate(ACTIVITY_LABELS)}


class FeatureAssembler:
    def __init__(
        self,
        ocr: OCRExtractor,
        ui: UIDetector,
        visual: VisualFeatureExtractor,
        interaction: InteractionFeatureExtractor,
        video_processor: VideoProcessor,
    ):
        self._ocr = ocr
        self._ui = ui
        self._visual = visual
        self._interaction = interaction
        self._vp = video_processor
        self._ocr_corpus: list[str] = []
        self._ocr_fitted = False

    def extract_segment_features(self, segment: SegmentData) -> np.ndarray:
        features = np.zeros(TOTAL_FEATURES, dtype=np.float32)

        action_records = [
            ActionRecord(
                action_type=a.get("action_type", "UNKNOWN"),
                timestamp=float(a.get("timestamp", 0)),
                params=a.get("action_params", a.get("params", {})),
                t_end=a.get("t_end"),
                groundcua_id=a.get("groundcua_id"),
            )
            if isinstance(a, dict)
            else a
            for a in segment.actions
        ]

        start, end = MODALITY_MAP["ocr_text"]
        self._last_ocr_text: str = ""
        if segment.keyframes:
            ocr_features, ocr_text = self._ocr.extract_segment(segment.keyframes)
            features[start:end] = ocr_features
            self._last_ocr_text = ocr_text

        start, end = MODALITY_MAP["ui_elements"]
        if segment.keyframes:
            ui_features = self._ui.extract_segment(segment.keyframes)
            features[start:end] = ui_features

        start, end = MODALITY_MAP["visual"]
        if segment.keyframes:
            visual_features = self._visual.extract_segment(segment.keyframes)
            features[start:end] = visual_features

        start, end = MODALITY_MAP["interaction"]
        interaction_features = self._interaction.extract(
            action_records, segment.start_time, segment.end_time
        )
        features[start:end] = interaction_features

        # has_action_log flag: 1.0 if action records exist, 0.0 if absent
        features[MODALITY_MAP["has_action_log"][0]] = 1.0 if action_records else 0.0

        return features

    def extract_task_features(
        self, task: TaskMetadata
    ) -> tuple[np.ndarray, int]:
        label_idx = _LABEL_TO_IDX.get(task.activity_label, _LABEL_TO_IDX["other"])

        if task.video_path and task.video_path.exists():
            action_dicts = [
                {
                    "action_type": a.action_type,
                    "timestamp": a.timestamp,
                    "action_params": a.params,
                    "t_end": a.t_end,
                    "groundcua_id": a.groundcua_id,
                }
                for a in task.actions
            ]
            segments = self._vp.extract_segments(task.video_path, action_dicts)
        else:
            action_records = task.actions
            if action_records:
                timestamps = [a.timestamp for a in action_records]
                segments = [
                    SegmentData(
                        segment_index=0,
                        start_time=min(timestamps),
                        end_time=max(t.t_end or t.timestamp for t in action_records),
                        keyframes=[],
                        actions=[
                            {
                                "action_type": a.action_type,
                                "timestamp": a.timestamp,
                                "action_params": a.params,
                                "t_end": a.t_end,
                            }
                            for a in action_records
                        ],
                    )
                ]
            else:
                segments = [
                    SegmentData(segment_index=0, start_time=0, end_time=1, keyframes=[], actions=[])
                ]

        X = np.array([self.extract_segment_features(seg) for seg in segments])
        return X, label_idx

    def _collect_ocr_corpus(self, tasks: list[TaskMetadata]) -> list[str]:
        corpus: list[str] = []
        for task in tasks:
            corpus.append(task.instruction)
            for a in task.actions:
                if a.params:
                    text = a.params.get("text", "") or a.params.get("value", "")
                    if text:
                        corpus.append(text)
        return corpus

    def build_dataset(
        self, tasks: list[TaskMetadata]
    ) -> tuple[np.ndarray, np.ndarray, dict]:
        if not self._ocr_fitted:
            logger.info("Building OCR TF-IDF vocabulary from task corpus...")
            corpus = self._collect_ocr_corpus(tasks)
            if corpus:
                self._ocr.fit_tfidf(corpus)
            self._ocr_fitted = True

        import time as _time

        all_X: list[np.ndarray] = []
        all_y: list[int] = []
        task_ids: list[int] = []
        total = len(tasks)
        t_start = _time.time()

        for idx, task in enumerate(tasks, 1):
            elapsed = _time.time() - t_start
            eta = (elapsed / idx) * (total - idx) if idx > 1 else 0
            pct = idx / total * 100
            logger.info(
                f"[{idx}/{total}] ({pct:.0f}%) Task {task.task_id} ({task.platform}) "
                f"| elapsed={elapsed:.0f}s | ETA={eta:.0f}s"
            )
            X_task, label_idx = self.extract_task_features(task)
            all_X.append(X_task)
            all_y.extend([label_idx] * X_task.shape[0])
            task_ids.extend([task.task_id] * X_task.shape[0])

        X = np.vstack(all_X) if all_X else np.zeros((0, TOTAL_FEATURES))
        y = np.array(all_y, dtype=np.int64)

        metadata = {
            "task_ids": np.array(task_ids),
            "n_tasks": len(tasks),
            "n_segments": len(y),
            "modality_map": MODALITY_MAP,
        }

        return X, y, metadata


def get_default_assembler(use_gpu: bool | None = None) -> FeatureAssembler:
    if use_gpu is None:
        try:
            import torch
            use_gpu = torch.cuda.is_available()
        except ImportError:
            use_gpu = False
    return FeatureAssembler(
        ocr=OCRExtractor(use_gpu=use_gpu),
        ui=UIDetector(use_gpu=use_gpu),
        visual=VisualFeatureExtractor(),
        interaction=InteractionFeatureExtractor(),
        video_processor=VideoProcessor(),
    )
