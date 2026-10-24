"""Run at image build: download every model's weights, then run the whole detector once.

easyocr's detector and recogniser, YOLOv8n and ResNet-18 are downloaded on first use;
doing it here bakes them into the image. Then each of the detector's models predicts
once, and the whole detector runs on a short generated video of text being typed, so
a missing library fails the build instead of the first upload.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import use_backend  # noqa: E402

use_backend()
import cv2  # noqa: E402
import joblib  # noqa: E402
import numpy as np  # noqa: E402

from v2k import sop_detector as sd  # noqa: E402
from v2k.frames import Extractors  # noqa: E402

ex = Extractors(with_cnn=True)
blank = np.full((480, 640, 3), 255, np.uint8)
ex.ocr.extract_text(blank)
ex.ui.detect(blank)
ex.cnn.embed([blank])

import detector  # noqa: E402
from detector import clicks, model_file, typed_text  # noqa: E402

clicks.load_pointer_model()
clicks.load_reaction_model()
if model_file.PKL:                       # the image: all four models in one pickle
    bundle = model_file.load()["typing"]
else:
    bundle = joblib.load(typed_text.RANKERS)
    joblib.load(sd.stage1_path(bundle))
pooled = bundle["pooled"]
pooled.predict_proba(np.zeros((1, pooled.n_features_in_)))      # LightGBM needs libgomp

# A 10 s, 1280x720 video: a command typed into a terminal-like window, one character
# every 0.4 s.
text = "sudo adduser priya"
with tempfile.TemporaryDirectory() as tmp:
    video = Path(tmp) / "typing.mp4"
    out = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (1280, 720))
    for i in range(100):
        f = np.full((720, 1280, 3), 30, np.uint8)
        cv2.putText(f, "user@host:~$ " + text[:min(len(text), i // 4)], (60, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4, (235, 235, 235), 3, cv2.LINE_AA)
        out.write(f)
    out.release()
    res = detector.run(video)
print(f"warm-up done: every model loaded and predicted; the whole detector ran on a test video "
      f"in {res['seconds_taken']} s (app {res['app']}, {len(res['steps'])} steps)")
