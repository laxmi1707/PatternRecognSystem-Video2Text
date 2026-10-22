#!/usr/bin/env bash
# Assemble the build context and build the SOP detector image.
#
#   bash Evaluation/deploy/sop-detector/build.sh [tag]        (default tag: latest)
#
# The context holds only what the service needs: the Evaluation code, the backend
# code the models were trained against (commit d866716, NOT the current main: its
# video, UI and OCR modules have changed since), the fitted models and the stored
# demo runs. It is rebuilt from the repository each time, into build/ next to this file.
set -euo pipefail

TAG="${1:-latest}"
IMAGE="video2text-sop-detector:${TAG}"
HERE="$(cd "$(dirname "$0")" && pwd)"
EVAL="$(cd "$HERE/../.." && pwd)"
REPO="$(git -C "$EVAL" rev-parse --show-toplevel)"
SNAPSHOT=d866716
BUILD="$HERE/build"
CTX="$BUILD/context"

case "$BUILD" in */deploy/sop-detector/build) ;; *) echo "unexpected build dir $BUILD"; exit 1 ;; esac
rm -rf "$BUILD"
mkdir -p "$CTX/vendor/main-$SNAPSHOT" "$CTX/runs/run_037_sop-detector" \
         "$CTX/runs/run_029_appid70/models" "$CTX/cache/demo_v2"

git -C "$REPO" archive "$SNAPSHOT" SourceCode/backend | tar -x -C "$CTX/vendor/main-$SNAPSHOT"

cp "$EVAL"/*.py "$CTX/"
cp -r "$EVAL/v2k" "$CTX/v2k"
rm -rf "$CTX/v2k/__pycache__"
cp "$EVAL/runs/run_037_sop-detector/sop_detector.joblib" "$CTX/runs/run_037_sop-detector/"
cp "$EVAL/runs/run_029_appid70/models/ocr_native+ui+visual+cnn__mlp.joblib" "$CTX/runs/run_029_appid70/models/"
cp "$EVAL/cache/pointer_cnn_v1.pt" "$EVAL/cache/bare_sop_v2_reaction.pkl" "$CTX/cache/"
cp "$EVAL/cache/demo_v2/"*.json "$CTX/cache/demo_v2/"
cp "$HERE/requirements.txt" "$HERE/warmup.py" "$CTX/"
cp "$HERE/Dockerfile" "$BUILD/"

echo "context: $(du -sh "$CTX" | cut -f1); building $IMAGE"
docker build -t "$IMAGE" "$BUILD"
echo "built $IMAGE"
