#!/usr/bin/env bash
# Wait for the frame extraction to finish, then start the training.
#
# "Finished" means the scheduler wrote its own completion line - not that the
# cache stopped growing, which also happens at every restart.
#
# Liveness is judged by the extraction log's age rather than by looking for the
# process: Git Bash has no pgrep, and its `ps` shows only the executable, so
# every bash script on the machine looks alike.
#
# STALE_MIN must stay above run_scheduled_v3.sh's CYCLE_MIN (45), or a routine
# memory-reclaiming restart would be read as a death. v1 watched
# frames_sched_004.log, which v3 no longer writes to.
#
# Start:  nohup bash run_when_frames_done_v2.sh > logs/chain_v2.log 2>&1 &

cd "$(dirname "$0")"
STATUS=logs/scheduler.status
FRAMES_LOG=logs/frames_sched_005.log
CACHE=cache/frames_v1_main-d866716
EXPECTED=6991
STALE_MIN=75

say() { echo "$(date '+%F %T') $*"; }

cached() { find "$CACHE" -name "*.json" 2>/dev/null | wc -l; }

say "waiting for extraction to finish ($(cached)/$EXPECTED cached)"

while true; do
  if grep -q "extraction finished" "$STATUS" 2>/dev/null; then
    say "extraction finished with $(cached) recordings cached; starting training"
    exec bash run_training_full.sh
  fi

  if [ -f "$FRAMES_LOG" ]; then
    age_min=$(( ( $(date +%s) - $(date -r "$FRAMES_LOG" +%s) ) / 60 ))
    if [ "$age_min" -ge "$STALE_MIN" ]; then
      say "$FRAMES_LOG has not moved for ${age_min} min - extraction looks dead ($(cached)/$EXPECTED cached)."
      say "restart the scheduler, or run run_training_full.sh by hand to train on what is cached."
      exit 1
    fi
  fi

  sleep 300
done
