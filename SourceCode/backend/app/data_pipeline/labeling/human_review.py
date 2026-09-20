from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.data_pipeline.types import AgreementResult, LabeledExample

REVIEW_QUEUE_PATH = Path("review_queue.jsonl")
REVIEW_DECISIONS_PATH = Path("review_decisions.jsonl")


def submit_for_review(result: AgreementResult) -> LabeledExample:
    """Queue a low-confidence candidate for a human to look at.

    Returns a provisional LabeledExample using the fused candidate's best
    guess (so the dataset never blocks on review), flagged label_source=
    "human_review" -- a reviewer resolves it later via apply_review_decision.
    """
    entry = {
        "video_id": result.candidate.frame.video_id,
        "frame_index": result.candidate.frame.frame_index,
        "image_path": str(result.candidate.frame.image_path),
        "candidate_activity": result.candidate.activity,
        "candidate_confidence": result.candidate.confidence,
        "agreement_score": result.agreement_score,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    with REVIEW_QUEUE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return LabeledExample(
        frame=result.candidate.frame,
        activity=result.candidate.activity,
        label_confidence=result.candidate.confidence,
        label_source="human_review",
    )


def apply_review_decision(
    result: AgreementResult, activity: str, reviewer_id: str
) -> LabeledExample:
    entry = {
        "video_id": result.candidate.frame.video_id,
        "frame_index": result.candidate.frame.frame_index,
        "activity": activity,
        "reviewer_id": reviewer_id,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    with REVIEW_DECISIONS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return LabeledExample(
        frame=result.candidate.frame,
        activity=activity,
        label_confidence=1.0,
        label_source="human_review",
    )
