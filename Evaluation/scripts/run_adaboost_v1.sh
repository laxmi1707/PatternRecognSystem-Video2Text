#!/usr/bin/env bash
# AdaBoost, scored on exactly the folds the other fourteen were scored on.
#
#   1. all 15 models, same settings as run_013, so the 14 reproduce and AdaBoost
#      slots into the same table rather than a separate one
#   2. AdaBoost's own 18-configuration grid, so its number is its tuned best
#      rather than a default compared against tuned rivals
set -u
cd "$(dirname "$0")" || exit 1

PY=.venv/Scripts/python.exe
LOG=logs/adaboost_v1.log
LABELS=csv:labels/labels_v3.csv

say() { echo "[$(date '+%F %H:%M:%S')] $*" | tee -a "$LOG"; }

say "1/2 all 15 models, v3 labels, native150, recording level"
V2K_MAX_THREADS=22 "$PY" -X utf8 -m v2k train \
  --labels "$LABELS" --features native150 --models all \
  --level task --folds 5 --min-tasks 10 --threads 22 \
  --name v3-all15 2>&1 | tee -a "$LOG"

say "2/2 AdaBoost hyperparameter grid"
V2K_MAX_THREADS=12 "$PY" -X utf8 -m v2k tune --prepare \
  --labels "$LABELS" --features native150 --models adaboost \
  --level task --folds 5 --min-tasks 10 --threads 12 --name adaboost-tuned 2>&1 | tee -a "$LOG"

run=$(ls -d runs/run_*_adaboost-tuned 2>/dev/null | sort | tail -1)
if [ -z "$run" ] || [ ! -f "$run/grid.json" ]; then
  say "prepare failed, stopping"
  exit 1
fi
for i in 0 1 2 3 4; do
  V2K_MAX_THREADS=4 "$PY" -X utf8 -m v2k tune --shard "$i/5" --run-dir "$run" --threads 4 \
    > "logs/adaboost_v1_shard$i.log" 2>&1 &
done
wait
V2K_MAX_THREADS=4 "$PY" -X utf8 -m v2k tune --collect --run-dir "$run" --threads 4 2>&1 | tee -a "$LOG"
say "adaboost done"
