"""Train the round-4 typing ranker for the detector (design and scores: run_039).

Fits v2k.sop_extras.fit on every recording - per-application rankers and one pooled
ranker on run_037's 32 features plus the 12 of sop_ranker_experiments_v4, combined by
their mean - and saves the bundle the detector loads.

    python train_typing_v2.py [THRESHOLD]       (default 0.5)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(16)

import joblib  # noqa: E402
import numpy as np  # noqa: E402

from sop_ranker_experiments_v4 import EXTRA, EXTRAS  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402
from v2k import sop_extras as sx  # noqa: E402


def main() -> None:
    from v2k.evaluate import new_run_dir
    thr = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    assert EXTRA == sx.EXTRA + sx.NOVELTY
    data = sd.build_candidates()
    with np.load(EXTRAS) as z:
        E = z["E"]
    bundle = sx.fit(data, E, thr)
    out = new_run_dir("sop-detector-v2")
    joblib.dump(bundle, out / "sop_detector.joblib", compress=3)
    (out / "config.json").write_text(json.dumps({
        "design": "runs/run_039_sop-ranker-experiments-4", "threshold": thr,
        "per_app_rankers": len(bundle["per_app"]), "n_rows": bundle["n_rows"],
        "importance": bundle["importance"][:15]}, indent=2), encoding="utf-8")
    print(f"{len(bundle['per_app'])} application rankers + pooled, threshold {thr}; saved to {out}")


if __name__ == "__main__":
    main()
