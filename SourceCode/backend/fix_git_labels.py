"""
Remap git_operations labels (index 0) to coding_editing (index 6) in cached
feature arrays, then trigger --load-features retrain.

Run on EC2 BEFORE retraining:
    cd ~/PatternRecognSystem-Video2Text/SourceCode/backend
    FEATURE_BACKEND=cnn MODEL_DIR=./models/v3 python fix_git_labels.py --model-dir ../../models/v3

After this script completes, run:
    FEATURE_BACKEND=cnn MODEL_DIR=./models/v3 python -m app.train \
        --dataset-root ../../dataset \
        --model-dir ../../models/v3 \
        --load-features
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="./models/v3")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    files = {
        "y_train": model_dir / "y_train.npy",
        "y_test":  model_dir / "y_test.npy",
    }

    # Indices into ACTIVITY_LABELS
    GIT_IDX = 0   # "git_operations"
    CODE_IDX = 6  # "coding_editing"

    for name, path in files.items():
        if not path.exists():
            print(f"  SKIP {name}: file not found at {path}")
            continue

        y = np.load(str(path))
        before = Counter(y.tolist())
        git_count = int(np.sum(y == GIT_IDX))

        if git_count == 0:
            print(f"  {name}: no git_operations labels found — nothing to do")
            continue

        y[y == GIT_IDX] = CODE_IDX
        after = Counter(y.tolist())
        np.save(str(path), y)

        print(f"  {name}: remapped {git_count} git_operations → coding_editing")
        print(f"    before: {dict(before)}")
        print(f"    after:  {dict(after)}")

    print("\nDone. Now run:")
    print(f"  FEATURE_BACKEND=cnn MODEL_DIR={model_dir} python -m app.train \\")
    print(f"    --dataset-root ../../dataset \\")
    print(f"    --model-dir {model_dir} \\")
    print(f"    --load-features")


if __name__ == "__main__":
    main()
