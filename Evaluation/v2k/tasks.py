"""Find downloaded tasks, parsed by the backend's own dataset loader."""
from __future__ import annotations

from pathlib import Path

from v2k.download import safe_name
from v2k.env import VIDEOS


def local_apps(root: Path | None = None) -> list[str]:
    """App folders under a dataset root: downloaded ones, or any folder holding tasks."""
    base = root or VIDEOS
    if not base.is_dir():
        return []
    if root is None:
        return sorted(p.name for p in base.iterdir() if (p / ".unpacked").exists())
    return sorted(
        p.name for p in base.iterdir()
        if p.is_dir() and not p.name.startswith("__") and any(p.glob("*/action_log.json"))
    )


def discover(apps: list[str] | None = None, root: Path | None = None) -> list[tuple[str, object]]:
    """(app folder, TaskMetadata) for every task that has a video on disk.

    `root` points at any folder laid out as <root>/<app>/<task_id>/action_log.json,
    so the team's own 48 GB copy can be read in place, without downloading again.
    discover_tasks expects <root>/<task_id>/...; a folder that nests its tasks one
    level deeper is handled by calling it on each parent folder.
    """
    base = root or VIDEOS
    folders = [safe_name(a) for a in apps] if apps else local_apps(root)
    found: list[tuple[str, object]] = []
    for folder in folders:
        app_dir = base / folder
        if not app_dir.is_dir():
            raise SystemExit(f"{folder} is not under {base}")
        for log_path in sorted(app_dir.rglob("action_log.json")):
            task = _read_task(log_path)
            if task is not None and task.video_path is not None:
                found.append((folder, task))
    return found


def _read_task(log_path: Path):
    """One task, built exactly as the backend's discover_tasks builds it.

    The backend opens action_log.json and label.txt without naming an encoding,
    so on Windows they are read as cp1252 and 111 of this dataset's label files
    (they contain curly quotes) raise UnicodeDecodeError. discover_tasks has no
    try/except, and its caller treats any failure as "no dataset" and trains on
    synthetic data instead - silently. Reading as UTF-8 here keeps the labels
    and instructions identical to what the backend would produce once fixed.
    """
    import json

    from app.ml.dataset_loader import ActionRecord, TaskMetadata, derive_activity_label

    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    task_dir = log_path.parent

    actions = [
        ActionRecord(
            action_type=entry.get("action_type", "UNKNOWN").upper(),
            timestamp=float(entry.get("timestamp", 0)),
            params=entry.get("action_params", {}),
            groundcua_id=entry.get("groundcua_id"),
        )
        for entry in data.get("action_log", [])
    ]
    instruction = data.get("task_instruction", "")
    platform = data.get("platform", task_dir.parent.name)
    task_id = int(data.get("task_id", 0)) or (int(task_dir.name) if task_dir.name.isdigit() else hash(task_dir.name))

    label_file = task_dir / "label.txt"
    if label_file.exists():
        instruction = label_file.read_text(encoding="utf-8", errors="replace").strip() or instruction

    video_path = task_dir / "video" / "video.mp4"
    video_meta = None
    meta_file = task_dir / "video" / "video_metadata.json"
    if video_path.exists() and meta_file.exists():
        try:
            video_meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            video_meta = None

    return TaskMetadata(
        task_id=task_id,
        instruction=instruction,
        platform=platform,
        video_path=video_path if video_path.exists() else None,
        actions=actions,
        video_meta=video_meta,
        activity_label=derive_activity_label(instruction, platform),
        workflow=instruction,
    )


def interleave_by_app(pairs: list[tuple[str, object]]) -> list[tuple[str, object]]:
    """Round-robin across apps, so an interrupted run still covers every app."""
    by_app: dict[str, list] = {}
    for app, task in pairs:
        by_app.setdefault(app, []).append((app, task))
    order: list[tuple[str, object]] = []
    while by_app:
        for app in sorted(by_app):
            order.append(by_app[app].pop(0))
            if not by_app[app]:
                del by_app[app]
    return order


def usable_video(task) -> str:
    """'' if the recording is fine, otherwise why it must be skipped.

    A few clips report a negative frame count, so the backend's
    total_frames / fps is nonsense and every feature it builds is zero.
    """
    import json

    meta = task.video_path.parent / "video_metadata.json"
    if not meta.exists():
        return ""
    try:
        seconds = float(json.loads(meta.read_text())["duration_seconds"])
    except Exception:
        return "unreadable video_metadata.json"
    if not 0 < seconds <= 7200:
        return f"video metadata says {seconds:.0f} s"
    return ""
