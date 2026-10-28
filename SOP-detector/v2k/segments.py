"""Stage 2: rebuild segment vectors from the frame cache.

Cached per-frame vectors are pooled the way FeatureAssembler.extract_segment_features
pools them (mean over a segment's keyframes, a repeated keyframe counted twice),
and the interaction block is computed by the backend's own code, so a model
trained here sees the numbers the backend computes live.

The two OCR blocks are the exception. Their TF-IDF vocabulary has to be fitted
on training data, so FeatureBuilder builds them per fold instead of storing them.
  ocr         - the backend's: text read from the 640x480 keyframe
  ocr_native  - the same TF-IDF on text read at the recording's own resolution
"""
from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from v2k.env import frame_cache_dir

log = logging.getLogger("v2k.segments")

BLOCK_DIMS = {"ocr": 50, "ocr_native": 50, "ui": 30, "visual": 40, "interaction": 30, "cnn": 512}
PRESETS = {
    # The backend's vector, in the backend's order (feature_assembler.MODALITY_MAP).
    "main150": ("ocr", "ui", "visual", "interaction"),
    # The same, with OCR read at full resolution - what fixing the resize would give.
    "native150": ("ocr_native", "ui", "visual", "interaction"),
}
_TEXT_BLOCKS = {"ocr": "text", "ocr_native": "text_native"}


def parse_feature_set(spec: str) -> tuple[str, ...]:
    """'main150', 'cnn', 'main150+cnn', 'visual+interaction', ... -> block names."""
    blocks: list[str] = []
    for part in spec.split("+"):
        expanded = PRESETS.get(part, (part,))
        for b in expanded:
            if b not in BLOCK_DIMS:
                known = ", ".join([*PRESETS, *BLOCK_DIMS])
                raise SystemExit(f"unknown feature block '{b}' in '{spec}' (known: {known})")
            if b not in blocks:
                blocks.append(b)
    return tuple(blocks)


@dataclass
class TaskInfo:
    task_id: int
    app: str
    platform: str
    instruction: str
    keyword_label: str
    keyframe_texts: list[str]         # every pooled keyframe's OCR text, repeats kept
    keyframe_texts_native: list[str]  # the same keyframes read at full resolution
    n_segments: int


@dataclass
class SegmentTable:
    task_id: np.ndarray        # (n,)
    segment_index: np.ndarray  # (n,)
    start: np.ndarray          # (n,) seconds
    end: np.ndarray            # (n,)
    text: list[str]            # a segment's combined OCR text, as OCRExtractor.extract_segment joins it
    text_native: list[str]     # the same, read at full resolution ("" when not cached)
    blocks: dict[str, np.ndarray]
    tasks: dict[int, TaskInfo]
    available: frozenset = frozenset(BLOCK_DIMS)  # blocks every cached task actually has

    def __len__(self) -> int:
        return len(self.task_id)


def _interaction_block(assembler, seg: dict) -> np.ndarray:
    from app.pipeline.feature_assembler import MODALITY_MAP
    from app.pipeline.video_processor import SegmentData

    # With no keyframes the assembler fills only the interaction block, using
    # exactly the ActionRecord conversion it applies in the live pipeline.
    stub = SegmentData(
        segment_index=seg["index"], start_time=seg["start"], end_time=seg["end"],
        keyframes=[], actions=seg["actions"],
    )
    s, e = MODALITY_MAP["interaction"]
    return assembler.extract_segment_features(stub)[s:e]


def _pool(values: np.ndarray, refs: list[int]) -> np.ndarray:
    if not refs:
        return np.zeros(values.shape[1], dtype=np.float32)
    return np.mean([values[r] for r in refs], axis=0).astype(np.float32)


def build_table(records: list[tuple[dict[str, np.ndarray], dict]]) -> SegmentTable:
    """records: (npz arrays, json record) per task, as frames.extract_video returns them."""
    from app.pipeline.feature_assembler import FeatureAssembler
    from app.pipeline.interaction_features import InteractionFeatureExtractor
    from app.pipeline.ocr_extractor import OCRExtractor
    from app.pipeline.ui_detector import UIDetector
    from app.pipeline.video_processor import VideoProcessor
    from app.pipeline.visual_features import VisualFeatureExtractor

    # Only the interaction extractor is exercised; nothing heavy gets loaded.
    assembler = FeatureAssembler(
        ocr=OCRExtractor(), ui=UIDetector(), visual=VisualFeatureExtractor(),
        interaction=InteractionFeatureExtractor(), video_processor=VideoProcessor(),
    )
    has_cnn = all(rec.get("has_cnn") for _, rec in records)
    # A pass that was skipped at extraction time must not look like empty text.
    available = set(BLOCK_DIMS)
    if not has_cnn:
        available.discard("cnn")
    if not all(rec.get("parity_ocr", True) for _, rec in records):
        available.discard("ocr")
    if not all(rec.get("native_ocr", False) for _, rec in records):
        available.discard("ocr_native")

    task_id, seg_index, start, end, text, text_native = [], [], [], [], [], []
    pooled: dict[str, list[np.ndarray]] = {b: [] for b in ("ui", "visual", "interaction")}
    if has_cnn:
        pooled["cnn"] = []
    tasks: dict[int, TaskInfo] = {}

    for arrays, rec in records:
        tid = int(rec["task_id"])
        frame_texts = [f["ocr_text"] for f in rec["frames"]]
        native_texts = [f.get("ocr_native_text") for f in rec["frames"]]
        keyframe_texts: list[str] = []
        keyframe_texts_native: list[str] = []
        for seg in rec["segments"]:
            refs = seg["keyframes"]
            parts = [frame_texts[r] for r in refs if frame_texts[r]]
            parts_native = [native_texts[r] for r in refs if native_texts[r]]
            keyframe_texts.extend(parts)
            keyframe_texts_native.extend(parts_native)
            text_native.append(" ".join(parts_native))
            task_id.append(tid)
            seg_index.append(seg["index"])
            start.append(seg["start"])
            end.append(seg["end"])
            text.append(" ".join(parts))
            pooled["ui"].append(_pool(arrays["ui"], refs))
            pooled["visual"].append(_pool(arrays["visual"], refs))
            pooled["interaction"].append(_interaction_block(assembler, seg))
            if has_cnn:
                pooled["cnn"].append(_pool(arrays["cnn"], refs))
        tasks[tid] = TaskInfo(
            task_id=tid,
            app=rec.get("app", ""),
            platform=rec.get("platform", ""),
            instruction=rec.get("instruction", ""),
            keyword_label=rec.get("keyword_label", ""),
            keyframe_texts=keyframe_texts,
            keyframe_texts_native=keyframe_texts_native,
            n_segments=len(rec["segments"]),
        )

    blocks = {
        b: (np.vstack(v).astype(np.float32) if v else np.zeros((0, BLOCK_DIMS[b]), np.float32))
        for b, v in pooled.items()
    }
    return SegmentTable(
        task_id=np.asarray(task_id, dtype=np.int64),
        segment_index=np.asarray(seg_index, dtype=np.int64),
        start=np.asarray(start, dtype=np.float64),
        end=np.asarray(end, dtype=np.float64),
        text=text,
        text_native=text_native,
        blocks=blocks,
        tasks=tasks,
        available=frozenset(available),
    )


def pool_to_tasks(table: SegmentTable) -> SegmentTable:
    """One row per recording: the mean of its segments' vectors.

    The labels are per recording, so a segment-level row asks a model to call a
    password prompt `run_command` purely because the recording it sits in was
    one. Pooling asks the question the labels can actually answer.

    The backend does not do this - extract_task_features also emits one row per
    segment and copies the task's label onto each - so this is a separate
    setting, not a change to the parity path. The price is far fewer rows and
    no timeline, which is why the SOP keeps working at segment level.
    """
    order = sorted(table.tasks)
    pos: dict[int, list[int]] = {t: [] for t in order}
    for i, t in enumerate(table.task_id):
        pos[int(t)].append(i)

    blocks = {b: np.vstack([v[pos[t]].mean(axis=0) for t in order]).astype(np.float32)
              for b, v in table.blocks.items()}
    return SegmentTable(
        task_id=np.asarray(order, dtype=np.int64),
        segment_index=np.zeros(len(order), dtype=np.int64),
        start=np.asarray([table.start[pos[t]].min() for t in order], dtype=np.float64),
        end=np.asarray([table.end[pos[t]].max() for t in order], dtype=np.float64),
        text=[" ".join(table.text[i] for i in pos[t]) for t in order],
        text_native=[" ".join(table.text_native[i] for i in pos[t]) for t in order],
        blocks=blocks,
        tasks=table.tasks,
        available=table.available,
    )


def load_cached(apps: list[str] | None = None) -> SegmentTable:
    root = frame_cache_dir()
    if not root.is_dir():
        raise SystemExit(f"no frame cache at {root}; run `python -m v2k frames` first")
    folders = [root / a for a in apps] if apps else sorted(p for p in root.iterdir() if p.is_dir())
    records = []
    for folder in folders:
        for json_path in sorted(folder.glob("*.json")):
            npz_path = json_path.with_suffix(".npz")
            if not npz_path.exists():
                continue
            rec = json.loads(json_path.read_text(encoding="utf-8"))
            with np.load(npz_path) as z:
                arrays = {k: z[k] for k in z.files}
            records.append((arrays, rec))
    if not records:
        raise SystemExit(f"no cached tasks under {root} for {apps or 'any app'}")
    return build_table(records)


def task_labels(table: SegmentTable, source: str) -> dict[int, str]:
    """Label per task.

    keyword   the backend's derive_activity_label (keyword match on the instruction)
    app       the application on screen - real ground truth, useful to check
              whether the vectors carry any signal at all
    csv:PATH  a file with task_id,label columns, for when the team hand-labels
    """
    if source == "keyword":
        return {tid: t.keyword_label for tid, t in table.tasks.items()}
    if source == "app":
        return {tid: t.platform for tid, t in table.tasks.items()}
    if source.startswith("csv:"):
        path = Path(source[4:])
        with open(path, newline="", encoding="utf-8") as f:
            rows = {int(r["task_id"]): r["label"].strip() for r in csv.DictReader(f) if r["label"].strip()}
        missing = [tid for tid in table.tasks if tid not in rows]
        if missing:
            log.warning(f"{len(missing)} cached task(s) have no label in {path.name} and are left out")
        return {tid: lab for tid, lab in rows.items() if tid in table.tasks}
    raise SystemExit(f"unknown label source '{source}' (keyword, app, csv:PATH)")


class FeatureBuilder:
    """Turns segment rows into a model's input matrix. Fitted on training rows only.

    It holds everything inference needs besides the model itself: the OCR
    TF-IDF vocabulary and the standardisation. A saved bundle carries it, so
    Step B transforms a new video exactly as the training data was transformed.
    """

    def __init__(self, blocks: tuple[str, ...], scale: bool = True):
        self.blocks = blocks
        self.scale = scale
        self._ocr: dict = {}  # block -> the backend's OCRExtractor holding that block's TF-IDF
        self._scaler = None

    @property
    def dim(self) -> int:
        return sum(BLOCK_DIMS[b] for b in self.blocks)

    def _check(self, table: SegmentTable) -> None:
        missing = [b for b in self.blocks if b not in table.available]
        if missing:
            raise SystemExit(
                f"the cache has no {', '.join(missing)} for every task "
                f"(it holds: {', '.join(sorted(table.available))}). Re-extract those tasks, "
                f"or pick a feature set built from what is cached."
            )

    def fit(self, table: SegmentTable, rows: np.ndarray) -> "FeatureBuilder":
        self._check(table)
        for block in (b for b in self.blocks if b in _TEXT_BLOCKS):
            from app.pipeline.ocr_extractor import OCRExtractor

            # The backend's corpus (FeatureAssembler._collect_ocr_corpus): every
            # keyframe's text plus each task's instruction - training tasks only.
            corpus: list[str] = []
            for tid in np.unique(table.task_id[rows]):
                info = table.tasks[int(tid)]
                corpus.extend(info.keyframe_texts if block == "ocr" else info.keyframe_texts_native)
                if info.instruction:
                    corpus.append(info.instruction)
            ocr = self._ocr[block] = OCRExtractor()
            try:
                ocr.fit_tfidf(corpus)
            except ValueError as e:  # empty vocabulary
                log.warning(f"{block}: TF-IDF could not be fitted ({e}); the block stays zero")
        if self.scale:
            from sklearn.preprocessing import StandardScaler

            self._scaler = StandardScaler().fit(self._raw(table, rows))
        return self

    def transform(self, table: SegmentTable, rows: np.ndarray) -> np.ndarray:
        X = self._raw(table, rows)
        if self._scaler is not None:
            X = self._scaler.transform(X)
        return X.astype(np.float32)

    def _raw(self, table: SegmentTable, rows: np.ndarray) -> np.ndarray:
        parts = []
        for b in self.blocks:
            if b in _TEXT_BLOCKS:
                texts = getattr(table, _TEXT_BLOCKS[b])
                parts.append(np.vstack([self._ocr[b].text_to_features(texts[i]) for i in rows])
                             if len(rows) else np.zeros((0, BLOCK_DIMS[b]), np.float32))
            else:
                if b not in table.blocks:
                    raise SystemExit(f"block '{b}' is not in the frame cache (was it built with --no-cnn?)")
                parts.append(table.blocks[b][rows])
        return np.hstack(parts).astype(np.float32)
