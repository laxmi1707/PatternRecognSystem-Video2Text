"""Survey a CUA-Suite folder without touching a single video frame.

Reads every action_log.json (and label.txt, which the backend prefers when it
exists), applies the backend's own derive_activity_label, and reports what the
label taxonomy would actually look like if the whole dataset were used, plus
what extraction would cost.
"""
from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from pathlib import Path

log = logging.getLogger("v2k.survey")

# Measured on this workstation: 16 threads, both OCR passes, below-normal priority.
SECONDS_PER_KEYFRAME = 5.1


def survey(root: Path, per_app_detail: int = 0) -> dict:
    from app.ml.config import ACTIVITY_LABELS
    from app.ml.dataset_loader import derive_activity_label

    by_label: Counter = Counter()
    by_app_label: dict[str, Counter] = defaultdict(Counter)
    label_examples: dict[str, list[str]] = defaultdict(list)
    tasks = keyframes = 0
    video_seconds = 0.0
    with_video = 0
    broken_video: list[str] = []

    for log_path in root.rglob("action_log.json"):
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        task_dir = log_path.parent
        instruction = data.get("task_instruction", "")
        label_file = task_dir / "label.txt"
        if label_file.exists():  # discover_tasks prefers label.txt over the log
            text = label_file.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                instruction = text
        platform = data.get("platform", task_dir.parent.name)
        label = derive_activity_label(instruction, platform)

        tasks += 1
        by_label[label] += 1
        by_app_label[platform][label] += 1
        if len(label_examples[label]) < 3:
            label_examples[label].append(instruction[:100])
        keyframes += len({round(float(a.get("timestamp", 0)), 6) for a in data.get("action_log", [])})

        meta = task_dir / "video" / "video_metadata.json"
        if meta.exists():
            try:
                seconds = float(json.loads(meta.read_text())["duration_seconds"])
            except Exception:
                seconds = 0.0
            # Some clips have a negative frame count, so the backend's
            # total_frames / fps is nonsense and its segments come out empty.
            if 0 < seconds <= 7200:
                video_seconds += seconds
                with_video += 1
            else:
                broken_video.append(str(task_dir.relative_to(root)))

    hours = keyframes * SECONDS_PER_KEYFRAME / 3600
    print(f"{tasks} tasks in {len(by_app_label)} apps, {with_video} with a usable video, "
          f"{video_seconds / 3600:.1f} h of footage, {keyframes} keyframes")
    if broken_video:
        print(f"{len(broken_video)} task(s) have an unreadable duration (negative frame count); "
              f"the backend would build empty, all-zero features for them, e.g. {broken_video[0]}")
    print(f"extracting all of it: about {hours:.0f} h of CPU at the measured "
          f"{SECONDS_PER_KEYFRAME:.1f} s per keyframe\n")

    print(f"{'label':<18}{'tasks':>7}{'share':>8}   {'apps':>5}")
    for label in ACTIVITY_LABELS:
        n = by_label.get(label, 0)
        apps = sum(1 for c in by_app_label.values() if c.get(label))
        bar = "#" * int(40 * n / max(tasks, 1))
        print(f"{label:<18}{n:>7}{n / max(tasks, 1):>7.1%}   {apps:>5}  {bar}")

    print("\nsample instructions per label:")
    for label in ACTIVITY_LABELS:
        for ex in label_examples.get(label, [])[:2]:
            print(f"  [{label:<15}] {ex}")

    if per_app_detail:
        print(f"\ntop {per_app_detail} apps by task count:")
        for app, counts in sorted(by_app_label.items(), key=lambda x: -sum(x[1].values()))[:per_app_detail]:
            top = ", ".join(f"{k} {v}" for k, v in counts.most_common(3))
            print(f"  {app:<22}{sum(counts.values()):>5} tasks   {top}")

    return {"tasks": tasks, "keyframes": keyframes, "video_hours": video_seconds / 3600,
            "broken_video": broken_video,
            "by_label": dict(by_label), "by_app_label": {a: dict(c) for a, c in by_app_label.items()}}
