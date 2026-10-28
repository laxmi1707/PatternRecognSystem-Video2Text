from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

import cv2
import numpy as np

logger = logging.getLogger(__name__)

OCR_FEATURE_DIM = 50

# A keyframe whose mean pixel difference from the last frame read is at most this
# (0-255 grey levels, on a 320x240 thumbnail) shows the same screen: reuse its text.
DUPLICATE_FRAME_DIFF = 1.0
OCR_BATCH_SIZE = 16

# Loading EasyOCR's models takes ~10 s, so one reader per process is shared by all jobs.
# The lock keeps two jobs from running OCR at once; they would only compete for the CPU.
_READERS: dict[tuple, object] = {}
_READER_LOCK = threading.Lock()


@dataclass
class TextRegion:
    text: str
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float


@dataclass
class OCRResult:
    regions: list[TextRegion] = field(default_factory=list)
    full_text: str = ""
    mean_confidence: float = 0.0


def _similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity between two strings."""
    if not a or not b:
        return 0.0
    ta, tb = set(a.lower().split()), set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _deduplicate_ocr(parts: list[str], threshold: float = 0.6) -> str:
    """Merge OCR text from multiple keyframes, dropping near-duplicate frames.

    Keyframes within the same segment often show nearly identical content.
    Keeping all of them concatenated repeats the same text 2-3x, which
    confuses downstream command extraction and inflates TF-IDF features.
    Strategy: keep a frame only if it is sufficiently different from all
    already-kept frames (Jaccard similarity on tokens < threshold).
    Then join the unique frames with a space.
    """
    kept: list[str] = []
    for part in parts:
        if not part.strip():
            continue
        if all(_similarity(part, k) < threshold for k in kept):
            kept.append(part)
    return " ".join(kept)


class OCRExtractor:
    def __init__(self, languages: list[str] | None = None, use_gpu: bool = False):
        self._languages = languages or ["en"]
        self._use_gpu = use_gpu
        self._easyocr_reader = None
        self._tfidf = None
        self._fitted = False
        # Thumbnail and result of the last frame actually read, to skip unchanged screens
        self._last_thumb: np.ndarray | None = None
        self._last_result: OCRResult | None = None
        self.frames_read = 0
        self.frames_reused = 0

    def _get_reader(self):
        if self._easyocr_reader is None:
            key = (tuple(self._languages), self._use_gpu)
            with _READER_LOCK:
                if key not in _READERS:
                    try:
                        import easyocr
                        _READERS[key] = easyocr.Reader(self._languages, gpu=self._use_gpu, verbose=False)
                    except ImportError:
                        logger.warning("easyocr not installed, OCR will return empty results")
                        return None
                self._easyocr_reader = _READERS[key]
        return self._easyocr_reader

    @staticmethod
    def _thumbnail(image: np.ndarray) -> np.ndarray:
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        return cv2.resize(grey, (320, 240), interpolation=cv2.INTER_AREA).astype(np.int16)

    def extract_text(self, image: np.ndarray) -> OCRResult:
        reader = self._get_reader()
        if reader is None:
            return OCRResult()

        try:
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb = image

            with _READER_LOCK:
                results = reader.readtext(rgb, batch_size=OCR_BATCH_SIZE)

            regions: list[TextRegion] = []
            for bbox_points, text, conf in results:
                x_coords = [int(p[0]) for p in bbox_points]
                y_coords = [int(p[1]) for p in bbox_points]
                bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
                regions.append(TextRegion(text=text, bbox=bbox, confidence=float(conf)))

            full_text = " ".join(r.text for r in regions)
            mean_conf = float(np.mean([r.confidence for r in regions])) if regions else 0.0

            return OCRResult(regions=regions, full_text=full_text, mean_confidence=mean_conf)

        except Exception as e:
            print(f"[OCR-DEBUG] EasyOCR FAILED: {type(e).__name__}: {e}", flush=True)
            logger.warning(f"EasyOCR failed, trying Tesseract fallback: {e}")
            return self._tesseract_fallback(image)

    def extract_with_fallback(self, image: np.ndarray) -> OCRResult:
        # Always use EasyOCR — Tesseract fallback produces worse results for terminal text
        return self.extract_text(image)

    def _tesseract_fallback(self, image: np.ndarray) -> OCRResult:
        try:
            import pytesseract
            from PIL import Image

            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb = image

            pil_img = Image.fromarray(rgb)
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)

            regions: list[TextRegion] = []
            for i, text in enumerate(data["text"]):
                text = text.strip()
                conf = float(data["conf"][i])
                if text and conf > 0:
                    x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                    regions.append(
                        TextRegion(
                            text=text,
                            bbox=(x, y, x + w, y + h),
                            confidence=conf / 100.0,
                        )
                    )

            full_text = " ".join(r.text for r in regions)
            mean_conf = float(np.mean([r.confidence for r in regions])) if regions else 0.0
            return OCRResult(regions=regions, full_text=full_text, mean_confidence=mean_conf)

        except ImportError:
            logger.warning("pytesseract not installed, returning empty OCR result")
            return OCRResult()
        except Exception as e:
            logger.warning(f"Tesseract fallback failed: {e}")
            return OCRResult()

    def fit_tfidf(self, corpus: list[str]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._tfidf = TfidfVectorizer(max_features=OCR_FEATURE_DIM, stop_words="english")
        self._tfidf.fit(corpus)
        self._fitted = True

    def text_to_features(self, text: str) -> np.ndarray:
        if not self._fitted or self._tfidf is None:
            return np.zeros(OCR_FEATURE_DIM, dtype=np.float32)
        vec = self._tfidf.transform([text]).toarray()[0]
        return vec.astype(np.float32)

    def _upscale_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Upscale image to at least 1000px wide for reliable OCR on screen recordings."""
        h, w = image.shape[:2]
        if w < 1000:
            scale = 1000 / w
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        return image

    def extract_segment(self, keyframes: list) -> tuple[np.ndarray, str]:
        all_text_parts: list[str] = []
        all_confidences: list[float] = []

        for kf in keyframes:
            # Screen recordings often hold still: reuse the text of an unchanged frame
            thumb = self._thumbnail(kf.image)
            if (
                self._last_result is not None
                and np.abs(thumb - self._last_thumb).mean() <= DUPLICATE_FRAME_DIFF
            ):
                result = self._last_result
                self.frames_reused += 1
            else:
                # Upscale to full resolution before OCR — resized (640x480) frames produce noise
                img = self._upscale_for_ocr(kf.image)
                result = self.extract_with_fallback(img)
                self._last_thumb, self._last_result = thumb, result
                self.frames_read += 1
            if result.full_text:
                all_text_parts.append(result.full_text)
                print(f"[OCR-DEBUG] frame OCR len={len(result.full_text)} conf={result.mean_confidence:.2f} text={repr(result.full_text[:100])}", flush=True)
            all_confidences.extend(r.confidence for r in result.regions)

        combined_text = _deduplicate_ocr(all_text_parts)
        features = self.text_to_features(combined_text)

        return features, combined_text
