"""The SOP detector's four fitted models in one pickle file, for deployment.

    stage1       names the application: run_029's MLP bundle (a dict, as joblib saved it)
    typing       keeps typed text: run_040's ranker bundle (per-application LightGBM,
                 pooled LightGBM, text model, feature lists, threshold)
    reaction     decides whether a pointer stop was a click: the 17-feature LightGBM
                 filter and its threshold (cache/reaction_lgbm_v2.pkl)
    pointer_cnn  finds the mouse pointer: the CNN's weights as numpy arrays

The file is a plain pickle: `pickle.load(open("sop_detector.pkl", "rb"))` returns the
dict (scikit-learn, LightGBM and numpy must be importable; torch is not needed to read
it). The code that uses the models is this package; with SOP_DETECTOR_PKL set to the
file, detector.typed_text and detector.clicks load everything from it instead of from
runs/ and cache/.

    python -m detector.model_file build models/sop_detector.pkl     write it from runs/ and cache/
    python -m detector.model_file show models/sop_detector.pkl      what is inside
"""
from __future__ import annotations

import os
import pickle
import sys
import time
from functools import lru_cache
from pathlib import Path

FORMAT = "video2text-sop-detector"
VERSION = 1
_DEFAULT = Path(__file__).resolve().parent.parent / "models" / "sop_detector.pkl"
# SOP_DETECTOR_PKL overrides; otherwise the file shipped in models/ is used.
PKL = os.environ.get("SOP_DETECTOR_PKL") or (str(_DEFAULT) if _DEFAULT.exists() else None)


def build(out: Path) -> dict:
    import joblib
    import torch

    from detector import clicks, typed_text
    from v2k import sop_detector as sd

    typing = joblib.load(typed_text.RANKERS)
    stage1_path = sd.stage1_path(typing)
    models = {
        "format": FORMAT,
        "version": VERSION,
        "built": time.strftime("%Y-%m-%d %H:%M"),
        "sources": {
            "stage1": stage1_path.relative_to(sd.RUNS.parent).as_posix(),
            "typing": typed_text.RANKERS.relative_to(sd.RUNS.parent).as_posix(),
            "reaction": clicks.REACTION_MODEL.relative_to(sd.RUNS.parent).as_posix(),
            "pointer_cnn": clicks.POINTER_MODEL.relative_to(sd.RUNS.parent).as_posix(),
        },
        "stage1": joblib.load(stage1_path),
        "typing": typing,
        "reaction": pickle.loads(clicks.REACTION_MODEL.read_bytes()),
        "pointer_cnn": {k: v.cpu().numpy() for k, v in
                        torch.load(clicks.POINTER_MODEL, map_location="cpu").items()},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(models, f, protocol=pickle.HIGHEST_PROTOCOL)
    return models


@lru_cache(maxsize=1)
def load(path: str | None = None) -> dict:
    with open(path or PKL, "rb") as f:
        models = pickle.load(f)
    if models.get("format") != FORMAT:
        raise ValueError(f"{path or PKL} is not an SOP detector model file")
    return models


def show(path: str) -> None:
    m = load(path)
    print(f"{path}: {FORMAT} v{m['version']}, built {m['built']}, {Path(path).stat().st_size / 1e6:.1f} MB")
    t = m["typing"]
    print(f"  stage1       {m['sources']['stage1']}: blocks {m['stage1'].get('blocks')}")
    print(f"  typing       {m['sources']['typing']}: {len(t['per_app'])} application rankers + pooled, "
          f"{len(t['all_features'])} features, threshold {t['threshold']}")
    r = m["reaction"]
    print(f"  reaction     {m['sources']['reaction']}: {len(r.get('features', []))} features, "
          f"threshold {r['threshold']:.3f}")
    print(f"  pointer_cnn  {m['sources']['pointer_cnn']}: {len(m['pointer_cnn'])} tensors, "
          f"{sum(v.size for v in m['pointer_cnn'].values()):,} weights")


if __name__ == "__main__":
    cmd, path = sys.argv[1], Path(sys.argv[2])
    if cmd == "build":
        if path.exists():
            raise SystemExit(f"{path} exists; write a new file")
        build(path)
        show(str(path))
    else:
        show(str(path))
