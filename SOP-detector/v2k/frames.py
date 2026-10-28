"""Stage 1: turn sampled frames into vectors once, and keep them on disk.

Frames are taken exactly the way the backend takes them (VideoProcessor, 640x480):
  keyframes - the frame at every action timestamp, grouped into segments by
              VideoProcessor.extract_segments. These are what the backend pools
              into its 150-dim segment vector.
  grid      - one frame per second (VideoProcessor.extract_frames), kept for
              frame-level models the team may want later.

For every frame the backend's own extractors run, and both their raw output
(OCR text and boxes, UI detections) and their vectors are stored. OCR is most
of the cost, so a new pooling rule or a refitted TF-IDF vocabulary must never
require OCR to run again.

Two additions for later use, neither of which the backend computes:
  native OCR - keyframes OCR'd at the recording's own resolution. The backend
               OCRs its 640x480 copy, where 1920-wide screen text is squeezed
               to a third of its width and comes back as gibberish.
  cnn        - a generic ImageNet ResNet-18 embedding (512-d) per frame: a
               learned way to turn a frame into a vector, independent of the
               team's hand-built one.
"""
from __future__ import annotations

import gc
import json
import logging
import os
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from v2k.env import BACKEND_SNAPSHOT, FRAME_SCHEMA, WEIGHTS, backend_commit, frame_cache_dir

log = logging.getLogger("v2k.frames")

KEYFRAME = 1  # pooled into a segment vector by the backend
GRID = 2      # on the 1-fps grid
CNN_DIM = 512
_YOLO_URL = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt"


def yolo_weights() -> Path:
    """The backend's yolov8n.pt, kept here instead of wherever the cwd happens to be."""
    path = WEIGHTS / "yolov8n.pt"
    if not path.exists():
        WEIGHTS.mkdir(parents=True, exist_ok=True)
        part = path.with_name(path.name + ".part")
        urllib.request.urlretrieve(_YOLO_URL, part)
        part.replace(path)
    return path


def action_dicts(task) -> list[dict]:
    # The dicts FeatureAssembler.extract_task_features hands to extract_segments.
    return [
        {
            "action_type": a.action_type,
            "timestamp": a.timestamp,
            "action_params": a.params,
            "t_end": a.t_end,
            "groundcua_id": a.groundcua_id,
        }
        for a in task.actions
    ]


class FrameEmbedder:
    """ImageNet ResNet-18 with its classifier head removed: frame -> 512-d."""

    def __init__(self, batch_size: int = 32):
        import torch
        import torchvision

        weights = torchvision.models.ResNet18_Weights.IMAGENET1K_V1
        model = torchvision.models.resnet18(weights=weights)
        model.fc = torch.nn.Identity()
        self._model = model.eval()
        self._mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
        self._std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
        self._batch = batch_size

    def embed(self, images: list[np.ndarray]) -> np.ndarray:
        import cv2
        import torch

        out = np.zeros((len(images), CNN_DIM), dtype=np.float32)
        for i in range(0, len(images), self._batch):
            chunk = images[i:i + self._batch]
            rgb = [
                cv2.cvtColor(cv2.resize(im, (224, 224), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
                for im in chunk
            ]
            x = torch.from_numpy(np.stack(rgb)).permute(0, 3, 1, 2).float() / 255.0
            with torch.no_grad():
                out[i:i + len(chunk)] = self._model((x - self._mean) / self._std).numpy()
        return out


class Extractors:
    """The backend's per-frame extractors, loaded once per process.

    The backend quietly returns empty results when easyocr or ultralytics is
    missing. A cache built that way would be all zeros, so refuse instead.
    """

    def __init__(self, with_cnn: bool = True):
        from app.pipeline.ocr_extractor import OCRExtractor
        from app.pipeline.ui_detector import UIDetector
        from app.pipeline.visual_features import VisualFeatureExtractor

        self.ocr = OCRExtractor()
        self.ui = UIDetector(model_name=str(yolo_weights()))
        self.visual = VisualFeatureExtractor()
        if self.ocr._get_reader() is None:
            raise RuntimeError("easyocr could not be loaded; OCR features would all be zero")
        if self.ui._get_model() is None:
            raise RuntimeError("YOLO could not be loaded; UI features would all be zero")
        self.cnn = FrameEmbedder() if with_cnn else None


def _native_frames(video_path: Path, keys: list[tuple]) -> list[np.ndarray | None]:
    """Frames at full resolution for the given row keys, seeked like the backend seeks."""
    import cv2

    frames: list[np.ndarray | None] = []
    cap = cv2.VideoCapture(str(video_path))
    try:
        for kind, value in keys:
            if kind == "t":
                cap.set(cv2.CAP_PROP_POS_MSEC, value * 1000)
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, value)
            ok, frame = cap.read()
            frames.append(frame if ok else None)
    finally:
        cap.release()
    return frames


def extract_video(
    video_path: Path, actions: list[dict], ex: Extractors, grid: bool, grid_ocr: bool,
    native_ocr: bool = True, parity_ocr: bool = True,
) -> tuple[dict[str, np.ndarray], dict]:
    """Run the backend's extractors over one recording.

    Returns (arrays, record). The arrays hold one row per distinct frame; the
    record keeps the OCR text, the UI detections and the segment structure,
    whose keyframe lists point into those rows.
    """
    from app.pipeline.video_processor import VideoProcessor

    vp = VideoProcessor()
    meta = vp.get_metadata(video_path)
    segments = vp.extract_segments(video_path, actions)
    grid_frames = vp.extract_frames(video_path) if grid else []

    images: list[np.ndarray] = []
    timestamps: list[float] = []
    indices: list[int] = []
    flags: list[int] = []
    rows: dict[tuple, int] = {}

    def add(frame, flag: int, key: tuple) -> int:
        row = rows.get(key)
        if row is None:
            row = rows[key] = len(images)
            images.append(frame.image)
            timestamps.append(frame.timestamp)
            indices.append(frame.frame_index)
            flags.append(0)
        flags[row] |= flag
        return row

    # With actions, a keyframe is seeked to each action timestamp. A repeated
    # timestamp (MOVE_TO then CLICK) is the same image, so it is run once but
    # referenced twice, and the backend's mean still counts it twice. Without
    # actions the one segment's keyframes are the 1-fps grid itself.
    seg_records = []
    for seg in segments:
        refs = []
        for kf in seg.keyframes:
            key = ("t", round(kf.timestamp, 6)) if actions else ("i", kf.frame_index)
            refs.append(add(kf, KEYFRAME, key))
        seg_records.append({
            "index": seg.segment_index,
            "start": seg.start_time,
            "end": seg.end_time,
            "keyframes": refs,
            "actions": seg.actions,
        })
    for frame in grid_frames:
        add(frame, GRID, ("i", frame.frame_index))

    n = len(images)
    ui = np.zeros((n, 30), dtype=np.float32)
    visual = np.zeros((n, 40), dtype=np.float32)
    ocr_conf = np.zeros(n, dtype=np.float32)
    ocr_ran = np.zeros(n, dtype=bool)
    native_conf = np.zeros(n, dtype=np.float32)
    frame_records = []
    spent = {"ocr": 0.0, "ocr_native": 0.0, "ui": 0.0, "visual": 0.0, "cnn": 0.0}
    key_of_row = {row: key for key, row in rows.items()}

    for r, image in enumerate(images):
        h, w = image.shape[:2]
        rec: dict = {"ocr_text": None, "ocr_regions": None}
        if parity_ocr and (flags[r] & KEYFRAME or grid_ocr):
            t = time.perf_counter()
            result = ex.ocr.extract_with_fallback(image)
            spent["ocr"] += time.perf_counter() - t
            rec["ocr_text"] = result.full_text
            rec["ocr_regions"] = [[g.text, *g.bbox, round(g.confidence, 4)] for g in result.regions]
            ocr_conf[r] = result.mean_confidence
            ocr_ran[r] = True

        t = time.perf_counter()
        detection = ex.ui.detect(image)
        ui[r] = ex.ui.detection_to_features(detection, frame_area=h * w)
        spent["ui"] += time.perf_counter() - t
        rec["ui_elements"] = [[e.class_name, *e.bbox, round(e.confidence, 4)] for e in detection.elements]

        t = time.perf_counter()
        visual[r] = ex.visual.extract(image)
        spent["visual"] += time.perf_counter() - t
        frame_records.append(rec)

    if native_ocr:
        # One full-resolution frame in memory at a time; keyframes only.
        wanted = [r for r in range(n) if flags[r] & KEYFRAME]
        for chunk_start in range(0, len(wanted), 16):
            chunk = wanted[chunk_start:chunk_start + 16]
            for r, frame in zip(chunk, _native_frames(video_path, [key_of_row[r] for r in chunk])):
                if frame is None:
                    continue
                t = time.perf_counter()
                result = ex.ocr.extract_text(frame)
                spent["ocr_native"] += time.perf_counter() - t
                frame_records[r]["ocr_native_text"] = result.full_text
                frame_records[r]["ocr_native_regions"] = [
                    [g.text, *g.bbox, round(g.confidence, 4)] for g in result.regions
                ]
                native_conf[r] = result.mean_confidence

    arrays = {
        "timestamp": np.asarray(timestamps, dtype=np.float64),
        "frame_index": np.asarray(indices, dtype=np.int64),
        "flags": np.asarray(flags, dtype=np.uint8),
        "ocr_ran": ocr_ran,
        "ocr_conf": ocr_conf,
        "ocr_native_conf": native_conf,
        "ui": ui,
        "visual": visual,
    }
    if ex.cnn is not None:
        t = time.perf_counter()
        arrays["cnn"] = ex.cnn.embed(images) if images else np.zeros((0, CNN_DIM), np.float32)
        spent["cnn"] += time.perf_counter() - t
    images.clear()

    record = {
        "schema": FRAME_SCHEMA,
        "backend_snapshot": BACKEND_SNAPSHOT,
        "backend_commit": backend_commit(),
        "video": {k: meta[k] for k in ("fps", "total_frames", "width", "height", "duration_seconds")},
        "n_frames": n,
        "n_keyframe_rows": sum(1 for f in flags if f & KEYFRAME),
        "has_cnn": ex.cnn is not None,
        "native_ocr": native_ocr,
        "parity_ocr": parity_ocr,
        "grid": grid,
        "grid_ocr": grid_ocr,
        "seconds_by_extractor": {k: round(v, 2) for k, v in spent.items()},
        "frames": frame_records,
        "segments": seg_records,
    }
    return arrays, record


def cache_paths(app: str, task_id: int) -> tuple[Path, Path]:
    folder = frame_cache_dir() / app
    return folder / f"{task_id}.npz", folder / f"{task_id}.json"


def is_cached(app: str, task_id: int) -> bool:
    return all(p.exists() for p in cache_paths(app, task_id))


_EX: Extractors | None = None


def _init_worker(threads: int, with_cnn: bool) -> None:
    import torch

    torch.set_num_threads(threads)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    # At 640x480 almost every frame is low-confidence, so the backend tries its
    # Tesseract fallback and warns that pytesseract is missing - once per frame.
    # The easyocr result is kept either way, exactly as in the live backend.
    logging.getLogger("app.pipeline.ocr_extractor").setLevel(logging.ERROR)
    global _EX
    _EX = Extractors(with_cnn=with_cnn)


def extract_task(app: str, task, grid: bool, grid_ocr: bool, native_ocr: bool,
                 parity_ocr: bool = True) -> dict:
    npz_path, json_path = cache_paths(app, task.task_id)
    if is_cached(app, task.task_id):
        return {"task_id": task.task_id, "skipped": True}

    start = time.time()
    arrays, record = extract_video(task.video_path, action_dicts(task), _EX, grid, grid_ocr,
                                   native_ocr, parity_ocr)
    record.update(
        task_id=task.task_id,
        app=app,
        platform=task.platform,
        instruction=task.instruction,
        keyword_label=task.activity_label,
        seconds=round(time.time() - start, 1),
        created=time.strftime("%Y-%m-%d %H:%M:%S"),
    )

    npz_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_npz = npz_path.with_name(f"{task.task_id}.tmp.npz")
    tmp_json = json_path.with_name(f"{task.task_id}.json.tmp")
    np.savez_compressed(tmp_npz, **arrays)
    tmp_json.write_text(json.dumps(record), encoding="utf-8")
    os.replace(tmp_npz, npz_path)
    os.replace(tmp_json, json_path)  # the .json appearing marks the task done
    summary = {
        "task_id": task.task_id,
        "frames": record["n_frames"],
        "keyframes": record["n_keyframe_rows"],
        "seconds": record["seconds"],
        "video_seconds": record["video"]["duration_seconds"],
    }
    del arrays, record
    gc.collect()
    return summary


def run(pairs: list[tuple[str, object]], workers: int, threads: int,
        with_cnn: bool, grid: bool, grid_ocr: bool, native_ocr: bool,
        parity_ocr: bool = True) -> None:
    from v2k.tasks import usable_video

    todo = []
    skipped = []
    for app, task in pairs:
        if is_cached(app, task.task_id):
            continue
        why = usable_video(task)
        if why:
            skipped.append(f"{app}/{task.task_id}: {why}")
        else:
            todo.append((app, task))
    log.info(f"{len(pairs)} tasks with video, {len(pairs) - len(todo) - len(skipped)} already cached, "
             f"{len(skipped)} unusable, {len(todo)} to extract")
    if skipped:
        log.warning(f"skipping {len(skipped)} unreadable recording(s), e.g. {skipped[0]}")
    log.info(f"cache: {frame_cache_dir()}")
    if not todo:
        return

    # Load everything once in this process first, so parallel workers do not
    # race to download the OCR, YOLO and ResNet weights.
    yolo_weights()
    _init_worker(threads, with_cnn)
    if workers > 1:
        # The coordinator does no extraction; holding the models would cost
        # several GB for nothing.
        global _EX
        _EX = None
        gc.collect()

    started = time.time()
    done_video = 0.0
    failures: list[str] = []

    def report(i: int, app: str, tid: int, info: dict) -> None:
        nonlocal done_video
        done_video += info["video_seconds"]
        elapsed = time.time() - started
        rate = elapsed / max(i, 1)
        eta = rate * (len(todo) - i)
        log.info(
            f"[{i}/{len(todo)}] {app}/{tid}: {info['frames']} frames "
            f"({info['keyframes']} keyframes) in {info['seconds']:.0f}s | "
            f"elapsed {elapsed / 60:.1f} min, eta ~{eta / 60:.0f} min"
        )

    if workers <= 1:
        for i, (app, task) in enumerate(todo, 1):
            try:
                report(i, app, task.task_id,
                       extract_task(app, task, grid, grid_ocr, native_ocr, parity_ocr))
            except Exception as e:
                failures.append(f"{app}/{task.task_id}: {type(e).__name__}: {e}")
                log.error(failures[-1])
    else:
        # No max_tasks_per_child here. easyocr, YOLO and torch do hold on to
        # allocations - a worker grew past 5 GB - but on Python 3.14 with the
        # spawn start method and an initializer, the pool stops handing out work
        # once each worker has taken max_tasks_per_child tasks: it hung at
        # exactly workers x 12 both times it was tried (6x12=72, 3x12=36).
        # Memory is reclaimed by restarting this whole command instead, which
        # run_scheduled_v3.sh does on a timer.
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker,
                                 initargs=(threads, with_cnn)) as pool:
            futures = {pool.submit(extract_task, app, t, grid, grid_ocr, native_ocr, parity_ocr): (app, t)
                       for app, t in todo}
            for i, fut in enumerate(as_completed(futures), 1):
                app, task = futures[fut]
                try:
                    report(i, app, task.task_id, fut.result())
                except Exception as e:
                    failures.append(f"{app}/{task.task_id}: {type(e).__name__}: {e}")
                    log.error(failures[-1])

    log.info(f"done in {(time.time() - started) / 60:.1f} min for {done_video / 60:.1f} min of video")
    if failures:
        log.warning(f"{len(failures)} task(s) failed and were not cached:")
        for f in failures:
            log.warning(f"  {f}")
