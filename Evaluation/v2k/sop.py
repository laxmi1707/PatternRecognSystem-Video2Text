"""Turn one cached recording into a step-by-step procedure with timestamps.

The backend already has an SOP generator, but its steps read
"Perform coding editing activity on NetBeans. Detected text: <gibberish>",
because the step title is the predicted class and the text comes from OCR of
the squashed 640x480 frame.

This one uses what the frame cache holds instead:

  what was clicked   every CLICK carries screen coordinates, and the
                     full-resolution OCR of that exact frame carries text with
                     boxes, so the label under the cursor names the control:
                     "Click 'New Project'", not "Click at (1097, 801)".
  what was typed     TYPING actions carry the text itself.
  when               action timestamps, grouped into the backend's segments.

No LLM is involved, so nothing here can be invented: every step names an action
that is in the log and, where quoted, text that OCR actually read on screen.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from v2k.frames import cache_paths

log = logging.getLogger("v2k.sop")

# How far from the click a text box may sit and still be taken as its label.
NEAR_PX = 70
VERB = {
    "CLICK": "Click", "DOUBLE_CLICK": "Double-click", "RIGHT_CLICK": "Right-click",
    "TYPING": "Type", "HOTKEY": "Press", "PRESS": "Press", "SCROLL": "Scroll",
    "DRAG_TO": "Drag to", "MOUSE_DOWN": "Hold", "MOUSE_UP": "Release",
}


@dataclass
class Step:
    seconds: float
    action: str
    text: str
    evidence: str = ""

    @property
    def clock(self) -> str:
        return f"{int(self.seconds) // 60:02d}:{int(self.seconds) % 60:02d}"


@dataclass
class Section:
    index: int
    start: float
    end: float
    activity: str
    steps: list[Step] = field(default_factory=list)
    confidence: float | None = None  # set only when a trained model named the activity
    segments: int = 1  # how many of the recording's segments this heading covers


def merge_adjacent(sections: list[Section]) -> list[Section]:
    """Join consecutive sections that carry the same activity.

    A run of identical headings tells the reader nothing and makes the procedure
    look longer than it is: a recording whose twelve segments are all classified
    the same reads as twelve steps of an unnamed process rather than one. The
    steps keep their own timestamps, so the pause between two merged segments is
    still visible in the table.

    The merged confidence is the mean over the segments it covers, and the count
    is kept so the heading can say how many predictions stand behind it.
    """
    merged: list[Section] = []
    for section in sections:
        last = merged[-1] if merged else None
        if last is not None and last.activity == section.activity:
            confs = [c for c in (last.confidence, section.confidence) if c is not None]
            weights = (last.segments, 1)
            last.end = section.end
            last.steps.extend(section.steps)
            last.segments += 1
            if len(confs) == 2:
                last.confidence = (last.confidence * weights[0] + section.confidence) / sum(weights)
            elif confs:
                last.confidence = confs[0]
            continue
        merged.append(Section(index=len(merged), start=section.start, end=section.end,
                              activity=section.activity, steps=list(section.steps),
                              confidence=section.confidence))
    return merged


def _label_at(regions: list, x: float, y: float) -> tuple[str, float]:
    """The OCR text under (x, y), or the nearest one within NEAR_PX."""
    best, best_d = "", float("inf")
    for text, x1, y1, x2, y2, conf in regions or []:
        if not text or conf < 0.4:
            continue
        if x1 <= x <= x2 and y1 <= y <= y2:
            return text, 0.0
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        d = float(np.hypot(cx - x, cy - y))
        if d < best_d:
            best, best_d = text, d
    return (best, best_d) if best_d <= NEAR_PX else ("", best_d)


def _describe(action: dict, regions: list) -> tuple[str, str]:
    """(what the step says, what it was read from)."""
    kind = (action.get("action_type") or "UNKNOWN").upper()
    params = action.get("action_params") or action.get("params") or {}
    verb = VERB.get(kind, kind.replace("_", " ").title())

    if kind == "TYPING":
        typed = params.get("text", "")
        return f'Type "{typed}"', ""
    if kind in {"HOTKEY", "PRESS"}:
        keys = params.get("keys") or params.get("text") or ""
        keys = " + ".join(keys) if isinstance(keys, list) else str(keys)
        return f"Press {keys}", ""

    x, y = params.get("x"), params.get("y")
    if x is None or y is None:
        return verb, ""
    label, distance = _label_at(regions, float(x), float(y))
    if label:
        near = "" if distance == 0 else f" (nearest label, {distance:.0f} px away)"
        return f'{verb} "{label}"', f"OCR at ({int(x)}, {int(y)}){near}"
    return f"{verb} at ({int(x)}, {int(y)})", "no text read at that point"


def predicted_activities(bundle: Path, app: str, task_id: int) -> tuple[list[str], list[float]]:
    """Per-segment labels from a trained bundle, indexed by segment index."""
    import joblib

    from v2k.predict import predict_cached

    # A bundle trained with --level task saw one averaged row per recording; run
    # per segment it would answer confidently on inputs unlike anything it was
    # fitted on, and the SOP would read as though that were a real per-step call.
    if joblib.load(bundle).get("level", "segment") == "task":
        raise SystemExit(
            f"{bundle.name} was trained at recording level, so it cannot name individual steps. "
            f"Use a bundle from a run without --level task."
        )

    rows = predict_cached(bundle, app, task_id)
    n = max(r["segment"] for r in rows) + 1
    labels, confs = ["unknown"] * n, [None] * n
    for r in rows:
        labels[r["segment"]] = r["label"]
        confs[r["segment"]] = r["confidence"]
    return labels, confs


def build(app: str, task_id: int, predictions: list[str] | None = None,
          confidences: list[float] | None = None, merge: bool = True) -> tuple[dict, list[Section]]:
    npz_path, json_path = cache_paths(app, task_id)
    if not json_path.exists():
        raise SystemExit(f"{app}/{task_id} is not in the frame cache")
    record = json.loads(json_path.read_text(encoding="utf-8"))
    frames = record["frames"]
    if not record.get("native_ocr"):
        log.warning("this task was cached without full-resolution OCR; clicks will not be named")

    sections: list[Section] = []
    for seg in record["segments"]:
        # The frame captured at an action's own timestamp is the one that shows
        # what the user was looking at when they acted.
        # extract_segments takes one keyframe per action in order, so the i-th
        # keyframe is the frame the i-th action happened on.
        refs = seg["keyframes"]
        activity = (predictions[seg["index"]] if predictions and seg["index"] < len(predictions)
                    else record.get("proposed_label") or record.get("keyword_label", "unknown"))
        conf = (confidences[seg["index"]] if confidences and seg["index"] < len(confidences) else None)
        section = Section(index=seg["index"], start=seg["start"], end=seg["end"], activity=activity,
                          confidence=conf)

        seen: set[tuple] = set()
        for pos, action in enumerate(seg["actions"]):
            kind = (action.get("action_type") or "").upper()
            if kind == "MOVE_TO":
                continue  # a move is always followed by the click that matters
            ts = float(action.get("timestamp", seg["start"]))
            ref = refs[min(pos, len(refs) - 1)] if refs else None
            regions = frames[ref].get("ocr_native_regions") if ref is not None else []
            text, evidence = _describe(action, regions)
            key = (round(ts, 2), text)
            if key in seen:
                continue
            seen.add(key)
            section.steps.append(Step(seconds=ts, action=kind, text=text, evidence=evidence))
        sections.append(section)

    meta = {
        "task_id": record.get("task_id"),
        "app": record.get("app"),
        "platform": record.get("platform"),
        "instruction": record.get("instruction", ""),
        "duration": record["video"]["duration_seconds"],
        "n_segments": len(record["segments"]),
    }
    return meta, merge_adjacent(sections) if merge else sections


def to_markdown(meta: dict, sections: list[Section]) -> str:
    lines = [f"# {meta['instruction'] or 'Recorded procedure'}", ""]
    lines.append(f"**Application:** {meta['platform']}  ·  **Recording:** "
                 f"{meta['duration']:.0f} s, {meta['n_segments']} segments  ·  "
                 f"**Source:** task {meta['task_id']}")
    lines += ["", "Steps are taken from the action log; quoted names are text that OCR read at "
                  "the clicked position in that frame.", ""]
    n = 0
    heading = 0
    for section in sections:
        if not section.steps:
            continue
        heading += 1
        said = "" if section.confidence is None else f", model {section.confidence:.0%} sure"
        if section.segments > 1:
            said += f" over {section.segments} segments"
        lines.append(f"## {heading}. {section.activity.replace('_', ' ').title()} "
                     f"({int(section.start) // 60:02d}:{int(section.start) % 60:02d}"
                     f"-{int(section.end) // 60:02d}:{int(section.end) % 60:02d}{said})")
        lines.append("")
        lines.append("| | time | step | read from |")
        lines.append("|---:|---|---|---|")
        for step in section.steps:
            n += 1
            lines.append(f"| {n} | {step.clock} | {step.text} | {step.evidence} |")
        lines.append("")
    return "\n".join(lines) + "\n"
