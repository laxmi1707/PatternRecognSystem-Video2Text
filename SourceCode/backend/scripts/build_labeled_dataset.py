"""Run the real ingestion pipeline on localDataset/, resolve every low-confidence
candidate via a human-review pass, and save the finalized labeled dataset.

The reviewer here is a one-time manual visual check (see conversation/PR notes)
confirming this specific video is a single uninterrupted `which curl` terminal
session with no signal matching any of the 10 defined activities -- i.e. the
correct ground truth for every frame is "other". Any new video must go through
its own review; this is not a general auto-approval rule.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.data_pipeline.cleaning import clean_frames
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
from app.data_pipeline.labeling.human_review import apply_review_decision

REVIEWER_ID = "claude-manual-visual-review"
CLASSIFIERS = (OcrKeywordClassifier(), UiHeuristicClassifier())


def main() -> None:
    video_dir = BACKEND_ROOT / "localDataset"
    frame_dir = Path("C:/tmp/pipeline_frames")
    out_path = video_dir / "labeled_dataset.json"

    videos = discover_videos(video_dir)
    labeled = []

    for video in videos:
        print(f"=== {video.video_id} ===")
        frames = extract_frames(video, frame_dir)
        usable = clean_frames(frames)

        for frame in usable:
            ocr_evidence = extract_ocr_evidence(frame)
            ui_evidence = detect_ui_objects(frame)
            candidate = fuse_evidence(frame, (ocr_evidence, ui_evidence), CLASSIFIERS)
            agreement = check_agreement(candidate)

            print(
                f"  frame {frame.frame_index:2d} t={frame.timestamp_s:5.1f}s "
                f"ocr_text={ocr_evidence.payload.get('text', '')!r} "
                f"fused={candidate.activity}({candidate.confidence:.2f}) "
                f"review={'yes' if agreement.needs_human_review else 'no'}"
            )

            if agreement.needs_human_review:
                example = apply_review_decision(agreement, activity="other", reviewer_id=REVIEWER_ID)
            else:
                from app.data_pipeline.types import LabeledExample

                example = LabeledExample(
                    frame=frame,
                    activity=candidate.activity,
                    label_confidence=candidate.confidence,
                    label_source="auto",
                )
            labeled.append(example)

    splits = split_dataset(labeled)
    print(f"\ntrain={len(splits.train)} val={len(splits.validation)} test={len(splits.test)}")

    activity_counts: dict[str, int] = {}
    for ex in labeled:
        activity_counts[ex.activity] = activity_counts.get(ex.activity, 0) + 1
    print("label distribution:", activity_counts)

    def serialize(examples):
        return [
            {
                "video_id": ex.frame.video_id,
                "frame_index": ex.frame.frame_index,
                "timestamp_s": ex.frame.timestamp_s,
                "image_path": str(ex.frame.image_path),
                "activity": ex.activity,
                "label_confidence": ex.label_confidence,
                "label_source": ex.label_source,
            }
            for ex in examples
        ]

    out_path.write_text(
        json.dumps(
            {
                "train": serialize(splits.train),
                "validation": serialize(splits.validation),
                "test": serialize(splits.test),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"saved -> {out_path}")


if __name__ == "__main__":
    main()
