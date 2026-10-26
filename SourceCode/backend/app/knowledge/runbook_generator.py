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
        from app.knowledge.sop_generator import (
            _extract_keywords, _extract_terminal_command, _merge_consecutive_segments,
        )

        if not ocr_texts:
            ocr_texts = [""] * len(activity_sequence)

        merged_segs, merged_ocr = _merge_consecutive_segments(activity_sequence, ocr_texts)

        _TERMINAL_LABELS = {"terminal_ops", "debugging", "git_operations", "docker_workflow", "kubernetes_ops"}

        steps: list[RunbookStep] = []
        for i, (activity, raw_ocr) in enumerate(zip(merged_segs, merged_ocr)):
            raw_label = activity.get("predicted_label", activity.get("label", "other"))
            start = activity.get("start_time", 0)
            end = activity.get("end_time", 0)

            terminal_cmd = _extract_terminal_command(raw_ocr) if raw_label in _TERMINAL_LABELS else ""
            if terminal_cmd:
                action = f"Run: `{terminal_cmd}`"
                details = f"Execute: `{terminal_cmd}` on {platform}."
                command = terminal_cmd
            else:
                keyword_action = _extract_keywords(raw_ocr)
                action = keyword_action if keyword_action else raw_label.replace("_", " ").title()
                details = f"{action} on {platform}." if platform.lower() not in action.lower() else f"{action}."
                command = ""

            steps.append(
                RunbookStep(
                    number=i + 1,
                    action=action,
                    details=details,
                    command=command,
                    expected_output=f"{raw_label.replace('_', ' ').title()} completed at {start:.0f}s–{end:.0f}s",
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

