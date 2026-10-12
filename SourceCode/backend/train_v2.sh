#!/usr/bin/env bash
# Train v2 classifiers using EfficientNet-B0 CNN features (FEATURE_BACKEND=cnn)
# Run on EC2 g4dn.xlarge from SourceCode/backend/
#
# Usage:
#   bash train_v2.sh                    # full run (first time, ~4-6 hrs)
#   bash train_v2.sh --load-features    # retrain only (features cached, ~10 min)

set -euo pipefail

DATASET_ROOT="${DATASET_ROOT:-/home/ubuntu/PatternRecognSystem-Video2Text/dataset}"
MODEL_DIR="${MODEL_DIR:-./models/v2}"
EXTRA_ARGS="${@}"

echo "========================================"
echo " Video2Knowledge v2 Training (CNN backbone)"
echo " Dataset : $DATASET_ROOT"
echo " Models  : $MODEL_DIR"
echo " Backend : FEATURE_BACKEND=cnn"
echo "========================================"

mkdir -p "$MODEL_DIR"

FEATURE_BACKEND=cnn \
  python -m app.train \
    --dataset-root "$DATASET_ROOT" \
    --model-dir "$MODEL_DIR" \
    $EXTRA_ARGS \
  2>&1 | tee train_v2.log

echo ""
echo "Done. Models saved to $MODEL_DIR"
echo "To run inference with v2: FEATURE_BACKEND=cnn MODEL_DIR=./models/v2 uvicorn app.main:app ..."
