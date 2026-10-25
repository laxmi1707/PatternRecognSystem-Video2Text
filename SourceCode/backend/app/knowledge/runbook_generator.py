from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RunbookDocument:
    title: str
    description: str
    when_to_use: str
    prerequisites: list[str]
    steps: list[RunbookStep]
    verification: list[str]
    rollback: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class RunbookStep:
    number: int
    action: str
    details: str
    command: str = ""
    expected_output: str = ""


class RunbookGenerator:
    def __init__(self):
        pass

    def generate_from_workflow(
        self,
        workflow_description: str,
        platform: str,
        duration_seconds: float,
        activity_sequence: list[dict],
        detected_commands: list[str] | None = None,
        ocr_texts: list[str] | None = None,
    ) -> RunbookDocument:
        return self._generate_rule_based(
            workflow_description, platform, duration_seconds,
            activity_sequence, detected_commands, ocr_texts,
        )

    def _generate_rule_based(
        self,
        workflow_description: str,
        platform: str,
        duration_seconds: float,
        activity_sequence: list[dict],
        detected_commands: list[str] | None,
        ocr_texts: list[str] | None = None,
    ) -> RunbookDocument:
        from app.knowledge.sop_generator import _extract_keywords

        steps: list[RunbookStep] = []
        for i, activity in enumerate(activity_sequence):
            raw_label = activity.get("predicted_label", activity.get("label", "other"))
            raw_ocr = (ocr_texts[i] if ocr_texts and i < len(ocr_texts) else "")
            keyword_action = _extract_keywords(raw_ocr)
            action = keyword_action if keyword_action else raw_label.replace("_", " ").title()

            if keyword_action and platform.lower() not in keyword_action.lower():
                details = f"{keyword_action} on {platform}."
            elif keyword_action:
                details = f"{keyword_action}."
            else:
                details = f"{action.lower()} on {platform}."

            command = ""
            if detected_commands and i < len(detected_commands):
                command = detected_commands[i]

            steps.append(
                RunbookStep(
                    number=i + 1,
                    action=action,
                    details=details,
                    command=command,
                    expected_output=f"Activity completed with confidence "
                    f"{activity.get('confidence', 0):.0%}",
                )
            )

        return RunbookDocument(
            title=f"Runbook: {workflow_description}",
            description=f"Operational procedure for {workflow_description} on {platform}.",
            when_to_use=f"When you need to {workflow_description.lower()}.",
            prerequisites=[
                f"Access to {platform}",
                "Appropriate user permissions",
            ],
            steps=steps,
            verification=[
                "Verify each step completed successfully",
                "Check application state matches expected outcome",
                "Review logs for any warnings or errors",
            ],
            rollback=[
                "Undo changes in reverse order",
                "Restore from backup if available",
                "Document any issues encountered",
            ],
        )

