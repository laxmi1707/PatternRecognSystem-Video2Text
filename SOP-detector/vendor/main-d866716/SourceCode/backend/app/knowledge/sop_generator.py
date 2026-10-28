from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.knowledge.templates import SOP_SYSTEM_PROMPT, SOP_USER_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class SOPDocument:
    title: str
    purpose: str
    prerequisites: list[str]
    steps: list[SOPStep]
    expected_outcome: str
    troubleshooting: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class SOPStep:
    number: int
    title: str
    description: str
    time_range: str = ""
    detected_text: str = ""


class SOPGenerator:
    def __init__(self, llm_client=None):
        self._llm = llm_client

    def generate_from_segments(
        self,
        task_instruction: str,
        platform: str,
        segments: list[dict],
        ocr_texts: list[str] | None = None,
    ) -> SOPDocument:
        if self._llm:
            return self._generate_with_llm(task_instruction, platform, segments, ocr_texts)
        return self._generate_rule_based(task_instruction, platform, segments, ocr_texts)

    def _generate_with_llm(
        self,
        task_instruction: str,
        platform: str,
        segments: list[dict],
        ocr_texts: list[str] | None,
    ) -> SOPDocument:
        segments_text = "\n".join(
            f"{i+1}. [{s.get('start_time', 0):.1f}s - {s.get('end_time', 0):.1f}s] "
            f"{s.get('predicted_label', 'unknown')} (confidence: {s.get('confidence', 0):.2f})"
            for i, s in enumerate(segments)
        )
        ocr_text = "\n".join(ocr_texts) if ocr_texts else "No OCR text available"

        prompt = SOP_USER_TEMPLATE.format(
            task_instruction=task_instruction,
            platform=platform,
            segments=segments_text,
            ocr_text=ocr_text,
        )

        try:
            response = self._llm.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=SOP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            return self._parse_llm_response(raw, task_instruction, platform, segments)
        except Exception as e:
            logger.warning(f"LLM generation failed, falling back to rule-based: {e}")
            return self._generate_rule_based(task_instruction, platform, segments, ocr_texts)

    def _generate_rule_based(
        self,
        task_instruction: str,
        platform: str,
        segments: list[dict],
        ocr_texts: list[str] | None,
    ) -> SOPDocument:
        steps: list[SOPStep] = []
        for i, seg in enumerate(segments):
            label = seg.get("predicted_label", "unknown").replace("_", " ").title()
            start = seg.get("start_time", 0)
            end = seg.get("end_time", 0)
            ocr = ocr_texts[i] if ocr_texts and i < len(ocr_texts) else ""

            description = f"Perform {label.lower()} activity on {platform}."
            if ocr:
                description += f' Detected text: "{ocr[:100]}"'

            steps.append(
                SOPStep(
                    number=i + 1,
                    title=label,
                    description=description,
                    time_range=f"{start:.1f}s - {end:.1f}s",
                    detected_text=ocr,
                )
            )

        return SOPDocument(
            title=f"SOP: {task_instruction}",
            purpose=f"Step-by-step procedure for: {task_instruction} on {platform}.",
            prerequisites=[f"Access to {platform}", "Required permissions and credentials"],
            steps=steps,
            expected_outcome=f"Successfully completed: {task_instruction}",
            troubleshooting=[
                "Verify all prerequisites are met",
                "Check application version compatibility",
                "Review error messages in the console/log",
            ],
        )

    def _parse_llm_response(
        self, raw: str, task_instruction: str, platform: str, segments: list[dict]
    ) -> SOPDocument:
        return SOPDocument(
            title=f"SOP: {task_instruction}",
            purpose=f"Generated procedure for {task_instruction} on {platform}.",
            prerequisites=[f"Access to {platform}"],
            steps=[
                SOPStep(
                    number=i + 1,
                    title=seg.get("predicted_label", "unknown").replace("_", " ").title(),
                    description="",
                    time_range=f"{seg.get('start_time', 0):.1f}s - {seg.get('end_time', 0):.1f}s",
                )
                for i, seg in enumerate(segments)
            ],
            expected_outcome=f"Completed: {task_instruction}",
            raw_text=raw,
        )
