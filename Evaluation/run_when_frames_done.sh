#!/usr/bin/env bash
# Wait for the frame extraction to finish, then start the training.
#
# "Finished" means the scheduler wrote its own completion line - not that the
# cache stopped growing, which also happens at every day/night switch while the
# workers are being restarted.
#
# Liveness is judged by the extraction log's age rather than by looking for the
# process: Git Bash has no pgrep, and its `ps` shows only the executable, so
# every bash script on the machine looks alike. A task takes minutes at most,
# so a log untouched for STALE_MIN minutes means the run has died, and this
# stops instead of training on a half-filled cache.
#
# Start:  nohup bash run_when_frames_done.sh > logs/chain.log 2>&1 &

cd "$(dirname "$0")"
STATUS=logs/scheduler.status
FRAMES_LOG=logs/frames_sched_004.log
CACHE=cache/frames_v1_main-d866716
EXPECTED=6991
STALE_MIN=45

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
