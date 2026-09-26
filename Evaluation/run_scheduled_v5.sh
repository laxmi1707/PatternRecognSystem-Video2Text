#!/usr/bin/env bash
# Extract frame vectors around the owner's working hours.
#
#   21:00-07:00  5 workers x 4 threads = 20 threads   (the machine is free)
#   07:00-21:00  3 workers x 4 threads = 12 threads   (someone is using it)
#
# Why v5: the owner asked for 22 threads from 21:00, having been told that v4's
# measurement showed extra threads buying nothing (480 min at 24 threads gave
# 2.12 tasks/min against 2.36 at 12). That is their call; the night window is
# wider and busier again, and this run re-measures it at 4 threads per worker
# rather than v2's 6x4.
#
# 22 is not used exactly. The only split reaching it is 11 workers x 2 threads,
# and 11 processes would hold roughly 44 GB: six processes once drove committed
# memory to 71 of 72 GB. 5 x 4 stays under the 22 the owner allowed, keeps the
# 4-threads-per-worker ratio that measured better than 2, and holds ~20 GB.
#
# Why v3: v2 relied on ProcessPoolExecutor(max_tasks_per_child=12) to keep the
# workers from growing. On Python 3.14, spawn start method plus an initializer,
# that silently stops the pool once every worker has taken its quota - it hung
# at exactly workers x 12 tasks twice (6x12=72, 3x12=36), leaving the launcher
# alive with no workers and the machine idle. max_tasks_per_child is gone, and
# memory is reclaimed by restarting the whole command every CYCLE_MIN minutes
# instead. A restart costs one model load (under a minute) and the task in
# flight; everything cached is kept.
#
# Start:  nohup bash run_scheduled_v5.sh > logs/scheduler_v5.log 2>&1 &
# Stop:   powershell -ExecutionPolicy Bypass -File stop_extraction.ps1
#         (and kill this script, or it will start the next cycle)

cd "$(dirname "$0")"
PY=.venv/Scripts/python.exe
ROOT="C:/Users/joshua.y.NUSSTF/Desktop/DATA OF PRS/Video CUA collect"
LOG=logs/frames_sched_007.log
STATUS=logs/scheduler.status       # appended to; the completion line is read from it
CYCLE_MIN=45

free_gb() {
  powershell -NoProfile -Command \
    "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)" 2>/dev/null \
    | tr -d '\r'
}

seconds_until() {  # seconds until the next occurrence of HH:00
  local target=$1
  local now_s=$(( $(date +%H) * 3600 + $(date +%M) * 60 + $(date +%S) ))
  local tgt_s=$(( target * 3600 ))
  local diff=$(( tgt_s - now_s ))
  [ $diff -le 0 ] && diff=$(( diff + 86400 ))
  echo $diff
}

while true; do
  hour=$(date +%H); hour=${hour#0}
  if [ "$hour" -ge 21 ] || [ "$hour" -lt 7 ]; then
    workers=5; window="night"; to_switch=$(seconds_until 7)
  else
    workers=3; window="day";   to_switch=$(seconds_until 21)
  fi
  threads=4

  free=$(free_gb)
  if [ -n "$free" ] && [ "${free%.*}" -lt 12 ]; then
    workers=$(( workers / 2 ))
    echo "$(date '+%F %T') only ${free} GB free, halving to ${workers} workers" >> "$STATUS"
  fi

  # Stop at whichever comes first: the memory-reclaiming restart, or the
  # day/night switch.
  secs=$(( CYCLE_MIN * 60 ))
  [ "$to_switch" -lt "$secs" ] && secs=$to_switch

  echo "$(date '+%F %T') v3 $window: ${workers}x${threads} threads for $((secs / 60)) min (${free} GB free)" >> "$STATUS"

  V2K_MAX_THREADS=22 timeout "${secs}s" "$PY" -m v2k frames \
      --root "$ROOT" --workers "$workers" --threads "$threads" --no-parity-ocr >> "$LOG" 2>&1
  rc=$?

  # timeout kills the launcher; its workers are separate processes.
  powershell -NoProfile -ExecutionPolicy Bypass -File stop_extraction.ps1 >> "$STATUS" 2>&1

  if [ $rc -eq 0 ] && tail -40 "$LOG" | grep -q "done in"; then
    echo "$(date '+%F %T') extraction finished" >> "$STATUS"
    break
  fi
  if [ $rc -ne 0 ] && [ $rc -ne 124 ] && [ $rc -ne 143 ]; then
    echo "$(date '+%F %T') frames exited $rc - see $LOG" >> "$STATUS"
  fi
done
