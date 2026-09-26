"""A label set derived from what the recordings actually contain.

The backend's ten DevOps classes were written for footage this dataset does not
have: terraform_iac and jenkins_ci_cd match nothing at all, kubernetes_ops
matches five tasks (all of them the word "podcast"), and 92% of tasks fall into
coding_editing or other. What the 7021 instructions do have is a small set of
recurring actions - the leading verb alone covers three quarters of them - so
the categories below are built from those verbs.

Each rule is (category, leading verbs, whole-sentence keywords). The first rule
that matches wins, so the order is the tie-breaker: a specific intent
(communicating, searching, deleting) is checked before a generic one
(navigating, editing).
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

MEDIA_WORDS = {
    "video", "audio", "clip", "track", "podcast", "recording", "screen", "song", "music",
    "media", "playback", "frame rate", "movie", "sound", "voice",
}
SHELL_WORDS = {
    "command", "terminal", "script", "service", "process", "directory", "sudo", "apt",
    "package", "shell", "bash", "executed", "daemon", "port", "permission",
}

# Applications whose whole interface is a command prompt.
TERMINAL_APPS = {"Ubuntu Terminal", "Bash", "GNU Octave"}

# Editors and IDEs. "Run the program" there is a Run button rather than a typed
# command, but it still produces console output, so it is closer to issuing a
# command than to editing text.
DEV_APPS = {
    "VSCode", "Spyder", "IntelliJ IDEA", "PyCharm", "Geany", "KDevelop", "Eclipse",
    "NetBeans", "Atom", "Brackets", "Code__Blocks", "Arduino IDE", "Bluefish",
}

# Tokens that only turn up when a command is genuinely being issued. SHELL_WORDS
# is far too loose for this on its own: "process" matches "Start the extraction
# process" in 7-Zip, and "directory" matches any file dialog.
COMMAND_TOKENS = {
    "sudo", "apt", "chmod", "chown", "grep", "ping", "alias", "disown", "flake8",
    "systemctl", "pid", "from history", "the last command", "the last executed command",
    " ls", "ls ", "cd ", "mkdir", "rm ", "cat ", "echo ", "ssh", "git ", "pip ",
    "npm ", "docker", "curl", "wget", "in the terminal", "running services",
    "running processes", "symbolic link",
}

# What a developer application is running, when it is running something.
CODE_OBJECTS = {
    "the code", "the program", "the kernel", "cell", "tasks.json", ".java", ".py",
    ".cpp", "a launch", "the project", "a file '",
}

CATEGORIES: list[tuple[str, set[str], set[str]]] = [
    # Only verbs that never mean anything else. "run", "execute", "count", "list",
    # "start", "stop", "repeat" and "kill" all appear constantly in GUI tasks
    # ("Count monthly expenses" is bookkeeping), so they reach run_command only
    # through _is_command() below, which demands a terminal or a real command.
    ("run_command", {
        "grep", "chmod", "chown",
    }, {"in the terminal", "the last executed command"}),
    ("communicate", {
        "send", "share", "invite", "reply", "comment", "react", "forward", "mention",
        "subscribe", "unsubscribe", "follow", "unfollow", "notify", "post", "message",
    }, {"send a message", "direct message", "to the channel"}),
    ("search_filter", {
        "search", "find", "filter", "locate", "query", "lookup", "browse",
    }, {"search for", "filter by"}),
    ("delete_remove", {
        "delete", "remove", "clear", "erase", "uninstall", "discard", "trash",
    }, set()),
    ("organize_items", {
        "sort", "arrange", "organize", "organise", "order", "group", "pin", "unpin",
        "bookmark", "mark", "flag", "star", "favorite", "favourite", "tag", "categorize",
        "rank", "archive",
    }, {"in alphabetical order"}),
    ("media_control", {
        "play", "pause", "trim", "crop", "render", "stream", "mute", "unmute",
    }, set()),
    ("file_manage", {
        "save", "export", "import", "download", "upload", "print", "backup", "restore",
        "load", "extract", "compress", "sync",
    }, {"save the file", "export as", "as pdf"}),
    ("format_style", {
        "change", "apply", "adjust", "increase", "decrease", "align", "resize", "format",
        "style", "zoom", "rotate", "bold", "italic", "underline", "highlight", "colour",
        "color", "scale", "indent",
    }, {"font size", "dark mode", "light theme", "the theme"}),
    ("configure_option", {
        "enable", "disable", "turn", "toggle", "set", "configure", "customize", "customise",
        "use", "allow", "activate", "deactivate", "check", "uncheck", "assign", "bind",
        "install", "update", "reset", "lock", "unlock", "stop", "start",
    }, {"in settings", "in preferences", "the option", "notifications"}),
    ("insert_element", {
        "insert", "draw", "embed", "place", "append", "attach", "plot", "link",
    }, {"insert a", "draw a"}),
    ("create_item", {
        "create", "new", "generate", "duplicate", "make", "build", "compose", "record",
    }, {"create a new", "a new file", "a new project"}),
    ("edit_content", {
        "edit", "rename", "replace", "move", "copy", "cut", "type", "write", "modify",
        "reorder", "merge", "split", "combine", "convert", "fix", "add", "enter", "drag",
        "flip", "pan", "join", "fill", "paste", "undo", "redo", "adjustments",
    }, {"rename the", "replace all"}),
    ("navigate_view", {
        "open", "view", "show", "display", "switch", "go", "navigate", "close", "hide",
        "expand", "collapse", "scroll", "minimize", "maximize", "preview", "access",
        "click", "select", "focus", "return", "back", "reload", "refresh",
    }, {"the menu", "the sidebar", "the panel", "the tab"}),
]

CATEGORY_NAMES = [c for c, _, _ in CATEGORIES] + ["other"]


@dataclass
class TaskText:
    app: str
    task_id: int
    text: str


def _is_command(text: str, app: str) -> bool:
    """Whether the instruction really issues a command, or only uses the word.

    v1 accepted any SHELL_WORDS match, which put 19 of 40 `run_command`
    recordings in the wrong class: "Start the extraction process" in 7-Zip,
    "Count monthly expenses" in Frappe Books, "Perform a word count" in
    OnlyOffice. Typing `ls` at a prompt and clicking Extract share no pixels, so
    the model could learn neither and scored F1 0.00 on the class.

    Evidence now has to be one of three concrete things.
    """
    if app in TERMINAL_APPS:
        return True
    if any(tok in text for tok in COMMAND_TOKENS):
        return True
    return app in DEV_APPS and any(obj in text for obj in CODE_OBJECTS)


def propose_label(instruction: str, app: str = "") -> str:
    """Category for one instruction: leading verb first, then keywords.

    Two verbs are ambiguous on their own and are settled by what follows:
    "record"/"play" mean media only next to a media word ("Record office rent
    payment of $500" is bookkeeping), and command verbs only mean a command when
    `_is_command` finds a terminal, a real command token, or code being run in a
    developer application.
    """
    text = instruction.strip().lower()
    if not text:
        return "other"
    words = re.findall(r"[a-z']+", text)
    lead = words[0] if words else ""
    # "In VS Code, enable Auto Save" - step over a leading preposition or app name
    if lead in {"in", "on", "from", "at", "the", "please", "using", "with", "to"} and len(words) > 2:
        for w in words[1:6]:
            if any(w in verbs for _, verbs, _ in CATEGORIES):
                lead = w
                break

    media = any(w in text for w in MEDIA_WORDS)
    if lead in {"play", "pause", "record", "capture"} and media:
        return "media_control"
    if lead in {"stop", "start", "count", "repeat", "run", "execute", "kill", "list",
                "restart", "ping"} and _is_command(text, app):
        return "run_command"

    for name, verbs, _ in CATEGORIES:
        if lead in verbs:
            return name
    for name, _, phrases in CATEGORIES:
        if any(p in text for p in phrases):
            return name
    for name, verbs, _ in CATEGORIES:  # a matching verb further into the sentence
        if any(w in verbs for w in words[:6]):
            return name
    return "other"


def read_tasks(root: Path) -> list[TaskText]:
    tasks: list[TaskText] = []
    for log_path in root.rglob("action_log.json"):
        task_dir = log_path.parent
        text = ""
        label_file = task_dir / "label.txt"
        if label_file.exists():
            text = label_file.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            try:
                text = json.loads(log_path.read_text(encoding="utf-8")).get("task_instruction", "")
            except Exception:
                continue
        text = text.split("\n")[0].strip()  # label.txt sometimes repeats the instruction
        if not text:
            continue
        task_id = int(task_dir.name) if task_dir.name.isdigit() else 0
        tasks.append(TaskText(app=task_dir.parent.name, task_id=task_id, text=text))
    return tasks


def report(root: Path, out_md: Path, out_csv: Path, examples_per_class: int = 4) -> dict:
    from app.ml.dataset_loader import derive_activity_label

    tasks = read_tasks(root)
    counts: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    per_app: dict[str, Counter] = defaultdict(Counter)
    old_counts: Counter = Counter()

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["task_id", "app", "label", "instruction"])
        for t in tasks:
            label = propose_label(t.text, t.app)
            counts[label] += 1
            per_app[t.app][label] += 1
            old_counts[derive_activity_label(t.text, t.app)] += 1
            if len(examples[label]) < examples_per_class:
                examples[label].append(t.text[:90])
            writer.writerow([t.task_id, t.app, label, t.text])

    total = len(tasks)
    lines = ["# Proposed label set", ""]
    lines.append(f"{total} tasks, {len({t.app for t in tasks})} applications. "
                 f"Each label is assigned by the leading verb of the task instruction; "
                 f"`{out_csv.name}` has one row per task and can be fed straight to "
                 f"`python -m v2k train --labels csv:{out_csv.name}`.")
    lines += ["", "## What the recordings actually contain", "",
              "| category | tasks | share | apps | example instructions |", "|---|---:|---:|---:|---|"]
    for name, n in counts.most_common():
        apps = sum(1 for c in per_app.values() if c.get(name))
        ex = "; ".join(f"*{e}*" for e in examples[name][:2])
        lines.append(f"| `{name}` | {n} | {n / total:.1%} | {apps} | {ex} |")

    lines += ["", "## The same tasks under the current DevOps labels", "",
              "| category | tasks | share |", "|---|---:|---:|"]
    from app.ml.config import ACTIVITY_LABELS
    for name in ACTIVITY_LABELS:
        n = old_counts.get(name, 0)
        lines.append(f"| `{name}` | {n} | {n / total:.1%} |")

    biggest = counts.most_common(1)[0]
    smallest = min((c for c in counts.items() if c[0] != "other"), key=lambda x: x[1])
    lines += ["", "## Why this one is trainable and that one is not", "",
              f"- Largest class: `{biggest[0]}` at {biggest[1] / total:.1%}. Always answering it "
              f"scores {biggest[1] / total:.1%} accuracy, so a model has room to beat the baseline.",
              f"  Under the DevOps labels the largest class is "
              f"`{old_counts.most_common(1)[0][0]}` at {old_counts.most_common(1)[0][1] / total:.1%}.",
              f"- Smallest named class: `{smallest[0]}` with {smallest[1]} tasks - enough for "
              f"five-fold cross-validation, which needs a handful of tasks per fold.",
              f"- Unmatched: {counts.get('other', 0)} tasks ({counts.get('other', 0) / total:.1%}) "
              f"fall in `other`; under the DevOps labels it is "
              f"{old_counts.get('other', 0)} ({old_counts.get('other', 0) / total:.1%}).",
              f"- Empty classes: {sum(1 for n in ACTIVITY_LABELS if not old_counts.get(n))} of "
              f"{len(ACTIVITY_LABELS)} DevOps labels match nothing, against "
              f"{sum(1 for n in CATEGORY_NAMES if not counts.get(n))} here.",
              "",
              "These labels come from the instruction text, so they are still weak supervision: "
              "they say what the task was asked to do, not what the pixels show. They are a "
              "starting point for hand-checking, not ground truth.",
              ""]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"tasks": total, "counts": dict(counts), "old_counts": dict(old_counts)}
