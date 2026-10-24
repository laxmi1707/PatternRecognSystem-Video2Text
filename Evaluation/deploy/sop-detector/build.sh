#!/usr/bin/env bash
# Assemble the build context and build the SOP detector image.
#
#   bash Evaluation/deploy/sop-detector/build.sh [tag]        (default tag: latest)
#
# The context holds only what the service needs: the detector package, the backend
# code the models were trained against (commit d866716, NOT the current main: its
# video, UI and OCR modules have changed since), the fitted models (one pickle,
# models/sop_detector.pkl) and the stored demo runs. It is rebuilt from the repository each time, into build/ next to this file.
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
mkdir -p "$CTX/vendor/main-$SNAPSHOT" "$CTX/models" "$CTX/cache/demo_v6"

git -C "$REPO" archive "$SNAPSHOT" SourceCode/backend | tar -x -C "$CTX/vendor/main-$SNAPSHOT"

# The service, the detector package and the v2k harness it builds on - not the
# research scripts.
cp "$EVAL/sop_detector_service.py" "$CTX/"
cp -r "$EVAL/detector" "$CTX/detector"
cp -r "$EVAL/v2k" "$CTX/v2k"
rm -rf "$CTX/detector/__pycache__" "$CTX/v2k/__pycache__"
# All four fitted models in one pickle (detector/model_file.py; SOP_DETECTOR_PKL in the Dockerfile)
cp "$EVAL/models/sop_detector.pkl" "$CTX/models/"
cp "$EVAL/cache/demo_v6/"*.json "$CTX/cache/demo_v6/"
cp "$HERE/requirements.txt" "$HERE/warmup.py" "$CTX/"
cp "$HERE/Dockerfile" "$BUILD/"

echo "context: $(du -sh "$CTX" | cut -f1); building $IMAGE"
docker build -t "$IMAGE" "$BUILD"
echo "built $IMAGE"
