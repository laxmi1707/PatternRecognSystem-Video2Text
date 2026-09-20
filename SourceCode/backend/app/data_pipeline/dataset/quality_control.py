from __future__ import annotations

from app.data_pipeline.labeling.human_review import submit_for_review
from app.data_pipeline.types import AgreementResult, LabeledExample


def to_quality_controlled_dataset(results: list[AgreementResult]) -> list[LabeledExample]:
    examples: list[LabeledExample] = []

    for result in results:
        if result.needs_human_review:
            examples.append(submit_for_review(result))
        else:
            examples.append(
                LabeledExample(
                    frame=result.candidate.frame,
                    activity=result.candidate.activity,
                    label_confidence=result.candidate.confidence,
                    label_source="auto",
                )
            )

    return examples
