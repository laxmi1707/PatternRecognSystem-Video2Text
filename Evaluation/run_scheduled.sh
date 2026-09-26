#!/usr/bin/env bash
# Extract frame vectors around the owner's working hours.
#
#   23:00-07:00  6 workers x 4 threads = 24 threads   (the machine is free)
#   07:00-23:00  6 workers x 2 threads = 12 threads   (someone is using it)
#
# The worker count stays the same in both windows on purpose: threads are what
# make it faster, workers are what make it eat memory (each one holds easyocr,
# YOLO and ResNet). If memory is tight at a switch, this drops to 4 workers.
#
# At each switch the run is stopped and restarted with the new setting. Work is
# cached per task, so a switch costs at most the task in flight.
#
# Start:  nohup bash run_scheduled.sh > logs/scheduler.log 2>&1 &
# Stop:   powershell -ExecutionPolicy Bypass -File stop_extraction.ps1
#         (and kill this script, or it will start the next cycle)

cd "$(dirname "$0")"
PY=.venv/Scripts/python.exe
ROOT="C:/Users/joshua.y.NUSSTF/Desktop/DATA OF PRS/Video CUA collect"
LOG=logs/frames_sched_004.log
STATUS=logs/scheduler.status

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
    threads=4; window="night"; secs=$(seconds_until 7)
  else
    threads=2; window="day";   secs=$(seconds_until 23)
  fi

  workers=6
  free=$(free_gb)
  if [ -n "$free" ] && [ "${free%.*}" -lt 12 ]; then
    workers=4
    echo "$(date '+%F %T') only ${free} GB free, dropping to 4 workers" >> "$STATUS"
  fi

  echo "$(date '+%F %T') $window: ${workers}x${threads} threads for the next $((secs / 60)) min (${free} GB free)" >> "$STATUS"

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
