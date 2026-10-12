from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Human-readable descriptions for each activity label
_LABEL_DESCRIPTIONS: dict[str, str] = {
    "coding_editing":   "Edit code or configuration files in the IDE",
    "web_browsing":     "Browse the web or search for information",
    "terminal_ops":     "Execute commands in the terminal or shell",
    "system_config":    "Configure system settings or application preferences",
    "debugging":        "Debug code using breakpoints or the debugger",
    "git_operations":   "Perform version control operations with Git",
    "docker_workflow":  "Build, run, or manage Docker containers",
    "aws_console":      "Manage cloud resources in the AWS console",
    "kubernetes_ops":   "Manage Kubernetes clusters or deployments",
    "terraform_iac":    "Provision infrastructure using Terraform",
    "jenkins_ci_cd":    "Configure or trigger CI/CD pipelines",
    "documentation":    "Write or update documentation",
    "other":            "Perform general screen activity",
}

# Platform-specific action verbs for more natural step descriptions
_PLATFORM_VERBS: dict[str, dict[str, str]] = {
    "eclipse":          {"coding_editing": "Edit code in Eclipse IDE", "debugging": "Use Eclipse debugger"},
    "visual studio code": {"coding_editing": "Edit code in VS Code", "debugging": "Debug in VS Code"},
    "vscode":           {"coding_editing": "Edit code in VS Code", "debugging": "Debug in VS Code"},
    "intellij":         {"coding_editing": "Edit code in IntelliJ IDEA", "debugging": "Debug in IntelliJ IDEA"},
    "pycharm":          {"coding_editing": "Edit Python code in PyCharm", "debugging": "Debug in PyCharm"},
    "terminal":         {"terminal_ops": "Run commands in the terminal"},
    "firefox":          {"web_browsing": "Browse using Firefox"},
    "chrome":           {"web_browsing": "Browse using Chrome"},
}


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


# Keywords that indicate meaningful UI actions — matched against OCR text
_UI_KEYWORDS: list[tuple[list[str], str]] = [
    (["perspective", "java perspective", "debug perspective"], "Switch perspective"),
    (["breakpoint", "debug", "step over", "step into", "resume"], "Debug code"),
    (["install", "extension", "plugin", "marketplace"], "Install extension or plugin"),
    (["terminal", "command", "shell", "bash", "run"], "Execute terminal command"),
    (["git", "commit", "push", "pull", "branch", "merge"], "Perform Git operation"),
    (["docker", "container", "image", "compose"], "Manage Docker container"),
    (["settings", "preferences", "configure", "configuration"], "Configure settings"),
    (["file", "open", "save", "new file", "create"], "Work with file"),
    (["search", "find", "replace", "grep"], "Search or find in files"),
    (["build", "compile", "run", "execute", "maven", "gradle"], "Build or run project"),
    (["test", "junit", "pytest", "assert"], "Run tests"),
    (["import", "export", "module", "package"], "Manage imports or packages"),
    (["class", "method", "function", "interface"], "Edit code structure"),
    (["aws", "s3", "ec2", "lambda", "iam"], "Manage AWS resources"),
    (["kubectl", "pod", "deployment", "namespace"], "Manage Kubernetes resources"),
]


def _extract_keywords(ocr_text: str) -> str:
    """Extract meaningful UI action from OCR keywords."""
    if not ocr_text:
        return ""
    text_lower = ocr_text.lower()
    for keywords, action in _UI_KEYWORDS:
        for kw in keywords:
            if kw in text_lower:
                # Find the actual matching text in OCR for context
                words = re.findall(r"[A-Za-z][a-zA-Z0-9\s]{2,30}", ocr_text)
                context = next((w.strip() for w in words if len(w.strip()) > 4), "")
                if context and context.lower() != kw:
                    return f"{action} ({context})"
                return action
    return ""


def _clean_ocr(text: str) -> str:
    """Extract meaningful words from Tesseract output — filter single chars and symbol noise."""
    if not text:
        return ""
    # Extract real English words (4+ chars) from the OCR dump
    words = re.findall(r"[A-Za-z]{4,}", text)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for w in words:
        wl = w.lower()
        if wl not in seen:
            seen.add(wl)
            unique.append(w)
    if not unique:
        return ""
    return " · ".join(unique[:8])  # max 8 meaningful words


def _step_description(label: str, platform: str, ocr: str) -> str:
    """Build a meaningful step description from label + platform + OCR keywords."""
    plat_lower = platform.lower()

    # Try platform-specific verb first
    for plat_key, verbs in _PLATFORM_VERBS.items():
        if plat_key in plat_lower and label in verbs:
            base = verbs[label]
            break
    else:
        base = _LABEL_DESCRIPTIONS.get(label, f"Perform {label.replace('_', ' ')} activity")

    # Try to extract a meaningful action from OCR keywords
    keyword_action = _extract_keywords(ocr)
    if keyword_action:
        return f"{base}: {keyword_action}."

    # Fall back to cleaned OCR words as context
    cleaned = _clean_ocr(ocr)
    if cleaned:
        return f"{base}. Visible on screen: {cleaned}."
    return f"{base}."


def _merge_consecutive_segments(
    segments: list[dict],
    ocr_texts: list[str],
) -> tuple[list[dict], list[str]]:
    """Merge consecutive segments with the same activity label into one step."""
    if not segments:
        return [], []

    merged_segs: list[dict] = []
    merged_ocr: list[str] = []

    cur = dict(segments[0])
    cur_ocr_parts = [ocr_texts[0]] if ocr_texts else [""]

    for i in range(1, len(segments)):
        seg = segments[i]
        ocr = ocr_texts[i] if i < len(ocr_texts) else ""
        if seg["predicted_label"] == cur["predicted_label"]:
            # Extend current segment
            cur["end_time"] = seg["end_time"]
            cur["confidence"] = max(cur["confidence"], seg.get("confidence", 0))
            if ocr and ocr not in cur_ocr_parts:
                cur_ocr_parts.append(ocr)
        else:
            merged_segs.append(cur)
            merged_ocr.append(" · ".join(p for p in cur_ocr_parts if p)[:200])
            cur = dict(seg)
            cur_ocr_parts = [ocr]

    merged_segs.append(cur)
    merged_ocr.append(" · ".join(p for p in cur_ocr_parts if p)[:200])

    return merged_segs, merged_ocr


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
        return self._generate_rule_based(task_instruction, platform, segments, ocr_texts)

    def _generate_rule_based(
        self,
        task_instruction: str,
        platform: str,
        segments: list[dict],
        ocr_texts: list[str] | None,
    ) -> SOPDocument:
        if not ocr_texts:
            ocr_texts = [""] * len(segments)

        # 1. Clean OCR text for each segment
        cleaned_ocr = [_clean_ocr(t) for t in ocr_texts]

        # 2. Merge consecutive same-label segments
        merged_segs, merged_ocr = _merge_consecutive_segments(segments, cleaned_ocr)

        # 3. Build steps
        steps: list[SOPStep] = []
        for i, (seg, ocr) in enumerate(zip(merged_segs, merged_ocr)):
            label = seg.get("predicted_label", "other")
            label_title = label.replace("_", " ").title()
            start = seg.get("start_time", 0)
            end = seg.get("end_time", 0)
            description = _step_description(label, platform, ocr)

            steps.append(SOPStep(
                number=i + 1,
                title=label_title,
                description=description,
                time_range=f"{start:.1f}s - {end:.1f}s",
                detected_text=ocr,
            ))

        # 4. Build prerequisites from platform + detected activities
        activity_labels = {s.get("predicted_label", "") for s in segments}
        prerequisites = [f"Access to {platform}"]
        if "terminal_ops" in activity_labels:
            prerequisites.append("Terminal or shell access")
        if "git_operations" in activity_labels:
            prerequisites.append("Git installed and repository cloned")
        if "docker_workflow" in activity_labels:
            prerequisites.append("Docker installed and running")
        if "aws_console" in activity_labels:
            prerequisites.append("AWS account with appropriate IAM permissions")
        prerequisites.append("Required permissions and credentials")

        # 5. Dominant activity for outcome sentence
        label_counts: dict[str, int] = {}
        for s in merged_segs:
            lbl = s.get("predicted_label", "other")
            label_counts[lbl] = label_counts.get(lbl, 0) + 1
        dominant = max(label_counts, key=label_counts.__getitem__) if label_counts else "other"
        dominant_desc = _LABEL_DESCRIPTIONS.get(dominant, "complete the task").lower()

        return SOPDocument(
            title=f"SOP: {task_instruction}",
            purpose=f"Step-by-step procedure to {dominant_desc} on {platform}.",
            prerequisites=prerequisites,
            steps=steps,
            expected_outcome=f"Successfully completed: {task_instruction}",
            troubleshooting=[
                "Verify all prerequisites are met",
                "Check application version compatibility",
                "Review error messages in the console or log output",
            ],
        )
