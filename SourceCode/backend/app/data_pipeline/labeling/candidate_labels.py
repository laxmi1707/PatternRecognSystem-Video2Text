from __future__ import annotations

from app.data_pipeline.labeling.keywords import score_text
from app.data_pipeline.types import CandidateLabel, EvidenceRecord, Frame


def build_candidate_label(frame: Frame, evidence: tuple[EvidenceRecord, ...]) -> CandidateLabel:
    ocr_text = ""
    ui_guess = None
    ui_confidence = 0.0

    for record in evidence:
        if record.source == "ocr":
            ocr_text = record.payload.get("text", "")
        elif record.source == "ui_heuristic":
            ui_guess = record.payload.get("activity_guess")
            ui_confidence = record.confidence

    if ocr_text.strip():
        activity, confidence, _ = score_text(ocr_text)
    elif ui_guess is not None:
        activity, confidence = ui_guess, ui_confidence
    else:
        activity, confidence = "other", 0.2

    return CandidateLabel(frame=frame, activity=activity, confidence=confidence, evidence=evidence)
