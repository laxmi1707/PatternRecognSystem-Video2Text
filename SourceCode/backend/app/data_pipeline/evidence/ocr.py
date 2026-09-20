from __future__ import annotations

import numpy as np

from app.data_pipeline.types import EvidenceRecord, Frame

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr

        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader


def extract_ocr_evidence(frame: Frame) -> EvidenceRecord:
    reader = _get_reader()
    detections = reader.readtext(str(frame.image_path))

    texts = [text for _, text, _ in detections]
    confidences = [float(conf) for _, _, conf in detections]
    full_text = " ".join(texts)
    avg_confidence = float(np.mean(confidences)) if confidences else 0.0

    return EvidenceRecord(
        frame=frame,
        source="ocr",
        payload={"text": full_text, "num_detections": len(detections)},
        confidence=avg_confidence,
    )
