from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from app.ml.config import ACTIVITY_LABELS


@dataclass
class ActionRecord:
    action_type: str
    timestamp: float
    params: dict = field(default_factory=dict)
    t_end: float | None = None
    groundcua_id: str | None = None


@dataclass
class TaskMetadata:
    task_id: int
    instruction: str
    platform: str
    video_path: Path | None
    actions: list[ActionRecord]
    video_meta: dict | None
    activity_label: str
    workflow: str


# Platform → label mapping (checked first; most reliable signal)
_PLATFORM_LABELS: dict[str, str] = {
    "vscode": "coding_editing",
    "vs code": "coding_editing",
    "visual studio code": "coding_editing",
    "eclipse": "coding_editing",
    "intellij": "coding_editing",
    "pycharm": "coding_editing",
    "sublime": "coding_editing",
    "neovim": "coding_editing",
    "vim": "coding_editing",
    "nano": "coding_editing",
    "emacs": "coding_editing",
    "xcode": "coding_editing",
    "android studio": "coding_editing",
    "chrome": "web_browsing",
    "firefox": "web_browsing",
    "safari": "web_browsing",
    "browser": "web_browsing",
    "terminal": "terminal_ops",
    "bash": "terminal_ops",
    "zsh": "terminal_ops",
    "powershell": "terminal_ops",
    "cmd": "terminal_ops",
    "iterm": "terminal_ops",
    "parallels": "terminal_ops",
}

# Instruction keyword rules — ordered most-specific first
_LABEL_KEYWORDS: list[tuple[list[str], str]] = [
    # DevOps / infra (highly specific terms, check before generic coding)
    (["kubectl", "helm", "k8s", "kubernetes", "daemonset", "namespace", "ingress", "kube"], "kubernetes_ops"),
    (["terraform", "tf plan", "tf apply", "tfstate", "infrastructure as code", "hcl"], "terraform_iac"),
    (["docker", "container", "image build", "docker-compose", "dockerfile", "docker run"], "docker_workflow"),
    (["jenkins", "ci/cd", "ci cd", "build pipeline", "github actions", "gitlab ci", "circleci"], "jenkins_ci_cd"),
    (["aws", "s3 bucket", "ec2 instance", "lambda function", "cloudwatch", "iam role", "cloudformation"], "aws_console"),
    # Git (specific verbs — avoid matching "git" in "digital")
    ([" git ", "git clone", "git commit", "git push", "git pull", "git branch",
      "git merge", "git checkout", "git stash", "git rebase", "git log"], "git_operations"),
    # Debugging
    (["debug", "breakpoint", "step into", "step over", "step out", "watch expression",
      "call stack", "inspect variable", "attach debugger"], "debugging"),
    # Documentation
    (["readme", "wiki", "docstring", "jsdoc", "sphinx", "mkdocs", "swagger",
      "api doc", "changelog", "annotate"], "documentation"),
    # Terminal / shell operations
    (["run command", "execute command", "terminal", "shell", "bash script", "chmod",
      "chown", "sudo", "apt install", "apt-get", "yum install", "pip install",
      "npm install", "brew install", "systemctl", "crontab", "ssh ", "scp ",
      "curl ", "wget ", "grep ", "awk ", "sed ", "kill process", "ps aux",
      "top command", "htop", "df -", "du -", "tar ", "zip ", "unzip ",
      "find command", "locate ", "ln -", "mount ", "umount",
      "environment variable", "export ", "alias ", "history"], "terminal_ops"),
    # System / app configuration
    (["setting", "preference", "configure", "theme", "dark mode", "light mode",
      "font size", "keyboard shortcut", "workspace", "layout", "perspective",
      "permission", "timezone", "hostname", "package manager", "update package",
      "upgrade package", "install software", "uninstall", "enable feature",
      "disable feature", "system info", "system uptime", "change password"], "system_config"),
    # Web browsing
    (["browse", "navigate to", "open website", "open url", "bookmark", "tab",
      "browser extension", "download file", "search on", "google search"], "web_browsing"),
    # Coding / IDE (broad — after all specifics above)
    (["vscode", "vs code", "visual studio", "eclipse", "intellij", "pycharm",
      "write code", "edit code", "create file", "new file", "open file",
      "refactor", "autocomplete", "snippet", "linter", "formatter", "extension",
      "install plugin", "install extension", "language extension",
      "syntax highlight", "code review", "pull request", "open project",
      "import module", "function", "class ", "method ", "variable",
      "compile", "build project", "run test", "unit test"], "coding_editing"),
]


def derive_activity_label(instruction: str, platform: str = "") -> str:
    plat_lower = platform.lower().strip()
    instr_lower = instruction.lower().strip()

    # 1. Exact platform match — most reliable
    for plat_key, label in _PLATFORM_LABELS.items():
        if plat_key in plat_lower:
            return label

    # 2. Keyword match on instruction + platform combined
    text = f"{instr_lower} {plat_lower}"
    for keywords, label in _LABEL_KEYWORDS:
        for kw in keywords:
            if kw in text:
                return label

    return "other"


def _parse_action_log(path: Path) -> tuple[list[ActionRecord], str, str, int]:
    with open(path) as f:
        data = json.load(f)

    actions: list[ActionRecord] = []
    for entry in data.get("action_log", []):
        actions.append(
            ActionRecord(
                action_type=entry.get("action_type", "UNKNOWN").upper(),
                timestamp=float(entry.get("timestamp", 0)),
                params=entry.get("action_params", {}),
                groundcua_id=entry.get("groundcua_id"),
            )
        )

    return (
        actions,
        data.get("task_instruction", ""),
        data.get("platform", "unknown"),
        int(data.get("task_id", 0)),
    )


def _parse_jsonl_labels(path: Path) -> dict[int, list[dict]]:
    tasks: dict[int, list[dict]] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            tid = int(entry.get("task_id", 0))
            if tid not in tasks:
                tasks[tid] = []
            tasks[tid].append(entry)
    return tasks


def _build_task_from_jsonl(task_id: int, entries: list[dict]) -> TaskMetadata:
    actions: list[ActionRecord] = []
    for entry in entries:
        actions.append(
            ActionRecord(
                action_type=entry.get("action", "unknown").upper(),
                timestamp=float(entry.get("t_start", 0)),
                t_end=float(entry.get("t_end", 0)) if entry.get("t_end") else None,
                params=entry.get("params", {}),
            )
        )

    first = entries[0]
    instruction = first.get("nl", "") or first.get("workflow", "")
    platform = first.get("app", "unknown")

    return TaskMetadata(
        task_id=task_id,
        instruction=instruction,
        platform=platform,
        video_path=None,
        actions=actions,
        video_meta=None,
        activity_label=derive_activity_label(instruction, platform),
        workflow=instruction,
    )


def discover_tasks(dataset_root: Path) -> list[TaskMetadata]:
    tasks: list[TaskMetadata] = []
    _scan_directory(dataset_root, tasks)
    return tasks


def _scan_directory(directory: Path, tasks: list[TaskMetadata]) -> None:
    for entry in sorted(directory.iterdir()):
        if not entry.is_dir():
            if entry.suffix == ".zip":
                tasks.extend(_discover_from_zip(entry))
            continue

        action_log = entry / "action_log.json"
        if action_log.exists():
            _load_task(entry, action_log, tasks)
        else:
            _scan_directory(entry, tasks)


def _load_task(task_dir: Path, action_log: Path, tasks: list[TaskMetadata]) -> None:
    actions, instruction, platform, task_id = _parse_action_log(action_log)
    if task_id == 0:
        task_id = int(task_dir.name) if task_dir.name.isdigit() else hash(task_dir.name)

    label_file = task_dir / "label.txt"
    if label_file.exists():
        instruction = label_file.read_text().strip() or instruction

    video_path = task_dir / "video" / "video.mp4"
    video_meta = None
    if video_path.exists():
        meta_file = task_dir / "video" / "video_metadata.json"
        if meta_file.exists():
            with open(meta_file) as f:
                video_meta = json.load(f)

    tasks.append(
        TaskMetadata(
            task_id=task_id,
            instruction=instruction,
            platform=platform,
            video_path=video_path if video_path.exists() else None,
            actions=actions,
            video_meta=video_meta,
            activity_label=derive_activity_label(instruction, platform),
            workflow=instruction,
        )
    )


def _discover_from_zip(zip_path: Path) -> list[TaskMetadata]:
    tasks: list[TaskMetadata] = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()

            jsonl_files = [n for n in names if n.endswith(".jsonl")]
            for jf in jsonl_files:
                content = zf.read(jf).decode("utf-8")
                by_task: dict[int, list[dict]] = {}
                for line in content.strip().split("\n"):
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    tid = int(entry.get("task_id", 0))
                    if tid not in by_task:
                        by_task[tid] = []
                    by_task[tid].append(entry)

                for tid, entries in by_task.items():
                    tasks.append(_build_task_from_jsonl(tid, entries))

            if not jsonl_files:
                action_logs = [n for n in names if n.endswith("action_log.json")]
                for al in action_logs:
                    content = zf.read(al).decode("utf-8")
                    data = json.loads(content)
                    actions: list[ActionRecord] = []
                    for entry in data.get("action_log", []):
                        actions.append(
                            ActionRecord(
                                action_type=entry.get("action_type", "UNKNOWN").upper(),
                                timestamp=float(entry.get("timestamp", 0)),
                                params=entry.get("action_params", {}),
                                groundcua_id=entry.get("groundcua_id"),
                            )
                        )
                    instruction = data.get("task_instruction", "")
                    platform = data.get("platform", zip_path.stem)
                    task_id = int(data.get("task_id", 0))
                    if task_id == 0:
                        task_dir = str(Path(al).parent)
                        task_id = int(task_dir) if task_dir.isdigit() else hash(task_dir)

                    tasks.append(
                        TaskMetadata(
                            task_id=task_id,
                            instruction=instruction,
                            platform=platform,
                            video_path=None,
                            actions=actions,
                            video_meta=None,
                            activity_label=derive_activity_label(instruction, platform),
                            workflow=instruction,
                        )
                    )
    except (zipfile.BadZipFile, KeyError):
        pass
    return tasks


def task_level_split(
    tasks: list[TaskMetadata],
    test_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[list[TaskMetadata], list[TaskMetadata]]:
    import numpy as np

    rng = np.random.RandomState(seed)

    label_to_tasks: dict[str, list[TaskMetadata]] = {}
    for t in tasks:
        label_to_tasks.setdefault(t.activity_label, []).append(t)

    train: list[TaskMetadata] = []
    test: list[TaskMetadata] = []

    for label, label_tasks in label_to_tasks.items():
        indices = rng.permutation(len(label_tasks))
        split_idx = max(1, int(len(label_tasks) * (1 - test_ratio)))
        for i in indices[:split_idx]:
            train.append(label_tasks[i])
        for i in indices[split_idx:]:
            test.append(label_tasks[i])

    return train, test
