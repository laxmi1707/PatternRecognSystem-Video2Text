#!/bin/sh
# The container's command (Dockerfile). When the image has the SOP detector, start it in
# the background on 127.0.0.1:8100, and start it again if it stops; then run the backend,
# which forwards /sop-detector/* to it (app/routers/sop_detector.py). The detector lowers
# its own CPU priority, so the backend stays responsive while a video is being read.
if [ -x /opt/sop-detector/venv/bin/python ]; then
    (
        cd /opt/sop-detector || exit 0
        export SOP_DETECTOR_HOST=127.0.0.1 SOP_DETECTOR_PORT=8100 \
            SOP_DETECTOR_THREADS="${SOP_DETECTOR_THREADS:-2}" \
            SOP_DETECTOR_UPLOADS=/tmp/sop-detector-uploads \
            SOP_DETECTOR_PKL=/opt/sop-detector/models/sop_detector.pkl \
            EASYOCR_MODULE_PATH=/opt/sop-detector/.EasyOCR
        while true; do
            venv/bin/python sop_detector_service.py
            echo "SOP detector stopped (exit $?); starting it again in 10 s" >&2
            sleep 10
        done
    ) &
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
