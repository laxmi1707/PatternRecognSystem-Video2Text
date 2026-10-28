"""Incremental OCR for the typing branch: read only what changed since the previous frame.

The typing branch reads every 1-fps frame at full resolution, and that OCR is 97% of the
detector's time. Most consecutive frames differ in a few small places (the pointer, a
few typed characters). So, per frame:

    - nothing changed: the previous frame's regions are returned as they are
    - a little changed: each changed area's full-width band of the screen is read
      again, widened to cover every previous text region it touches, so a line is
      always read whole - reading part of a line splits its text differently from a
      full read, and the typing rule then misses it; previous regions in the bands
      are replaced by the new reads, the rest are kept
    - much changed (over FULL_FRACTION of the screen), the first frame, or every
      FULL_EVERY frames: the whole frame is read, as before

IncrementalOCR wraps the backend's OCRExtractor and keeps its extract_text interface,
so v2k.frames.extract_video uses it unchanged; make a new one per video.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

DIFF = 25              # grey-level change that counts as changed
DILATE = 9             # px, joins the pieces of one changed word
PAD_Y = 12             # px above and below a changed area
FULL_FRACTION = 0.15   # changed share of the screen above which the whole frame is read
FULL_EVERY = 10        # frames between full reads, so small errors cannot pile up
MIN_AREA = 20          # px; smaller changes (noise) are ignored


def _py(v):
    """A numpy scalar as the plain Python number the full reads give (records are JSON)."""
    return v.item() if hasattr(v, "item") else v


@dataclass
class Region:
    text: str
    bbox: tuple
    confidence: float


@dataclass
class Result:
    regions: list = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return " ".join(r.text for r in self.regions)

    @property
    def mean_confidence(self) -> float:
        return float(np.mean([r.confidence for r in self.regions])) if self.regions else 0.0


class IncrementalOCR:
    def __init__(self, ocr):
        self.ocr = ocr
        self.prev = None          # previous grey frame
        self.regions: list[Region] = []
        self.since_full = 0
        self.full_reads = self.partial_reads = self.reused = 0

    def _read(self, image, x0=0, y0=0) -> list[Region]:
        out = []
        for g in self.ocr.extract_text(image).regions:
            x1, y1, x2, y2 = g.bbox
            box = tuple(_py(v) for v in (x1 + x0, y1 + y0, x2 + x0, y2 + y0))
            out.append(Region(g.text, box, _py(g.confidence)))
        return out

    def extract_text(self, frame) -> Result:
        import cv2
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        H, W = grey.shape
        if self.prev is None or self.prev.shape != grey.shape or self.since_full >= FULL_EVERY:
            return self._full(frame, grey)
        changed = (cv2.absdiff(grey, self.prev) > DIFF).astype(np.uint8)
        if changed.mean() > FULL_FRACTION:
            return self._full(frame, grey)
        self.prev = grey
        self.since_full += 1
        changed = cv2.dilate(changed, np.ones((DILATE, DILATE), np.uint8))
        n, _, stats, _ = cv2.connectedComponentsWithStats(changed, connectivity=8)
        bands = [(max(0, y - PAD_Y), min(H, y + h + PAD_Y)) for x, y, w, h, a in stats[1:] if a >= MIN_AREA]
        if not bands:
            self.reused += 1
            return Result(list(self.regions))
        bands = self._whole_lines(bands, H)
        if sum(b - a for a, b in bands) > 0.5 * H:
            return self._full(frame, grey)
        keep = [r for r in self.regions if not any(r.bbox[1] < b and r.bbox[3] > a for a, b in bands)]
        for y1, y2 in bands:
            keep += self._read(frame[y1:y2], 0, y1)
        self.regions = sorted(keep, key=lambda r: (r.bbox[1], r.bbox[0]))
        self.partial_reads += 1
        return Result(list(self.regions))

    def _whole_lines(self, bands, H):
        """Merge overlapping bands and grow them until no previous region is cut by an edge."""
        while True:
            bands = sorted(bands)
            merged = [list(bands[0])]
            for a, b in bands[1:]:
                if a <= merged[-1][1]:
                    merged[-1][1] = max(merged[-1][1], b)
                else:
                    merged.append([a, b])
            grown = False
            for m in merged:
                for r in self.regions:
                    y1, y2 = int(r.bbox[1]), int(r.bbox[3])
                    if y1 < m[1] and y2 > m[0] and (y1 < m[0] or y2 > m[1]):
                        m[0], m[1] = max(0, min(m[0], y1 - 2)), min(H, max(m[1], y2 + 2))
                        grown = True
            bands = [tuple(m) for m in merged]
            if not grown:
                return bands

    def _full(self, frame, grey) -> Result:
        self.prev = grey
        self.since_full = 0
        self.regions = self._read(frame)
        self.full_reads += 1
        return Result(list(self.regions))

