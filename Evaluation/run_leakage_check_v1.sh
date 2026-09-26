#!/usr/bin/env bash
# Quantify what an ungrouped split is worth, so the report can say it with a number.
#
# Everything is held fixed - same recordings, same native150 features, same v3
# labels, same xgboost, same seed, segment level - and only the fold split
# changes:
#
#   grouped   a recording's segments stay on one side (every reported run)
#   random    segments shuffled, so a recording appears in both sides. Two frames
#             a second apart are near-identical, so the test fold is largely
#             scored on copies of its own training rows. This is what the
#             backend's dataset.py:80-88 and the data_pipeline's splits.py do.
#
# The gap between the two is the leak. Segment level is required: pooling to one
# row per recording leaves nothing to leak.
set -u
cd "$(dirname "$0")" || exit 1

PY=.venv/Scripts/python.exe
LOG=logs/leakage_check_v1.log
THREADS=16
IDS="4 26"      # xgboost grid: library default (100/6/0.1) and run_016's winner (600/10/0.2)

say() { echo "[$(date '+%F %H:%M:%S')] $*" | tee -a "$LOG"; }

trainers() {
  powershell -NoProfile -Command \
    "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*-m v2k tune*' }).Count" \
    2>/dev/null | tr -d '\r\n '
}

say "queued; waiting for the tuning shards to exit"
while [ "$(trainers)" != "0" ]; do sleep 60; done

for split in grouped random; do
  name="leak-$split"
  say "$name: preparing (segment level, $split split)"
  V2K_MAX_THREADS=$THREADS "$PY" -X utf8 -m v2k tune --prepare \
    --labels csv:labels/labels_v3.csv --features native150 --models xgboost \
    --level segment --split "$split" --folds 5 --min-tasks 10 \
    --threads $THREADS --name "$name" 2>&1 | tee -a "$LOG"

  run=$(ls -d runs/run_*_"$name" 2>/dev/null | sort | tail -1)
  if [ -z "$run" ] || [ ! -f "$run/grid.json" ]; then
    say "$name: prepare failed, stopping"
    exit 1
  fi
  # shellcheck disable=SC2086  # $IDS is a deliberate word list
  V2K_MAX_THREADS=$THREADS "$PY" -X utf8 -m v2k tune \
    --shard 0/1 --run-dir "$run" --ids $IDS --threads $THREADS 2>&1 | tee -a "$LOG"
  V2K_MAX_THREADS=4 "$PY" -X utf8 -m v2k tune --collect --run-dir "$run" --threads 4 \
    2>&1 | grep -E "^\| [0-9]|wrote" | tee -a "$LOG"
  say "$name: done"
done
say "leakage check done"
