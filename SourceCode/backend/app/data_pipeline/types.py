from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoRecord:
    video_id: str
    source_path: Path
    duration_s: float
    fps: float


@dataclass(frozen=True)
class Frame:
    video_id: str
    frame_index: int
    timestamp_s: float
    image_path: Path


@dataclass(frozen=True)
class AugmentedFrame:
    frame: Frame
    augmentation: str
    image_path: Path


@dataclass(frozen=True)
class EvidenceRecord:
    frame: Frame
    source: str
    payload: dict
    confidence: float


@dataclass(frozen=True)
class CandidateLabel:
    frame: Frame
    activity: str
    confidence: float
    evidence: tuple[EvidenceRecord, ...]


@dataclass(frozen=True)
class AgreementResult:
    candidate: CandidateLabel
    agreement_score: float
    needs_human_review: bool


@dataclass(frozen=True)
class LabeledExample:
    frame: Frame
    activity: str
    label_confidence: float
    label_source: str  # "auto" (cleared the confidence/agreement gate) or "human_review"


@dataclass(frozen=True)
class DatasetSplits:
    train: tuple[LabeledExample, ...]
    validation: tuple[LabeledExample, ...]
    test: tuple[LabeledExample, ...]
