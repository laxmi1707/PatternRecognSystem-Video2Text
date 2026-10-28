"""Step B: load a saved bundle and classify a new recording.

The bundle carries the fitted FeatureBuilder (OCR TF-IDF vocabulary, scaler)
and the class list next to the model, so the new video goes through exactly
the transformation the training data went through - which is what the
backend's live path currently gets wrong (its OCR block is always zero).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from v2k.frames import Extractors, action_dicts, cache_paths, extract_video
from v2k.segments import build_table

log = logging.getLogger("v2k.predict")


def _load_actions(path: Path | None) -> list[dict]:
    if path is None:
        return []
    from app.ml.dataset_loader import TaskMetadata, _parse_action_log

    actions, *_ = _parse_action_log(path)
    stub = TaskMetadata(task_id=0, instruction="", platform="", video_path=None, actions=actions,
                        video_meta=None, activity_label="", workflow="")
    return action_dicts(stub)


def predict(bundle_path: Path, video: Path, actions_path: Path | None) -> list[dict]:
    import joblib

    bundle = joblib.load(bundle_path)
    log.info(f"{bundle['model_name']} on {bundle['feature_set']}, classes: {', '.join(bundle['classes'])}")

    ex = Extractors(with_cnn="cnn" in bundle["blocks"])
    arrays, record = extract_video(video, _load_actions(actions_path), ex, grid=False, grid_ocr=False,
                                   native_ocr="ocr_native" in bundle["blocks"],
                                   parity_ocr="ocr" in bundle["blocks"])
    record.update(task_id=0, app="(input)", platform="", instruction="", keyword_label="")
    table = build_table([(arrays, record)])

    return _rows(bundle, table)


def predict_cached(bundle_path: Path, app: str, task_id: int) -> list[dict]:
    """The same classification for a recording already in the frame cache.

    Nothing is decoded or read again, so labelling an SOP costs a second
    instead of the minutes a fresh extraction takes.
    """
    import json

    import joblib

    bundle = joblib.load(bundle_path)
    npz_path, json_path = cache_paths(app, task_id)
    if not json_path.exists():
        raise SystemExit(f"{app}/{task_id} is not in the frame cache")
    record = json.loads(json_path.read_text(encoding="utf-8"))
    with np.load(npz_path) as z:
        arrays = {k: z[k] for k in z.files}
    table = build_table([(arrays, record)])

    missing = [b for b in bundle["blocks"] if b not in table.available]
    if missing:
        raise SystemExit(
            f"{app}/{task_id} was cached without {', '.join(missing)}, which this bundle needs. "
            f"Re-extract that recording, or use a bundle trained on {', '.join(sorted(table.available))}."
        )
    return _rows(bundle, table)


def _rows(bundle: dict, table) -> list[dict]:
    X = bundle["builder"].transform(table, np.arange(len(table)))
    out = bundle["model"].predict(X)
    rows = []
    for i, k in enumerate(np.asarray(out.labels).astype(int)):
        probs = np.asarray(out.probabilities[i])
        rows.append({
            "segment": int(table.segment_index[i]),
            "start": round(float(table.start[i]), 1),
            "end": round(float(table.end[i]), 1),
            "label": bundle["classes"][k],
            "confidence": round(float(probs[k]), 3) if k < len(probs) else None,
        })
    return rows
