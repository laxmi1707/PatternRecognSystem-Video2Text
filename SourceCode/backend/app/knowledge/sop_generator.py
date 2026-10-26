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
    "diagram_design":   "Create or edit diagrams, flowcharts, or visual designs",
    "media_editing":    "Edit video, audio, or multimedia content",
    "file_management":  "Manage files and directories in the file system",
    "image_editing":    "Edit or process images using a graphics tool",
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
    # Header fields for action-based SOPs ("Application / platform", "Source recording", ...)
    platform: str = ""
    source_recording: str = ""
    generated_at: str = ""


@dataclass
class SOPStep:
    number: int
    title: str
    description: str
    time_range: str = ""
    detected_text: str = ""
    # Action-based SOPs: what the screen showed after the action
    delay_s: float | None = None
    screen_output: list[str] = field(default_factory=list)  # text that appeared
    screen_removed: list[str] = field(default_factory=list)  # text that disappeared
    risk_level: str = "none"   # "high" | "medium" | "none"
    risk_reason: str = ""


# Keywords that indicate meaningful UI actions — matched against OCR text.
# Each tuple: (keyword_variants, action_description)
# Variants include common Tesseract misreads of UI elements.
_UI_KEYWORDS: list[tuple[list[str], str]] = [
    # Eclipse perspective switching — OCR rarely captures menu text directly,
    # but segment 2 shows "Source" in menu bar = Debug perspective is active
    (["perspective", "penpecon", "perpectne", "perspect",
      "patpece", "paupece", "panpece", "penpece",
      "open perspective", "close perspective", "save perspective",
      "java perspective", "debug perspective"], "Switch IDE perspective"),
    # Debug/Java perspective — check BEFORE generic eclipse detection
    # "Source" in the menu bar (source lator/keaton = EasyOCR misread of Source menu items)
    # means the Debug or Java perspective is active in Eclipse
    (["breakpoint", "step over", "step into", "resume",
      "debug view", "debug perspective", "dcbuq", "dcbug",
      "statements", "behaviour", "breviicn",
      "source refactor", "source keaton", "source lator", "source nenpte"], "Debug or navigate code"),
    # Eclipse workspace/IDE detection (generic — matched after more specific checks above)
    # EasyOCR actual misreads observed: ccipre, idipre, worecpece, worerpace, woricpoce
    (["eclipse", "echpse", "echpze", "ccliosc", "ccmosc", "ccipre", "idipre",
      "worecpece", "worerpace", "woricpoce", "worespece",
      "eclipse ide", "eclipse-workspace", "window help"], "Navigate Eclipse IDE"),
    # Terminal / shell
    (["terminal", "bash", "shell", "command prompt", "powershell"], "Execute terminal command"),
    # Git
    (["commit", "push origin", "pull request", "git branch", "merge branch"], "Perform Git operation"),
    # Docker
    (["docker", "container", "compose", "dockerfile"], "Manage Docker container"),
    # Settings / preferences
    (["preferences", "settings", "configure", "configuration", "appeaance", "appearance"], "Configure settings"),
    # File operations
    (["save as", "new file", "open file", "close all"], "Work with files"),
    # Search
    (["find in files", "search project", "replace all"], "Search or replace in files"),
    # Build / run
    (["build project", "run as", "maven", "gradle", "compile"], "Build or run project"),
    # Tests
    (["junit", "pytest", "test suite", "test runner"], "Run tests"),
    # AWS
    (["aws console", "s3 bucket", "ec2 instance", "lambda", "iam"], "Manage AWS resources"),
    # Kubernetes
    (["kubectl", "kubernetes", "namespace", "deployment"], "Manage Kubernetes resources"),
    # VS Code specific
    (["vscode", "visual studio code", "code insiders", "extensions marketplace"], "Navigate VS Code"),
]


def _extract_keywords(ocr_text: str) -> str:
    """Extract meaningful UI action from OCR keywords, tolerating Tesseract misreads."""
    if not ocr_text:
        return ""
    text_lower = ocr_text.lower()
    for keywords, action in _UI_KEYWORDS:
        for kw in keywords:
            if kw in text_lower:
                return action
    return ""


# Known meaningful words that may appear in screen recordings
_KNOWN_SCREEN_WORDS: set[str] = {
    # IDE names — exact and EasyOCR variants observed in CUA dataset
    "eclipse", "echpse", "echpze", "ccliosc", "ccmosc", "ccipre", "idipre",
    "worecpece", "worerpace", "woricpoce", "worespece",
    "vscode", "intellij", "pycharm",
    # UI menus and actions — exact and OCR variants
    "perspective", "penpecon", "perpectne", "patpece", "paupece", "panpece",
    "debug", "dcbuq", "dcbug", "java", "python", "window",
    "navigate", "navigetc", "navicttc", "nenpte", "mongate",
    "search", "sewch", "seach", "project", "projcct", "pryect", "progct",
    "refactor", "source", "workspace", "terminal", "bash",
    "docker", "container", "commit", "branch", "merge", "push", "pull",
    "settings", "preferences", "appearance", "configure",
    "build", "compile", "maven", "gradle", "junit",
    "file", "save", "open", "close", "edit",
    "statement", "behaviour", "projects",
}


_TERMINAL_COMMANDS: set[str] = {
    "sed", "awk", "grep", "cat", "ls", "cd", "pwd", "echo", "mv", "cp", "rm",
    "mkdir", "touch", "chmod", "chown", "find", "sort", "uniq", "wc", "head",
    "tail", "cut", "tr", "xargs", "pipe", "python", "python3", "pip", "npm",
    "node", "java", "javac", "gcc", "make", "cmake", "git", "docker", "kubectl",
    "curl", "wget", "ssh", "scp", "tar", "zip", "unzip", "apt", "yum", "brew",
    "export", "source", "chmod", "sudo", "bash", "sh", "zsh", "vim", "nano",
    "ps", "kill", "top", "df", "du", "mount", "ping", "ifconfig", "netstat",
    "aws", "terraform", "helm", "ansible", "systemctl", "service", "journalctl",
}


# Risk rules: (activity_labels, ocr_keywords, risk_level, reason)
# Applied in order — first match wins.
_RISK_RULES: list[tuple[set[str], list[str], str, str]] = [
    # Destructive cloud operations
    ({"aws_console"}, ["delete", "terminate", "destroy", "purge", "deregister", "detach"],
     "high", "Destructive AWS operation detected"),
    # Destructive filesystem / DB commands visible in OCR
    (set(), ["rm -rf", "rm -r /", "drop table", "drop database", "truncate table",
             "chmod 777", "sudo rm"],
     "high", "Destructive command visible on screen"),
    # Force operations and credential exposure
    (set(), ["--force", "--hard", "force-push", "force push",
             "password", "secret", "private_key", "credentials", "access_key"],
     "high", "Sensitive operation or credential visible on screen"),
    # Infrastructure destroy
    ({"terraform_iac", "kubernetes_ops"}, ["destroy", "drain", "force-delete", "delete ns"],
     "high", "Irreversible infrastructure change detected"),
    # Container/cluster removal
    ({"docker_workflow", "kubernetes_ops"}, ["prune", "force", "kill", "remove", "delete"],
     "medium", "Potentially destructive container or cluster operation"),
    # Errors and crashes in debugging sessions
    ({"debugging"}, ["exception", "crash", "fatal", "killed", "error", "traceback", "segfault"],
     "medium", "Error or crash detected during debugging"),
]


def _assess_risk(label: str, ocr_text: str) -> tuple[str, str]:
    """Return (risk_level, risk_reason) for a segment given its activity label and OCR text."""
    if not ocr_text:
        return "none", ""
    text_lower = ocr_text.lower()
    for labels, keywords, level, reason in _RISK_RULES:
        label_match = (not labels) or (label in labels)
        if label_match and any(kw in text_lower for kw in keywords):
            return level, reason
    return "none", ""


_UI_NOISE_PATTERN = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Activities|Terminal|"
    r"Applications|Places|System|Files|Settings|Monday|Tuesday|Wednesday|Thursday|"
    r"Friday|Saturday|Sunday)\b"
)


def _extract_terminal_command(text: str) -> str:
    """Extract shell commands from OCR text of terminal segments."""
    if not text:
        return ""
    candidates = re.split(r"[$#]\s+", text)

    best_cmd = ""
    best_is_known = False
    for candidate in candidates[1:]:
        candidate = re.split(r"\n|\s{3,}", candidate)[0].strip()
        user_at = re.search(r"[\s;]\S+\s*@\s*\S+", candidate)
        if user_at:
            candidate = candidate[:user_at.start()].strip()
        if not candidate or len(candidate) < 3:
            continue
        if _UI_NOISE_PATTERN.search(candidate):
            continue
        # Reject garbled OCR: require printable ASCII only
        if not re.match(r'^[\x20-\x7E]+$', candidate):
            continue
        tokens = candidate.split()
        if len(tokens) > 10:
            continue
        first = tokens[0].lower().lstrip("'\"") if tokens else ""
        is_known = first in _TERMINAL_COMMANDS and len(candidate) > len(first)
        # Only accept text whose first word is a known command — rejects OCR garbage
        if is_known and (not best_is_known or len(candidate) > len(best_cmd)):
            best_cmd = candidate[:80]
            best_is_known = True

    return best_cmd


def _clean_ocr(text: str) -> str:
    """Extract recognisable screen words from Tesseract output."""
    if not text:
        return ""
    words = re.findall(r"[A-Za-z]{4,}", text)
    seen: set[str] = set()
    unique = []
    for w in words:
        wl = w.lower()
        if wl not in seen and wl in _KNOWN_SCREEN_WORDS:
            seen.add(wl)
            unique.append(w)
    if not unique:
        return ""
    return " · ".join(unique[:6])


def _step_description(label: str, platform: str, ocr: str, keyword_action: str = "") -> str:
    """Build a meaningful step description grounded in OCR-detected action."""
    if keyword_action:
        # Description is driven entirely by what OCR detected on screen
        plat_lower = platform.lower()
        for plat_key, verbs in _PLATFORM_VERBS.items():
            if plat_key in plat_lower and label in verbs:
                return f"{verbs[label]}."
        # Avoid "Navigate Eclipse IDE on Eclipse IDE" when action already names the platform
        if platform.lower() in keyword_action.lower():
            return f"{keyword_action}."
        return f"{keyword_action} on {platform}."
    # Fall back to model label description only when OCR gives no signal
    base = _LABEL_DESCRIPTIONS.get(label, f"Perform {label.replace('_', ' ')} activity")
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
            merged_ocr.append(" · ".join(p for p in cur_ocr_parts if p))
            cur = dict(seg)
            cur_ocr_parts = [ocr]

    merged_segs.append(cur)
    merged_ocr.append(" · ".join(p for p in cur_ocr_parts if p))

    return merged_segs, merged_ocr


class SOPGenerator:
    def __init__(self):
        pass

    def generate_from_segments(
        self,
        task_instruction: str,
        platform: str,
        segments: list[dict],
        ocr_texts: list[str] | None = None,
    ) -> SOPDocument:
        return self._generate_rule_based(task_instruction, platform, segments, ocr_texts)

    def generate_from_actions(
        self,
        task_instruction: str,
        platform: str,
        actions: list,
        source_recording: str = "",
        generated_at: str = "",
    ) -> SOPDocument:
        """One step per user action, each with what the screen showed afterwards.

        ``actions`` are ``screen_effects.UserAction``s with their effects captured.
        """
        from app.knowledge.screen_effects import action_sentence, effect_sentence

        steps = [
            SOPStep(
                number=i + 1,
                title=action_sentence(a),
                description=effect_sentence(a.effect),
                time_range=f"{a.timestamp:.1f}s",
                detected_text="\n".join(a.effect.appeared),
                delay_s=a.effect.delay_s,
                screen_output=list(a.effect.appeared),
                screen_removed=list(a.effect.disappeared),
            )
            for i, a in enumerate(actions)
        ]
        last_output = next((s.screen_output for s in reversed(steps) if s.screen_output), [])
        expected = (
            "The screen shows: " + " / ".join(last_output[:3])
            if last_output else f"Successfully completed: {task_instruction}"
        )
        return SOPDocument(
            title=f"SOP: {task_instruction}",
            purpose=task_instruction,
            prerequisites=[f"Access to {platform}"],
            steps=steps,
            expected_outcome=expected,
            troubleshooting=[
                "If a step shows no visible change, check the application is focused and repeat it",
                "Compare the screen with the text shown under each step before continuing",
            ],
            platform=platform,
            source_recording=source_recording,
            generated_at=generated_at,
        )

    def _generate_rule_based(
        self,
        task_instruction: str,
        platform: str,
        segments: list[dict],
        ocr_texts: list[str] | None,
    ) -> SOPDocument:
        if not ocr_texts:
            ocr_texts = [""] * len(segments)

        # 1. Collect raw OCR for whole-document keyword/platform detection
        all_raw_ocr = " ".join(ocr_texts).lower()

        # 2. Merge consecutive same-label segments — prevents 3 identical "Coding Editing" steps
        merged_segs, merged_raw_ocr = _merge_consecutive_segments(segments, ocr_texts)

        # 4. Detect platform from OCR (overrides "Screen Recording" fallback)
        detected_platform = platform
        if platform == "Screen Recording":
            if any(kw in all_raw_ocr for kw in [
                "eclipse", "echpse", "echpze", "ccliosc", "ccipre", "idipre",
                "worecpece", "worerpace", "woricpoce", "worespece", "window help",
            ]):
                detected_platform = "Eclipse IDE"
            elif any(kw in all_raw_ocr for kw in ["vscode", "visual studio code"]):
                detected_platform = "VS Code"
            elif any(kw in all_raw_ocr for kw in ["intellij", "pycharm"]):
                detected_platform = "IntelliJ / PyCharm"

        # 5. Build steps
        steps: list[SOPStep] = []
        for i, (seg, raw_ocr) in enumerate(zip(merged_segs, merged_raw_ocr)):
            label = seg.get("predicted_label", "other")
            start = seg.get("start_time", 0)
            end = seg.get("end_time", 0)

            # For terminal segments, try to extract actual command from OCR first
            terminal_cmd = _extract_terminal_command(raw_ocr) if label in ("terminal_ops", "debugging", "git_operations", "docker_workflow") else ""
            if terminal_cmd:
                keyword_action = ""
                step_title = f"Run: `{terminal_cmd}`"
                description = f"Execute: `{terminal_cmd}`"
            else:
                # Run keyword matching on RAW ocr (multi-word phrases intact, not split by · )
                keyword_action = _extract_keywords(raw_ocr)
                # Don't let a generic platform keyword ("Navigate VS Code") override a specific
                # activity label (git_operations, debugging, etc.) — use the label instead
                _generic_platform_actions = {"Navigate VS Code", "Navigate Eclipse IDE", "Navigate IntelliJ / PyCharm"}
                _specific_labels = {"git_operations", "debugging", "docker_workflow", "aws_console", "kubernetes_ops", "terminal_ops"}
                if keyword_action in _generic_platform_actions and label in _specific_labels:
                    keyword_action = ""
                step_title = keyword_action if keyword_action else label.replace("_", " ").title()
                description = _step_description(label, detected_platform, raw_ocr, keyword_action)

            risk_level, risk_reason = _assess_risk(label, raw_ocr)
            steps.append(SOPStep(
                number=i + 1,
                title=step_title,
                description=description,
                time_range=f"{start:.1f}s - {end:.1f}s",
                detected_text=raw_ocr,
                risk_level=risk_level,
                risk_reason=risk_reason,
            ))

        # 4. Prerequisites driven by OCR content (more reliable than model labels on F1=0.29)
        prerequisites = [f"Access to {detected_platform}"]
        # Only add tool-specific prerequisites when OCR actually shows those tools
        if any(kw in all_raw_ocr for kw in ["terminal", "bash", "shell", "wcrkepacc"]):
            prerequisites.append("Terminal or shell access")
        if any(kw in all_raw_ocr for kw in ["commit", "push", "branch", "merge", "git"]):
            prerequisites.append("Git installed and repository cloned")
        if any(kw in all_raw_ocr for kw in ["docker", "container", "compose"]):
            prerequisites.append("Docker installed and running")
        if any(kw in all_raw_ocr for kw in ["aws", "s3", "ec2", "lambda", "iam"]):
            prerequisites.append("AWS account with appropriate IAM permissions")
        prerequisites.append("Required permissions and credentials")

        # 6. Purpose — use detected_platform and most frequent OCR keyword action
        keyword_actions = [_extract_keywords(o) for o in merged_raw_ocr if o]
        dominant_action = max(set(keyword_actions), key=keyword_actions.count) if keyword_actions else ""
        if dominant_action:
            if detected_platform.lower() in dominant_action.lower():
                purpose = f"Step-by-step procedure to perform: {dominant_action}."
            else:
                purpose = f"Step-by-step procedure to perform: {dominant_action} on {detected_platform}."
        else:
            label_counts: dict[str, int] = {}
            for s in merged_segs:
                lbl = s.get("predicted_label", "other")
                label_counts[lbl] = label_counts.get(lbl, 0) + 1
            dominant = max(label_counts, key=label_counts.__getitem__) if label_counts else "other"
            dominant_desc = _LABEL_DESCRIPTIONS.get(dominant, "complete the task").lower()
            purpose = f"Step-by-step procedure to {dominant_desc} on {detected_platform}."

        return SOPDocument(
            title=f"SOP: {task_instruction}",
            purpose=purpose,
            prerequisites=prerequisites,
            steps=steps,
            expected_outcome=f"Successfully completed: {task_instruction}",
            troubleshooting=[
                "Verify all prerequisites are met",
                "Check application version compatibility",
                "Review error messages in the console or log output",
            ],
        )
