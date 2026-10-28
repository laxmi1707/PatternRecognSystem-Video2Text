"""Download trained model artifacts from S3 into the local model directory.

S3 is the preferred source; the local model directory is the fallback. Any S3
failure (not configured, boto3 missing, no credentials, network, checksum
mismatch) leaves the local files untouched so the service still starts with
whatever was baked into the image or trained locally.

Layout in the bucket:  s3://<bucket>/<prefix>/<model_name>.pkl
Optional checksum:     s3://<bucket>/<prefix>/<model_name>.sha256  (hex SHA-256)
"""
from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# .json: label_names.json maps each model's class index to its activity name
MODEL_SUFFIXES = (".pkl", ".json")
CHECKSUM_SUFFIX = ".sha256"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_client(region: str | None) -> Any:
    import boto3

    return boto3.client("s3", region_name=region)


def _list_keys(client: Any, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


def sync_models_from_s3(
    bucket: str | None,
    prefix: str,
    local_dir: str | Path,
    region: str | None = None,
    require_checksum: bool = False,
    client: Any = None,
) -> list[str]:
    """Download model artifacts from S3 into ``local_dir``.

    Returns the names of the model files that were downloaded. An empty list
    means the local directory is used as-is.
    """
    if not bucket:
        logger.info("MODEL_S3_BUCKET not set; using local models in %s", local_dir)
        return []

    local = Path(local_dir)
    prefix = prefix.strip("/") + "/" if prefix.strip("/") else ""

    try:
        if client is None:
            client = _make_client(region)
        keys = _list_keys(client, bucket, prefix)
    except ImportError:
        logger.warning("boto3 not installed; falling back to local models in %s", local)
        return []
    except Exception as e:  # noqa: BLE001 - any S3 failure must fall back to local models
        logger.warning("Cannot list s3://%s/%s (%s); falling back to local models in %s", bucket, prefix, e, local)
        return []

    # Only files directly under the prefix; sub-prefixes hold other versions.
    names = {k[len(prefix):] for k in keys if "/" not in k[len(prefix):]}
    model_names = sorted(n for n in names if n.endswith(MODEL_SUFFIXES))
    if not model_names:
        logger.warning("No model artifacts under s3://%s/%s; falling back to local models in %s", bucket, prefix, local)
        return []

    local.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] = []
    for name in model_names:
        checksum_name = Path(name).stem + CHECKSUM_SUFFIX
        has_checksum = checksum_name in names
        if require_checksum and not has_checksum:
            logger.warning("Skipping %s: no %s in S3 and checksum is required; keeping local copy", name, checksum_name)
            continue

        # Download to a temp file first so a failed or corrupt download never
        # clobbers the local fallback.
        fd, tmp_name = tempfile.mkstemp(dir=local, suffix=".part")
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            client.download_file(bucket, prefix + name, str(tmp))
            if has_checksum:
                body = client.get_object(Bucket=bucket, Key=prefix + checksum_name)["Body"].read()
                expected = body.decode().split()[0].strip().lower()
                actual = _sha256(tmp)
                if actual != expected:
                    logger.warning(
                        "Checksum mismatch for %s (expected %s…, got %s…); keeping local copy",
                        name, expected[:12], actual[:12],
                    )
                    continue
            os.replace(tmp, local / name)
            downloaded.append(name)
        except Exception as e:  # noqa: BLE001 - keep the local copy on any download failure
            logger.warning("Failed to download s3://%s/%s%s (%s); keeping local copy", bucket, prefix, name, e)
        finally:
            tmp.unlink(missing_ok=True)

    logger.info("Downloaded %d/%d model artifacts from s3://%s/%s into %s",
                len(downloaded), len(model_names), bucket, prefix, local)
    return downloaded
