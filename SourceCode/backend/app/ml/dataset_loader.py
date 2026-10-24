from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path



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
# Order matters: longer/more-specific keys should appear before shorter ones that
# are substrings of them (e.g. "mozilla firefox" before "firefox").
_PLATFORM_LABELS: dict[str, str] = {
    # ── Code editors / IDEs ────────────────────────────────────────────────
    "visual studio code": "coding_editing",
    "vscode": "coding_editing",
    "vs code": "coding_editing",
    "android studio": "coding_editing",
    "intellij idea": "coding_editing",
    "intellij": "coding_editing",
    "pycharm": "coding_editing",
    "eclipse": "coding_editing",
    "netbeans": "coding_editing",
    "xcode": "coding_editing",
    "sublime text": "coding_editing",
    "sublime": "coding_editing",
    "atom editor": "coding_editing",
    "atom": "coding_editing",
    "brackets": "coding_editing",
    "notepad++": "coding_editing",
    "notepad": "coding_editing",
    "gedit": "coding_editing",
    "kate": "coding_editing",
    "geany": "coding_editing",
    "mousepad": "coding_editing",
    "bluefish": "coding_editing",
    "neovim": "coding_editing",
    "vim": "coding_editing",
    "nano": "coding_editing",
    "emacs": "coding_editing",
    "onlyoffice": "coding_editing",
    "libreoffice": "coding_editing",
    "openoffice": "coding_editing",
    # ── Browsers ───────────────────────────────────────────────────────────
    "mozilla firefox": "web_browsing",
    "google chrome": "web_browsing",
    "chromium": "web_browsing",
    "firefox": "web_browsing",
    "chrome": "web_browsing",
    "safari": "web_browsing",
    "opera": "web_browsing",
    "brave": "web_browsing",
    "edge": "web_browsing",
    "jitsi": "web_browsing",
    "wekan": "web_browsing",
    "signal": "web_browsing",
    "zoom": "web_browsing",
    "slack": "web_browsing",
    "teams": "web_browsing",
    "discord": "web_browsing",
    "telegram": "web_browsing",
    "thunderbird": "web_browsing",
    "evolution": "web_browsing",
    # ── Terminals / shells ─────────────────────────────────────────────────
    "terminal": "terminal_ops",
    "bash": "terminal_ops",
    "zsh": "terminal_ops",
    "powershell": "terminal_ops",
    "cmd": "terminal_ops",
    "iterm": "terminal_ops",
    "konsole": "terminal_ops",
    "gnome terminal": "terminal_ops",
    "xterm": "terminal_ops",
    "parallels": "terminal_ops",
    # ── System config / utilities ──────────────────────────────────────────
    "bitwarden": "system_config",
    "keepass": "system_config",
    "cryptomator": "system_config",
    "7-zip": "system_config",
    "7zip": "system_config",
    "gnome settings": "system_config",
    "system settings": "system_config",
    "control panel": "system_config",
    # ── Diagramming tools ──────────────────────────────────────────────────
    "draw.io": "diagram_design",
    "drawio": "diagram_design",
    "lucidchart": "diagram_design",
    "visio": "diagram_design",
    "excalidraw": "diagram_design",
    "miro": "diagram_design",
    # ── Media / video editing ──────────────────────────────────────────────
    "openshot": "media_editing",
    "kdenlive": "media_editing",
    "davinci resolve": "media_editing",
    "shotcut": "media_editing",
    "handbrake": "media_editing",
    "audacity": "media_editing",
    "vlc": "media_editing",
    # ── Diagramming / vector tools ─────────────────────────────────────────
    "inkscape": "diagram_design",
    "scribus": "diagram_design",
    "pencil": "diagram_design",
    "dia": "diagram_design",
    "yed": "diagram_design",
    "gliffy": "diagram_design",
    "plantuml": "diagram_design",
    "drawio": "diagram_design",
    "draw.io": "diagram_design",
    "lucidchart": "diagram_design",
    "visio": "diagram_design",
    "excalidraw": "diagram_design",
    "miro": "diagram_design",
    # ── Media / video / audio editing ──────────────────────────────────────
    "openshot": "media_editing",
    "kdenlive": "media_editing",
    "davinci resolve": "media_editing",
    "shotcut": "media_editing",
    "handbrake": "media_editing",
    "audacity": "media_editing",
    "vlc": "media_editing",
    "blender": "media_editing",
    "musescore": "media_editing",
    "lmms": "media_editing",
    "ardour": "media_editing",
    "pitivi": "media_editing",
    "flowblade": "media_editing",
    "cinelerra": "media_editing",
    "lightworks": "media_editing",
    "olive": "media_editing",
    "ffmpeg": "media_editing",
    "avidemux": "media_editing",
    "rhythmbox": "media_editing",
    "clementine": "media_editing",
    "banshee": "media_editing",
    "amarok": "media_editing",
    # ── Image / raster editing ─────────────────────────────────────────────
    "gimp": "image_editing",
    "krita": "image_editing",
    "darktable": "image_editing",
    "rawtherapee": "image_editing",
    "digikam": "image_editing",
    "shotwell": "image_editing",
    "gthumb": "image_editing",
    "imagemagick": "image_editing",
    "eog": "image_editing",
    "gwenview": "image_editing",
    "pinta": "image_editing",
    "mypaint": "image_editing",
    "photogimp": "image_editing",
    # ── File managers ──────────────────────────────────────────────────────
    "nautilus": "file_management",
    "dolphin file": "file_management",
    "thunar": "file_management",
    "nemo": "file_management",
    "pcmanfm": "file_management",
    "ranger": "file_management",
    "midnight commander": "file_management",
    "mc ": "file_management",
    "doublecmd": "file_management",
    "krusader": "file_management",
    "spacefm": "file_management",
    "mucommander": "file_management",
    "worker": "file_management",
    "xfe": "file_management",
    "rox": "file_management",
    # ── Office / productivity ──────────────────────────────────────────────
    "libreoffice writer": "coding_editing",
    "libreoffice calc": "coding_editing",
    "libreoffice impress": "coding_editing",
    "libreoffice draw": "diagram_design",
    "libreoffice base": "coding_editing",
    "libreoffice math": "coding_editing",
    "onlyoffice document": "coding_editing",
    "onlyoffice spreadsheet": "coding_editing",
    "onlyoffice presentation": "coding_editing",
    "wps office": "coding_editing",
    "wps": "coding_editing",
    "calligra": "coding_editing",
    "abiword": "coding_editing",
    "gnumeric": "coding_editing",
    "freeplane": "diagram_design",
    "freemind": "diagram_design",
    "xmind": "diagram_design",
    # ── Email / calendar / PIM ─────────────────────────────────────────────
    "thunderbird": "web_browsing",
    "evolution": "web_browsing",
    "geary": "web_browsing",
    "kmail": "web_browsing",
    "claws mail": "web_browsing",
    "sylpheed": "web_browsing",
    "gnome calendar": "web_browsing",
    "korganizer": "web_browsing",
    "kontact": "web_browsing",
    "GNOME Contacts": "web_browsing",
    # ── DevOps / containers / cloud ────────────────────────────────────────
    "portainer": "docker_workflow",
    "rancher": "kubernetes_ops",
    "lens": "kubernetes_ops",
    "openlens": "kubernetes_ops",
    "k9s": "kubernetes_ops",
    "helm": "kubernetes_ops",
    "podman": "docker_workflow",
    "buildah": "docker_workflow",
    "vagrant": "docker_workflow",
    "ansible": "jenkins_ci_cd",
    "puppet": "jenkins_ci_cd",
    "chef": "jenkins_ci_cd",
    "salt": "jenkins_ci_cd",
    "github desktop": "git_operations",
    "sourcetree": "git_operations",
    "gitkraken": "git_operations",
    "gitg": "git_operations",
    "gitk": "git_operations",
    "gitahead": "git_operations",
    "smartgit": "git_operations",
    # ── Databases ──────────────────────────────────────────────────────────
    "dbeaver": "coding_editing",
    "pgadmin": "coding_editing",
    "mysql workbench": "coding_editing",
    "sqlitebrowser": "coding_editing",
    "db browser": "coding_editing",
    "datagrip": "coding_editing",
    "valentina": "coding_editing",
    "beekeeper": "coding_editing",
    # ── Note-taking / knowledge ────────────────────────────────────────────
    "obsidian": "documentation",
    "notion": "documentation",
    "joplin": "documentation",
    "zettlr": "documentation",
    "logseq": "documentation",
    "cherrytree": "documentation",
    "zim": "documentation",
    "org-mode": "documentation",
    "wiki.js": "documentation",
    "confluence": "documentation",
    "bookstack": "documentation",
    # ── Virtual machines / remote desktop ──────────────────────────────────
    "virtualbox": "system_config",
    "vmware": "system_config",
    "qemu": "system_config",
    "virt-manager": "system_config",
    "gnome boxes": "system_config",
    "remmina": "system_config",
    "vinagre": "system_config",
    "vncviewer": "system_config",
    "xrdp": "system_config",
    "teamviewer": "system_config",
    "anydesk": "system_config",
    # ── Networking / security ──────────────────────────────────────────────
    "wireshark": "terminal_ops",
    "nmap": "terminal_ops",
    "netcat": "terminal_ops",
    "postman": "coding_editing",
    "insomnia": "coding_editing",
    "curl": "terminal_ops",
    "httpie": "terminal_ops",
    "filezilla": "terminal_ops",
    "winscp": "terminal_ops",
    "putty": "terminal_ops",
    "openssh": "terminal_ops",
    # ── Finance / accounting ───────────────────────────────────────────────
    "gnucash": "system_config",
    "homebank": "system_config",
    "kmymoney": "system_config",
    # ── Science / math ─────────────────────────────────────────────────────
    "octave": "coding_editing",
    "matlab": "coding_editing",
    "jupyter": "coding_editing",
    "rstudio": "coding_editing",
    "spyder": "coding_editing",
    "scilab": "coding_editing",
    "wxmaxima": "coding_editing",
    "geogebra": "coding_editing",
    # ── PDF / document viewers ─────────────────────────────────────────────
    "okular": "documentation",
    "evince": "documentation",
    "zathura": "documentation",
    "qpdf": "documentation",
    "pdftk": "documentation",
    "xreader": "documentation",
    "mupdf": "documentation",
    "mendeley": "documentation",
    "zotero": "documentation",
    "jabref": "documentation",
    # ── System monitors / admin ────────────────────────────────────────────
    "htop": "terminal_ops",
    "glances": "terminal_ops",
    "bashtop": "terminal_ops",
    "btop": "terminal_ops",
    "nmon": "terminal_ops",
    "gparted": "system_config",
    "disks": "system_config",
    "gnome disk utility": "system_config",
    "timeshift": "system_config",
    "baobab": "system_config",
    "stacer": "system_config",
    # ── Misc utilities ─────────────────────────────────────────────────────
    "calibre": "documentation",
    "anki": "documentation",
    "chezmoi": "system_config",
    "syncthing": "system_config",
    "nextcloud": "system_config",
    "owncloud": "system_config",
    "rclone": "terminal_ops",
    "rsync": "terminal_ops",
    "duplicati": "system_config",
    "backintime": "system_config",
    "deja-dup": "system_config",
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
    # Web browsing (use "new tab"/"open tab" not bare "tab" to avoid substring hits)
    (["browse", "navigate to", "open website", "open url", "bookmark", "new tab",
      "open tab", "browser extension", "download file", "search on", "google search",
      "web browser", "incognito", "private window"], "web_browsing"),
    # File management
    (["file manager", "copy file", "move file", "rename file", "delete file",
      "create folder", "new folder", "cut paste", "file browser",
      "nautilus", "thunar", "dolphin", "nemo", "pcmanfm",
      "open folder", "navigate folder", "extract archive",
      "compress file", "zip file", "unzip file", "file permission",
      "show hidden", "bookmark folder", "sort files", "search file"], "file_management"),
    # Image / raster editing
    (["gimp", "krita", "darktable", "rawtherapee", "digikam",
      "brightness contrast", "hue saturation", "color balance",
      "crop image", "resize image", "rotate image", "flip image",
      "add layer", "merge layer", "flatten image", "color picker",
      "clone stamp", "healing brush", "dodge burn", "levels curve",
      "sharpen", "blur image", "noise reduction", "white balance",
      "raw processing", "export image", "photo edit", "retouch",
      "selection tool", "magic wand", "lasso tool", "eraser tool"], "image_editing"),
    # Diagramming / visual design
    (["diagram", "canvas", "shape", "connector", "flowchart", "draw.io",
      "drawio", "insert shape", "fill color", "add shape", "lock shape",
      "group object", "align shape", "snap to grid", "export diagram",
      "rectangle shape", "ellipse", "text box", "arrow", "svg format"], "diagram_design"),
    # Media / video editing
    (["timeline", "video clip", "audio track", "keyframe", "mute audio",
      "export video", "trim clip", "split clip", "transition", "blur effect",
      "frame rate", "render", "openshot", "picture-in-picture",
      "fast forward", "rewind", "playback", "project file", "audio level",
      "duplicate clip", "snapping", "track 1", "track 2", "track 3"], "media_editing"),
    # Coding / IDE (broad — after all specifics above)
    (["vscode", "vs code", "visual studio", "eclipse", "intellij", "pycharm",
      "netbeans", "bluefish", "onlyoffice", "libreoffice",
      "write code", "edit code", "create file", "new file", "open file",
      "refactor", "autocomplete", "snippet", "linter", "formatter",
      "install plugin", "install extension", "language extension",
      "syntax highlight", "code review", "pull request", "open project",
      "import module", "compile", "build project", "run test", "unit test",
      "code folding", "line numbers", "error highlighting", "code completion",
      "enable line", "disable line", "split editor", "split vertically",
      "split horizontally", "editor window", "editor panel",
      "maven project", "gradle project", "java project",
      "enable word wrap", "word wrap", "line wrap"], "coding_editing"),
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
