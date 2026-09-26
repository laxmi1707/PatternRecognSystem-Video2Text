#!/usr/bin/env bash
# Stage A, second pass. run_016 answered "does tuning help"; this answers the two
# questions its numbers raise and could not settle:
#
#   A1b  the winners' per-class F1 - run_016 stored no predictions, so a headline
#        macro-F1 of 0.3271 says nothing about whether run_command recovered.
#        Eight configurations only: each model's default and each model's winner.
#   A2   do tuning and class balancing add up? Tuning gave xgboost +0.0231 and
#        balancing gave it +0.0139, both measured against the same untuned,
#        unbalanced run - which does not mean +0.037 together. Same 75-config
#        grid, this time with --balance 5.
#
# Same layout as v1: prepare once, SHARDS x THREADS = 20 of 32 threads.
set -u
cd "$(dirname "$0")" || exit 1

PY=.venv/Scripts/python.exe
LOG=logs/tuning_A_v2.log
SHARDS=5
THREADS=4
LABELS=csv:labels/labels_v3.csv
WINNERS="4 6 31 53 55 56 64 65"   # run_016 grid ids: each model's default and best

say() { echo "[$(date '+%F %H:%M:%S')] $*" | tee -a "$LOG"; }

# One pass: prepare, fan out, collect. $1 = run name, rest = extra prepare flags.
pass() {
  local name=$1 ids=$2; shift 2
  say "$name: preparing"
  V2K_MAX_THREADS=12 "$PY" -X utf8 -m v2k tune --prepare \
    --labels "$LABELS" --features native150 \
    --models lightgbm xgboost random_forest stacking \
    --level task --folds 5 --min-tasks 10 --threads 12 --name "$name" "$@" 2>&1 | tee -a "$LOG"

  local run
  run=$(ls -d runs/run_*_"$name" 2>/dev/null | sort | tail -1)
  if [ -z "$run" ] || [ ! -f "$run/grid.json" ]; then
    say "$name: prepare failed, stopping"
    return 1
  fi
  say "$name: prepared $run - $SHARDS shards at $THREADS threads"

  local i
  for i in $(seq 0 $((SHARDS - 1))); do
    # shellcheck disable=SC2086  # $ids is a deliberate word list, or empty
    V2K_MAX_THREADS=$THREADS "$PY" -X utf8 -m v2k tune \
      --shard "$i/$SHARDS" --run-dir "$run" --threads $THREADS ${ids:+--ids $ids} \
      > "logs/tuning_${name}_shard$i.log" 2>&1 &
  done
  wait
  V2K_MAX_THREADS=4 "$PY" -X utf8 -m v2k tune --collect --run-dir "$run" --threads 4 2>&1 | tee -a "$LOG"
  say "$name: done"
}

pass v3-tuned-perclass "$WINNERS"          # minutes: 8 configurations
pass v3-tuned-balanced "" --balance 5      # the full grid again, balanced
say "A v2 done"
