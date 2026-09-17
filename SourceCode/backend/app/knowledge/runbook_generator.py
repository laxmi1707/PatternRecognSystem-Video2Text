from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.knowledge.templates import RUNBOOK_SYSTEM_PROMPT, RUNBOOK_USER_TEMPLATE

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
    def __init__(self, llm_client=None):
        self._llm = llm_client

    def generate_from_workflow(
        self,
        workflow_description: str,
        platform: str,
        duration_seconds: float,
        activity_sequence: list[dict],
        detected_commands: list[str] | None = None,
    ) -> RunbookDocument:
        if self._llm:
            return self._generate_with_llm(
                workflow_description, platform, duration_seconds,
                activity_sequence, detected_commands,
            )
        return self._generate_rule_based(
            workflow_description, platform, duration_seconds,
            activity_sequence, detected_commands,
        )

    def _generate_with_llm(
        self,
        workflow_description: str,
        platform: str,
        duration_seconds: float,
        activity_sequence: list[dict],
        detected_commands: list[str] | None,
    ) -> RunbookDocument:
        activities_text = "\n".join(
            f"{i+1}. {a.get('label', 'unknown')} "
            f"[{a.get('start_time', 0):.1f}s-{a.get('end_time', 0):.1f}s] "
            f"(confidence: {a.get('confidence', 0):.2f})"
            for i, a in enumerate(activity_sequence)
        )
        commands_text = "\n".join(detected_commands) if detected_commands else "None detected"

        duration_str = f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s"

        prompt = RUNBOOK_USER_TEMPLATE.format(
            workflow_description=workflow_description,
            platform=platform,
            duration=duration_str,
            activity_sequence=activities_text,
            detected_text=commands_text,
        )

        try:
            response = self._llm.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=RUNBOOK_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            return self._parse_llm_response(raw, workflow_description, platform, activity_sequence)
        except Exception as e:
            logger.warning(f"LLM generation failed, falling back to rule-based: {e}")
            return self._generate_rule_based(
                workflow_description, platform, duration_seconds,
                activity_sequence, detected_commands,
            )

    def _generate_rule_based(
        self,
        workflow_description: str,
        platform: str,
        duration_seconds: float,
        activity_sequence: list[dict],
        detected_commands: list[str] | None,
    ) -> RunbookDocument:
        steps: list[RunbookStep] = []
        for i, activity in enumerate(activity_sequence):
            label = activity.get("label", "unknown").replace("_", " ").title()
            command = ""
            if detected_commands and i < len(detected_commands):
                command = detected_commands[i]

            steps.append(
                RunbookStep(
                    number=i + 1,
                    action=label,
                    details=f"Perform {label.lower()} on {platform}.",
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

    def _parse_llm_response(
        self, raw: str, workflow_description: str, platform: str, activity_sequence: list[dict]
    ) -> RunbookDocument:
        return RunbookDocument(
            title=f"Runbook: {workflow_description}",
            description=f"Generated runbook for {workflow_description} on {platform}.",
            when_to_use=f"When performing {workflow_description.lower()}.",
            prerequisites=[f"Access to {platform}"],
            steps=[
                RunbookStep(
                    number=i + 1,
                    action=a.get("label", "unknown").replace("_", " ").title(),
                    details="",
                )
                for i, a in enumerate(activity_sequence)
            ],
            verification=["Verify completion"],
            raw_text=raw,
        )
