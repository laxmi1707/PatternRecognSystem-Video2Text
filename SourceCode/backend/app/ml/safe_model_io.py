"""Safe model serialization with joblib and SHA-256 checksum verification."""
import hashlib
from pathlib import Path

import joblib


class ModelIntegrityError(Exception):
    pass


def _checksum_path(model_path: str) -> Path:
    return Path(model_path).with_suffix(".sha256")


def _compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def save_model(model: object, path: str) -> None:
    joblib.dump(model, path, compress=3)
    digest = _compute_sha256(path)
    _checksum_path(path).write_text(digest)


def load_model(path: str) -> object:
    cksum_file = _checksum_path(path)
    if not cksum_file.exists():
        raise ModelIntegrityError(f"Checksum file missing for {path}")
    expected = cksum_file.read_text().strip()
    actual = _compute_sha256(path)
    if actual != expected:
        raise ModelIntegrityError(
            f"Checksum mismatch for {path}: expected {expected[:16]}…, got {actual[:16]}…"
        )
    return joblib.load(path)
