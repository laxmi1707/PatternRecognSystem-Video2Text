from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.dataset import generate_synthetic_dataset
from app.models.job import AnalysisJob
from app.models.result import ClassificationResult
from app.services.job_service import update_job_status

logger = logging.getLogger(__name__)

# Called from the extraction thread after each segment with (segments done, total).
ProgressFn = Callable[[int, int], None]

# Bump when feature extraction changes, so stale cached features are not reused.
FEATURE_CACHE_VERSION = "2"  # 2: full-resolution OCR in lines, changed-pixel duplicate check


def _feature_cache_path(video_path: Path, action_log_path: Path | None) -> Path:
    """Cache file for this video's features: same bytes, log and backend give the same features."""
    from app.config import settings
    from app.pipeline.feature_assembler import FEATURE_BACKEND

    h = hashlib.sha256(f"v{FEATURE_CACHE_VERSION}|{FEATURE_BACKEND}|".encode())
    with open(video_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    if action_log_path and action_log_path.exists():
        h.update(b"|log|" + action_log_path.read_bytes())
    return Path(settings.upload_dir) / "feature_cache" / f"{h.hexdigest()}.npz"


def _load_cached_features(path: Path) -> tuple[np.ndarray, list[dict]] | None:
    try:
        with np.load(path, allow_pickle=False) as data:
            return data["X"], json.loads(str(data["segments"]))
    except FileNotFoundError:
        return None
    except Exception as e:  # unreadable or old-format entry: extract again
        logger.warning(f"Ignoring feature cache {path.name}: {e}")
        return None


def _save_cached_features(path: Path, X: np.ndarray, segments: list[dict]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + ".tmp.npz")
        np.savez_compressed(tmp, X=X, segments=np.array(json.dumps(segments)))
        os.replace(tmp, path)
    except Exception as e:  # the cache is an optimisation; never fail the job over it
        logger.warning(f"Could not write feature cache {path.name}: {e}")


def _extract_features(
    video_path: Path | None,
    action_log_path: Path | None,
    on_progress: ProgressFn | None = None,
) -> tuple[np.ndarray, list[dict], bool]:
    """Returns (features, segments, used_yolo)."""
    from app.pipeline.feature_assembler import TOTAL_FEATURES

    if video_path and video_path.exists():
        from app.pipeline.temporal_encoder import TemporalEncoder
        try:
            cache_path = _feature_cache_path(video_path, action_log_path)
            cached = _load_cached_features(cache_path)
            if cached is not None:
                X, segments = cached
                logger.info(f"Feature cache hit for {video_path.name}: {X.shape[0]} segments")
                if on_progress:
                    on_progress(len(segments), len(segments))
                return X, segments, True

            X, segments = _extract_real_features(video_path, action_log_path, on_progress)
            if X.shape[0] > 1:
                encoder = TemporalEncoder(window_size=1)
                X = encoder.encode_sequence(X)
            logger.info(
                f"Real pipeline: {video_path.name} → {X.shape[0]} segments, "
                f"{X.shape[1]} features"
            )
            _save_cached_features(cache_path, X, segments)
            return X, segments, True
        except Exception as e:
            print(f"[OCR-DEBUG] Real feature extraction FAILED: {e}", flush=True)
            logger.warning(f"Real feature extraction failed, falling back to synthetic: {e}")
            X_full, _ = generate_synthetic_dataset(n_samples=100, n_features=TOTAL_FEATURES)
            duration = 50.0
            n_segments = 10
            segments = [
                {"start_time": i * (duration / n_segments), "end_time": (i + 1) * (duration / n_segments)}
                for i in range(n_segments)
            ]
            return X_full[:n_segments], segments, False

    logger.info("No video file provided, using synthetic features")
    X_full, _ = generate_synthetic_dataset(n_samples=100, n_features=TOTAL_FEATURES)
    segments = [{"start_time": i * 5.0, "end_time": (i + 1) * 5.0} for i in range(10)]
    return X_full[:10], segments, False


def _get_available_models() -> list[str]:
    """Return only models that have a .pkl file in the configured model dir."""
    from pathlib import Path
    from app.ml.config import MLConfig
    model_dir = Path(MLConfig().model_dir)
    if not model_dir.exists():
        return []
    order = ["svm", "knn", "random_forest", "cnn1d", "lstm", "stacking"]
    available = {p.stem for p in model_dir.glob("*.pkl")}
    # Return in tier order, only those present
    ordered = [m for m in order if m in available]
    # Append any extras not in the fixed order
    ordered += sorted(available - set(order))
    return ordered

# Feature extraction and classification are CPU-bound and synchronous, so they run in a
# worker thread (asyncio.to_thread) to keep the event loop free for /health and job-status
# polling. ml_service is a shared singleton that may train a missing model on first use,
# so classify calls from concurrent jobs are serialized.
_MODEL_LOCK = threading.Lock()


def _classify_locked(X: np.ndarray, model_name: str) -> dict:
    from app.services.ml_service import ml_service

    with _MODEL_LOCK:
        return ml_service.classify(X, model_name=model_name)


async def _classify_all_models(
    X: np.ndarray,
    db=None, job_id: int | None = None,
) -> dict[str, list[dict]]:
    all_results: dict[str, list[dict]] = {}
    models = _get_available_models()
    total = len(models)
    for idx, model_name in enumerate(models):
        if db and job_id:
            pct = 70 + int((idx / total) * 25)
            await update_job_status(db, job_id, "processing", pct, f"classifying with {model_name} ({idx+1}/{total})")
        logger.info(f"[classify] starting {model_name} ({idx+1}/{total})")
        _t0 = time.perf_counter()
        try:
            result = await asyncio.to_thread(_classify_locked, X, model_name)
            all_results[model_name] = result["results"]
            _elapsed = time.perf_counter() - _t0
            logger.info(f"[classify] done {model_name} ({idx+1}/{total}) — {len(result['results'])} segments in {_elapsed:.1f}s")
        except Exception as e:
            _elapsed = time.perf_counter() - _t0
            logger.warning(f"[classify] {model_name} failed after {_elapsed:.1f}s: {e}")

    return all_results


async def run_classification_job(
    db: AsyncSession,
    job: AnalysisJob,
    video_path: Path | None = None,
    action_log_path: Path | None = None,
) -> list[ClassificationResult]:
    await update_job_status(db, job.id, "processing", 5.0, "preparing video analysis")

    try:
        await update_job_status(db, job.id, "processing", 10.0, "extracting video segments and keyframes")

        # The extraction thread records how many segments are done; the heartbeat reports
        # that as 10→59% so the bar follows the real work instead of stopping at a guess.
        seg_progress = {"done": 0, "total": 0}

        def _on_segment(done: int, total: int) -> None:
            seg_progress["done"], seg_progress["total"] = done, total

        async def _feature_extraction_heartbeat(stop_event: asyncio.Event) -> None:
            reported = (0, 0)
            while not stop_event.is_set():
                await asyncio.sleep(2)
                done, total = seg_progress["done"], seg_progress["total"]
                if stop_event.is_set() or total == 0 or (done, total) == reported:
                    continue
                reported = (done, total)
                await update_job_status(
                    db, job.id, "processing", 10.0 + 49.0 * done / total,
                    f"reading screen text and features: segment {done} of {total}",
                )

        stop_heartbeat = asyncio.Event()
        heartbeat_task = asyncio.create_task(_feature_extraction_heartbeat(stop_heartbeat))

        try:
            X, segments, used_yolo = await asyncio.to_thread(
                _extract_features, video_path, action_log_path, _on_segment
            )
        finally:
            stop_heartbeat.set()
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        n_segments = X.shape[0]
        n_features = X.shape[1]

        await update_job_status(
            db, job.id, "processing", 60.0,
            f"extracted {n_segments} segments with {n_features}-dim features"
        )

        await update_job_status(db, job.id, "processing", 65.0, "loading classification models")

        all_model_results = await _classify_all_models(
            X, db=db, job_id=job.id
        )

        await update_job_status(db, job.id, "processing", 96.0, "saving results to database")

        results: list[ClassificationResult] = []
        for model_name, predictions in all_model_results.items():
            for i, pred in enumerate(predictions):
                seg = segments[i] if i < len(segments) else {"start_time": i * 5.0, "end_time": (i + 1) * 5.0}
                probs = dict(pred["probabilities"])
                ocr = seg.get("ocr_text", "")
                if ocr:
                    probs["_ocr"] = ocr
                cr = ClassificationResult(
                    job_id=job.id,
                    segment_index=i,
                    start_time=seg["start_time"],
                    end_time=seg["end_time"],
                    predicted_label=pred["label"],
                    confidence=pred["confidence"],
                    probabilities=probs,
                    model_name=model_name,
                    latency_ms=pred["latency_ms"],
                )
                results.append(cr)

        db.add_all(results)
        await update_job_status(db, job.id, "completed", 100.0, "analysis complete")

        return results

    except Exception as e:
        await update_job_status(db, job.id, "failed", error_message=str(e))
        raise


def _extract_real_features(
    video_path: Path, action_log_path: Path | None = None, on_progress: ProgressFn | None = None
) -> tuple[np.ndarray, list[dict]]:
    from app.pipeline.feature_assembler import get_default_assembler
    from app.pipeline.video_processor import VideoProcessor

    actions: list[dict] = []
    if action_log_path and action_log_path.exists():
        with open(action_log_path) as f:
            data = json.load(f)
        actions = data.get("action_log", [])

    assembler = get_default_assembler()
    processor = VideoProcessor()
    segments = processor.extract_segments(video_path, actions)
    if on_progress:
        on_progress(0, len(segments))

    features_list = []
    segment_info = []
    for i, seg in enumerate(segments):
        feat = assembler.extract_segment_features(seg)
        features_list.append(feat)
        ocr = getattr(assembler, "_last_ocr_text", "")
        print(f"[OCR-DEBUG] Segment {seg.segment_index} [{seg.start_time:.1f}-{seg.end_time:.1f}s] "
              f"keyframes={len(seg.keyframes)} ocr_len={len(ocr)} ocr={repr(ocr[:120])}", flush=True)
        segment_info.append({
            "start_time": seg.start_time,
            "end_time": seg.end_time,
            "ocr_text": ocr,
        })
        if on_progress:
            on_progress(i + 1, len(segments))

    ocr_extractor = getattr(assembler, "_ocr", None)
    if ocr_extractor is not None:
        logger.info(
            f"OCR read {ocr_extractor.frames_read} keyframes, "
            f"reused text for {ocr_extractor.frames_reused} unchanged ones"
        )
    X = np.array(features_list)
    return X, segment_info
