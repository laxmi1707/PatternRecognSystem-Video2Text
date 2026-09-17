from __future__ import annotations

import logging
from dataclasses import dataclass, field

import cv2
import numpy as np

logger = logging.getLogger(__name__)

UI_FEATURE_DIM = 30

UI_ELEMENT_CLASSES = [
    "button", "text_field", "menu", "dropdown", "toolbar",
    "sidebar", "tab", "dialog", "terminal", "icon",
    "scroll_bar", "status_bar",
]
_UI_CLASS_INDEX = {c: i for i, c in enumerate(UI_ELEMENT_CLASSES)}

INTERACTIVE_CLASSES = {"button", "dropdown", "menu", "text_field"}


@dataclass
class UIElement:
    class_name: str
    bbox: tuple[int, int, int, int]
    confidence: float


@dataclass
class UIDetectionResult:
    elements: list[UIElement] = field(default_factory=list)
    element_counts: dict[str, int] = field(default_factory=dict)
    total_elements: int = 0


class UIDetector:
    def __init__(self, model_name: str = "yolov8n.pt", conf_threshold: float = 0.25):
        self._model_name = model_name
        self._conf_threshold = conf_threshold
        self._model = None
        self._coco_to_ui = self._build_coco_mapping()

    def _build_coco_mapping(self) -> dict[str, str]:
        return {
            "tv": "terminal",
            "laptop": "terminal",
            "cell phone": "dialog",
            "keyboard": "text_field",
            "mouse": "icon",
            "remote": "button",
            "book": "tab",
            "clock": "status_bar",
        }

    def _get_model(self):
        if self._model is None:
            try:
                from ultralytics import YOLO
                self._model = YOLO(self._model_name)
            except ImportError:
                logger.warning("ultralytics not installed, UI detection will return empty results")
            except Exception as e:
                logger.warning(f"Failed to load YOLO model: {e}")
        return self._model

    def detect(self, image: np.ndarray) -> UIDetectionResult:
        model = self._get_model()
        if model is None:
            return UIDetectionResult()

        try:
            results = model(image, conf=self._conf_threshold, verbose=False)

            elements: list[UIElement] = []
            counts: dict[str, int] = {}

            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = model.names.get(cls_id, "unknown")
                    ui_class = self._coco_to_ui.get(cls_name, "icon")

                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])

                    elements.append(
                        UIElement(
                            class_name=ui_class,
                            bbox=(int(x1), int(y1), int(x2), int(y2)),
                            confidence=conf,
                        )
                    )
                    counts[ui_class] = counts.get(ui_class, 0) + 1

            return UIDetectionResult(
                elements=elements,
                element_counts=counts,
                total_elements=len(elements),
            )

        except Exception as e:
            logger.warning(f"YOLO detection failed: {e}")
            return UIDetectionResult()

    def detection_to_features(self, detection: UIDetectionResult, frame_area: int = 1) -> np.ndarray:
        features = np.zeros(UI_FEATURE_DIM, dtype=np.float32)

        # [0:12] Element type counts (normalized)
        total = max(detection.total_elements, 1)
        for cls_name, count in detection.element_counts.items():
            idx = _UI_CLASS_INDEX.get(cls_name, -1)
            if 0 <= idx < 12:
                features[idx] = count / total

        # [12:20] Spatial layout features
        if detection.elements:
            x_centers = [(e.bbox[0] + e.bbox[2]) / 2 for e in detection.elements]
            y_centers = [(e.bbox[1] + e.bbox[3]) / 2 for e in detection.elements]
            areas = [(e.bbox[2] - e.bbox[0]) * (e.bbox[3] - e.bbox[1]) for e in detection.elements]
            confs = [e.confidence for e in detection.elements]

            max_center = max(max(x_centers, default=1), 1)
            features[12] = np.mean(x_centers) / max_center
            features[13] = np.mean(y_centers) / max(max(y_centers, default=1), 1)
            features[14] = (np.std(x_centers) / max_center) if len(x_centers) > 1 else 0.0
            features[15] = (np.std(y_centers) / max(max(y_centers, default=1), 1)) if len(y_centers) > 1 else 0.0
            max_area = max(max(areas, default=1), 1)
            features[16] = np.mean(areas) / max_area
            features[17] = (np.std(areas) / max_area) if len(areas) > 1 else 0.0
            features[18] = max(areas) / max(frame_area, 1)
            features[19] = min(detection.total_elements / 50.0, 1.0)  # element density

        # [20:24] Detection confidence stats
        if detection.elements:
            confs = [e.confidence for e in detection.elements]
            features[20] = np.mean(confs)
            features[21] = np.std(confs) if len(confs) > 1 else 0.0
            features[22] = min(confs)
            features[23] = max(confs)

        # [24:30] UI complexity metrics
        features[24] = min(
            sum(1 for e in detection.elements if e.class_name == "text_field") / 5.0, 1.0
        )
        features[25] = min(
            sum(1 for e in detection.elements if e.class_name in INTERACTIVE_CLASSES) / 10.0, 1.0
        )
        features[26] = 1.0 if detection.element_counts.get("toolbar", 0) > 0 else 0.0
        features[27] = 1.0 if detection.element_counts.get("sidebar", 0) > 0 else 0.0
        features[28] = 1.0 if detection.element_counts.get("terminal", 0) > 0 else 0.0
        features[29] = 1.0 if detection.element_counts.get("dialog", 0) > 0 else 0.0

        return features

    def extract_segment(self, keyframes: list) -> np.ndarray:
        if not keyframes:
            return np.zeros(UI_FEATURE_DIM, dtype=np.float32)

        frame_features: list[np.ndarray] = []
        for kf in keyframes:
            detection = self.detect(kf.image)
            h, w = kf.image.shape[:2]
            features = self.detection_to_features(detection, frame_area=h * w)
            frame_features.append(features)

        return np.mean(frame_features, axis=0).astype(np.float32)
