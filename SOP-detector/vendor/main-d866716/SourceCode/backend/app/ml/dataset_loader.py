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


_LABEL_KEYWORDS: list[tuple[list[str], str]] = [
    (["git", "clone", "commit", "push", "pull", "branch", "merge", "checkout"], "git_operations"),
    (["docker", "container", "image", "compose", "dockerfile"], "docker_workflow"),
    (["kubernetes", "kubectl", "helm", "k8s", "pod", "deployment"], "kubernetes_ops"),
    (["terraform", "tf plan", "tf apply", "infrastructure as code"], "terraform_iac"),
    (["aws", "s3 ", "ec2", "lambda", "console", "cloudwatch"], "aws_console"),
    (["jenkins", "pipeline", "ci/cd", "ci cd", "build pipeline"], "jenkins_ci_cd"),
    (
        [
            "code", "edit", "write", "extension", "install", "project",
            "new file", "open file", "save", "font", "theme", "shortcut",
            "ide", "plugin", "customize", "setting", "preference",
        ],
        "coding_editing",
    ),
    (["debug", "breakpoint", "inspect", "step into", "step over", "watch"], "debugging"),
    (["doc", "readme", "wiki", "comment", "annotation", "markdown", "note"], "documentation"),
]


def derive_activity_label(instruction: str, platform: str = "") -> str:
    text = f"{instruction} {platform}".lower()
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

    for task_dir in sorted(dataset_root.iterdir()):
        if not task_dir.is_dir():
            if task_dir.suffix == ".zip":
                tasks.extend(_discover_from_zip(task_dir))
            continue

        action_log = task_dir / "action_log.json"
        if not action_log.exists():
            continue

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

    return tasks


def _discover_from_zip(zip_path: Path) -> list[TaskMetadata]:
    tasks: list[TaskMetadata] = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            jsonl_files = [n for n in zf.namelist() if n.endswith(".jsonl")]
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
