#!/bin/bash
# v3 training: fresh feature extraction with OCR + action logs
# Models: SVM, KNN, Random Forest, LSTM, CNN1D, Stacking (6 models)
# PT requirements: supervised learning, ML+DL, ensemble, intelligent sensing
# Expected runtime: 10-12 hrs (feature extraction) + ~20 min (training)

set -e

DATASET_ROOT="${DATASET_ROOT:-/app/dataset}"
MODEL_DIR=./models/v3
LOG_FILE=train_v3.log

mkdir -p "$MODEL_DIR"

echo "Starting v3 training at $(date)" | tee "$LOG_FILE"
echo "Dataset: $DATASET_ROOT" | tee -a "$LOG_FILE"
echo "Models: svm knn random_forest lstm cnn1d stacking" | tee -a "$LOG_FILE"
echo "OCR: enabled | Action logs: enabled | Feature backend: cnn" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

FEATURE_BACKEND=cnn \
    python3 -m app.train \
    --dataset-root "$DATASET_ROOT" \
    --model-dir "$MODEL_DIR" \
    --models svm knn random_forest lstm cnn1d stacking \
    2>&1 | tee -a "$LOG_FILE"

echo "========================================" | tee -a "$LOG_FILE"
echo "v3 training complete at $(date)" | tee -a "$LOG_FILE"
