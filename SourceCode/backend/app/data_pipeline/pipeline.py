from __future__ import annotations

from pathlib import Path

from app.data_pipeline.cleaning import clean_frames
from app.data_pipeline.dataset.quality_control import to_quality_controlled_dataset
from app.data_pipeline.dataset.splits import split_dataset
from app.data_pipeline.evidence.ocr import extract_ocr_evidence
from app.data_pipeline.evidence.ui_object_detection import detect_ui_objects
from app.data_pipeline.frame_extraction import extract_frames
from app.data_pipeline.ingestion import discover_videos
from app.data_pipeline.labeling.confidence_agreement import check_agreement
from app.data_pipeline.labeling.evidence_fusion import (
    OcrKeywordClassifier,
    UiHeuristicClassifier,
    fuse_evidence,
)
from app.data_pipeline.types import AgreementResult, DatasetSplits

CLASSIFIERS = (OcrKeywordClassifier(), UiHeuristicClassifier())


def run_data_pipeline(raw_video_dir: Path, frame_output_dir: Path) -> DatasetSplits:
    videos = discover_videos(raw_video_dir)

    agreement_results: list[AgreementResult] = []
    for video in videos:
        frames = extract_frames(video, frame_output_dir)
        usable = clean_frames(frames)

        for frame in usable:
            evidence = (extract_ocr_evidence(frame), detect_ui_objects(frame))
            candidate = fuse_evidence(frame, evidence, CLASSIFIERS)
            agreement_results.append(check_agreement(candidate))

    labeled = to_quality_controlled_dataset(agreement_results)
    return split_dataset(labeled)
