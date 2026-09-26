"""Fetch CUA-Suite recordings (ServiceNow/VideoCUA), one application at a time."""
from __future__ import annotations

import json
import logging
import shutil
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from v2k.env import VIDEOS, ZIPS

log = logging.getLogger("v2k.download")

REPO = "ServiceNow/VideoCUA"
_TREE = f"https://huggingface.co/api/datasets/{REPO}/tree/main/raw_data"
_FILE = f"https://huggingface.co/datasets/{REPO}/resolve/main/raw_data/{{name}}"


def safe_name(app: str) -> str:
    """Folder name for an app: 'Code::Blocks' is not a legal Windows path."""
    return app.replace(":", "_")


def remote_apps() -> dict[str, int]:
    """App name -> zip size in bytes, as listed on Hugging Face."""
    with urllib.request.urlopen(_TREE, timeout=60) as r:
        entries = json.load(r)
    apps: dict[str, int] = {}
    for e in entries:
        name = e["path"].rsplit("/", 1)[-1]
        if name.endswith(".zip"):
            apps[name[:-4]] = (e.get("lfs") or {}).get("size") or e.get("size", 0)
    return apps


def fetch(app: str, expected_size: int | None) -> Path:
    ZIPS.mkdir(parents=True, exist_ok=True)
    dest = ZIPS / f"{safe_name(app)}.zip"
    if dest.exists() and (expected_size is None or dest.stat().st_size == expected_size):
        return dest

    url = _FILE.format(name=urllib.parse.quote(f"{app}.zip"))
    part = dest.with_name(dest.name + ".part")
    log.info(f"downloading {app} ({(expected_size or 0) / 1e6:.0f} MB)")
    with urllib.request.urlopen(url, timeout=120) as r, open(part, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    if expected_size is not None and part.stat().st_size != expected_size:
        raise RuntimeError(
            f"{app}: got {part.stat().st_size} bytes, Hugging Face lists {expected_size}"
        )
    part.replace(dest)
    return dest


def unpack(app: str, zip_path: Path) -> Path:
    out = VIDEOS / safe_name(app)
    done = out / ".unpacked"
    if done.exists():
        return out
    root = out.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not (out / name).resolve().is_relative_to(root):
                raise RuntimeError(f"{zip_path.name} contains an unsafe path: {name}")
        zf.extractall(out)
    done.write_text(zip_path.name)
    return out


def download(apps: list[str]) -> None:
    available = remote_apps()
    unknown = [a for a in apps if a not in available]
    if unknown:
        raise SystemExit(
            f"not on Hugging Face: {', '.join(unknown)}  (run `python -m v2k apps` for the list)"
        )
    for app in apps:
        out = unpack(app, fetch(app, available[app]))
        n = sum(1 for _ in out.rglob("action_log.json"))
        log.info(f"{app}: {n} tasks in {out}")
