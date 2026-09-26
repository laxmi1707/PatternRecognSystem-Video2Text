#!/usr/bin/env bash
# Stage A: hyperparameter grid search, started once stage C has released the CPU.
#
# The cache load costs three minutes and a single fit costs seconds, so the grid
# is prepared once and then split across SHARDS processes that each start in a
# second. SHARDS x THREADS stays at or under the 22 threads the user authorised;
# the machine belongs to his team lead, so it is never all of them.
set -u
cd "$(dirname "$0")" || exit 1

PY=.venv/Scripts/python.exe
LOG=logs/tuning_A_v1.log
SHARDS=5
THREADS=4          # 5 x 4 = 20 of 32
NAME=v3-tuned
LABELS=csv:labels/labels_v3.csv

say() { echo "[$(date '+%F %H:%M:%S')] $*" | tee -a "$LOG"; }

# Git Bash has no pgrep and its ps shows only the executable, so ask Windows.
trainers() {
  powershell -NoProfile -Command \
    "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*-m v2k train*' }).Count" \
    2>/dev/null | tr -d '\r\n '
}

say "stage A queued; waiting for stage C to exit"
while [ "$(trainers)" != "0" ]; do sleep 60; done
say "stage C done - preparing the grid"

V2K_MAX_THREADS=12 "$PY" -X utf8 -m v2k tune --prepare \
  --labels "$LABELS" --features native150 \
  --models lightgbm xgboost random_forest stacking \
  --level task --folds 5 --min-tasks 10 --threads 12 --name "$NAME" 2>&1 | tee -a "$LOG"

RUN=$(ls -d runs/run_*_"$NAME" 2>/dev/null | sort | tail -1)
if [ -z "$RUN" ] || [ ! -f "$RUN/grid.json" ]; then
  say "prepare failed - no prepared run folder, stopping"
  exit 1
fi
say "prepared $RUN - launching $SHARDS shards at $THREADS threads each"

for i in $(seq 0 $((SHARDS - 1))); do
  V2K_MAX_THREADS=$THREADS "$PY" -X utf8 -m v2k tune \
    --shard "$i/$SHARDS" --run-dir "$RUN" --threads $THREADS \
    > "logs/tuning_A_v1_shard$i.log" 2>&1 &
done
wait
say "all shards finished - collecting"

V2K_MAX_THREADS=4 "$PY" -X utf8 -m v2k tune --collect --run-dir "$RUN" --threads 4 2>&1 | tee -a "$LOG"
say "A done"
