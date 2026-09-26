"""Reproduce the label.txt decoding failure in discover_tasks.

Run it against the VideoCUA dataset root:

    python repro_label_encoding_v1.py "path/to/Video CUA collect"

It reads every label.txt the way app/ml/dataset_loader.py does, counts the ones
that raise, and shows what the same file contains when UTF-8 is requested.
Nothing is written or changed.
"""
from __future__ import annotations

import locale
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(f"usage: python {Path(__file__).name} <dataset root>")
    root = Path(sys.argv[1])
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")

    print(f"python default encoding on this machine: {locale.getpreferredencoding(False)}")
    print(f"dataset root: {root}\n")

    total, failed = 0, []
    for label_file in root.glob("*/*/label.txt"):
        total += 1
        try:
            # exactly what dataset_loader._load_task does today
            label_file.read_text()
        except UnicodeDecodeError as exc:
            failed.append((label_file, exc))

    print(f"label.txt files found     : {total}")
    print(f"raising UnicodeDecodeError: {len(failed)}\n")

    if not failed:
        print("No failures here - this machine's default encoding already reads them.")
        print("It still breaks wherever the default is not UTF-8 (Windows cp1252, cp932, ...).")
        return

    for label_file, exc in failed[:5]:
        app, task = label_file.parent.parent.name, label_file.parent.name
        print(f"  {app}/{task}")
        print(f"    {type(exc).__name__}: {exc}")
        text = label_file.read_text(encoding="utf-8").strip().replace("\n", " ")
        print(f"    with encoding='utf-8': {text[:90]!r}\n")

    if len(failed) > 5:
        print(f"  ... and {len(failed) - 5} more\n")

    print("The offending bytes are UTF-8 curly quotes in instructions such as")
    print('  Open “Plugins” from 7-Zip File Manager')
    print("cp1252 has no mapping at 0x9d, so decoding raises.\n")
    print("Fix, in app/ml/dataset_loader.py (_load_task):")
    print('  instruction = label_file.read_text(encoding="utf-8").strip() or instruction')


if __name__ == "__main__":
    main()
