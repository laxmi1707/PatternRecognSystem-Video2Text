# The SOP detector service as a container. Build from the repository root:
#     docker build -t sop-detector .
FROM python:3.14-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only torch: the PyPI wheels for Linux pull in several GB of CUDA libraries.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.10.0 torchvision==0.25.0
COPY requirements.txt .
# ultralytics pulls in the GUI build of OpenCV; both share the cv2 package, so remove it
# and reinstall the headless build over the top.
RUN pip install --no-cache-dir -r requirements.txt \
 && pip uninstall -y opencv-python \
 && pip install --no-cache-dir --force-reinstall --no-deps opencv-python-headless==5.0.0.93 \
 && python -c "import cv2; print('cv2', cv2.__version__)"

COPY . /app/

# Every fitted model comes from this one file (detector/model_file.py).
ENV SOP_DETECTOR_PKL=/app/models/sop_detector.pkl

# Download the OCR, YOLO and ResNet weights now, so a task starts without the internet,
# and fail the build if any model does not load.
RUN python warmup.py

ENV SOP_DETECTOR_HOST=0.0.0.0 \
    SOP_DETECTOR_PORT=8000 \
    SOP_DETECTOR_THREADS=4 \
    SOP_DETECTOR_UPLOADS=/tmp/uploads \
    PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["python", "sop_detector_service.py"]
