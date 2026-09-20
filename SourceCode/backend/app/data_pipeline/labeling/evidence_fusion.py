from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

from app.data_pipeline.labeling.candidate_labels import build_candidate_label
from app.data_pipeline.types import CandidateLabel, EvidenceRecord, Frame


class EvidenceClassifier(Protocol):
    name: str

    def predict(self, frame: Frame, evidence: tuple[EvidenceRecord, ...]) -> CandidateLabel: ...


@dataclass
class OcrKeywordClassifier:
    name: str = "ocr_keywords"

    def predict(self, frame: Frame, evidence: tuple[EvidenceRecord, ...]) -> CandidateLabel:
        ocr_only = tuple(e for e in evidence if e.source == "ocr")
        return build_candidate_label(frame, ocr_only)


@dataclass
class UiHeuristicClassifier:
    name: str = "ui_heuristic"

    def predict(self, frame: Frame, evidence: tuple[EvidenceRecord, ...]) -> CandidateLabel:
        ui_only = tuple(e for e in evidence if e.source == "ui_heuristic")
        return build_candidate_label(frame, ui_only)


# OCR text is a much stronger activity signal than the UI heuristic (see
# app/data_pipeline/evidence/ui_object_detection.py), so it dominates the vote.
CLASSIFIER_WEIGHTS = {"ocr_keywords": 0.75, "ui_heuristic": 0.25}


# Voting/stacking fusion across evidence sources (OCR, UI detection, ...) that
# produces one CandidateLabel per frame — separate from the boosting ensemble
# in app.training.boosting, which combines base classifiers, not evidence sources.
def fuse_evidence(
    frame: Frame,
    evidence: tuple[EvidenceRecord, ...],
    classifiers: tuple[EvidenceClassifier, ...],
) -> CandidateLabel:
    if not classifiers:
        raise ValueError("fuse_evidence requires at least one classifier")

    scores: dict[str, float] = defaultdict(float)
    total_weight = 0.0

    for classifier in classifiers:
        candidate = classifier.predict(frame, evidence)
        weight = CLASSIFIER_WEIGHTS.get(classifier.name, 1.0)
        scores[candidate.activity] += weight * candidate.confidence
        total_weight += weight

    best_activity = max(scores, key=scores.get)
    fused_confidence = scores[best_activity] / total_weight if total_weight else 0.0

    return CandidateLabel(frame=frame, activity=best_activity, confidence=fused_confidence, evidence=evidence)
