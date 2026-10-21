from __future__ import annotations

import logging
from dataclasses import dataclass, field

import cv2
import numpy as np

logger = logging.getLogger(__name__)

OCR_FEATURE_DIM = 50


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


class OCRExtractor:
    def __init__(self, languages: list[str] | None = None, use_gpu: bool = False):
        self._languages = languages or ["en"]
        self._use_gpu = use_gpu
        self._easyocr_reader = None
        self._tfidf = None
        self._fitted = False

    def _get_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(
                    self._languages, gpu=self._use_gpu, verbose=False
                )
            except ImportError:
                logger.warning("easyocr not installed, OCR will return empty results")
        return self._easyocr_reader

    def extract_text(self, image: np.ndarray) -> OCRResult:
        reader = self._get_reader()
        if reader is None:
            return OCRResult()

        try:
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb = image

            results = reader.readtext(rgb)

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
            # Upscale to full resolution before OCR — resized (640x480) frames produce noise
            img = self._upscale_for_ocr(kf.image)
            result = self.extract_with_fallback(img)
            if result.full_text:
                all_text_parts.append(result.full_text)
                print(f"[OCR-DEBUG] frame OCR len={len(result.full_text)} conf={result.mean_confidence:.2f} text={repr(result.full_text[:100])}", flush=True)
            all_confidences.extend(r.confidence for r in result.regions)

        combined_text = " ".join(all_text_parts)
        features = self.text_to_features(combined_text)

        return features, combined_text
