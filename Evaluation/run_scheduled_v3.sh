#!/usr/bin/env bash
# Extract frame vectors around the owner's working hours.
#
#   23:00-07:00  6 workers x 4 threads = 24 threads   (the machine is free)
#   07:00-23:00  3 workers x 4 threads = 12 threads   (someone is using it)
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
# Start:  nohup bash run_scheduled_v3.sh > logs/scheduler_v3.log 2>&1 &
# Stop:   powershell -ExecutionPolicy Bypass -File stop_extraction.ps1
#         (and kill this script, or it will start the next cycle)

cd "$(dirname "$0")"
PY=.venv/Scripts/python.exe
ROOT="C:/Users/joshua.y.NUSSTF/Desktop/DATA OF PRS/Video CUA collect"
LOG=logs/frames_sched_005.log
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
  if [ "$hour" -ge 23 ] || [ "$hour" -lt 7 ]; then
    workers=6; window="night"; to_switch=$(seconds_until 7)
  else
    workers=3; window="day";   to_switch=$(seconds_until 23)
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

  V2K_MAX_THREADS=24 timeout "${secs}s" "$PY" -m v2k frames \
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
