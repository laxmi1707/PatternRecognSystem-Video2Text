from __future__ import annotations

import cv2

from app.data_pipeline.types import EvidenceRecord, Frame

# Classical-CV heuristics standing in for a trained UI-object detector.
# No labeled UI-element dataset exists yet to train one, so this only reports
# coarse structural cues (panel count, light/dark theme, a rough left-sidebar
# check for an IDE-like layout). It only ever makes a non-"other" guess for
# that one recognizable layout, at low confidence -- pixels alone can't tell
# git from docker from kubectl, so it doesn't pretend to.
MIN_PANEL_AREA_FRACTION = 0.15


def detect_ui_objects(frame: Frame) -> EvidenceRecord:
    image = cv2.imread(str(frame.image_path))
    if image is None:
        return EvidenceRecord(frame=frame, source="ui_heuristic", payload={}, confidence=0.0)

    h, w = image.shape[:2]
    frame_area = h * w
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    panels = [c for c in contours if cv2.contourArea(c) / frame_area >= MIN_PANEL_AREA_FRACTION]

    mean_brightness = float(gray.mean())
    theme = "dark" if mean_brightness < 128 else "light"

    left_strip = gray[:, : max(1, w // 6)]
    has_left_sidebar = abs(float(left_strip.mean()) - mean_brightness) > 20

    if has_left_sidebar and len(panels) >= 1:
        activity_guess = "coding_editing"
        confidence = 0.4
    else:
        activity_guess = "other"
        confidence = 0.25

    return EvidenceRecord(
        frame=frame,
        source="ui_heuristic",
        payload={
            "num_panels": len(panels),
            "theme": theme,
            "has_left_sidebar": has_left_sidebar,
            "activity_guess": activity_guess,
        },
        confidence=confidence,
    )
