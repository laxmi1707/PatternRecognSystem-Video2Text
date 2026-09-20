from __future__ import annotations

from app.data_pipeline.types import AgreementResult, CandidateLabel

HUMAN_REVIEW_THRESHOLD = 0.7


def check_agreement(candidate: CandidateLabel) -> AgreementResult:
    # fuse_evidence's weighted vote already folds cross-source agreement into
    # `candidate.confidence`: when evidence sources disagree, the winning
    # activity only collects a fraction of the total classifier weight, so a
    # low fused confidence here *is* low agreement, not a separate signal.
    agreement_score = candidate.confidence
    needs_human_review = agreement_score < HUMAN_REVIEW_THRESHOLD

    return AgreementResult(
        candidate=candidate,
        agreement_score=agreement_score,
        needs_human_review=needs_human_review,
    )
