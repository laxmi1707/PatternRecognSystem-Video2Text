# CPU-only image for serving (ECS Fargate has no GPU). Training on a GPU
# machine uses Dockerfile.gpu (docker-compose.yml).
#
# The SOP detector (SOP-detector/ at the repository root) runs beside the backend in this
# image when the build is given that folder, as .github/workflows/deploy-backend.yml does:
#     docker build --build-context sop-detector=../../SOP-detector .
# Without it the stage below stays empty: the image is the backend alone, and
# /sop-detector/* answers 503.
FROM scratch AS sop-detector

# The detector's folder without what the image does not need (its .dockerignore, plus
# the sample videos).
FROM python:3.11-slim-bookworm AS sop-detector-src
COPY --from=sop-detector / /src/
RUN cd /src && rm -rf .git .venv deploy docs reports samples weights cache/sop_service \
        docker-compose.yml \
 && find . -name __pycache__ -prune -exec rm -rf {} +

FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
# torch and torchvision come from the CPU wheel index first, so easyocr and
# ultralytics don't pull the multi-GB CUDA builds from PyPI.
RUN pip install --no-cache-dir --timeout=1200 --retries=10 \
    torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --timeout=1200 --retries=10 ".[ml,aws]"

RUN useradd --create-home --uid 1000 appuser

# Bake the EfficientNet-B0 weights (FEATURE_BACKEND=cnn) into the image, so a new task does
# not download them on its first job; torch looks for them under TORCH_HOME.
ENV TORCH_HOME=/app/.cache/torch
RUN python -c "import torchvision.models as m; m.efficientnet_b0(weights=m.EfficientNet_B0_Weights.IMAGENET1K_V1)"

# The SOP detector. Its models were fitted under Python 3.14 with the exact library
# versions in its requirements.txt, so it gets its own interpreter (installed by uv) and
# virtualenv, as its own Dockerfile installs them. warmup.py bakes its OCR, YOLO and
# ResNet weights into the image and runs it once, so a broken install fails the build.
COPY --from=sop-detector-src /src/ /opt/sop-detector/
RUN if [ -f /opt/sop-detector/requirements.txt ]; then \
        pip install --no-cache-dir uv==0.13.1 \
     && UV_PYTHON_INSTALL_DIR=/opt/python uv venv --seed --python 3.14 \
            --python-preference only-managed /opt/sop-detector/venv \
     && pip uninstall -y uv \
     && cd /opt/sop-detector \
     && venv/bin/pip install --no-cache-dir --timeout=1200 --retries=10 \
            --index-url https://download.pytorch.org/whl/cpu torch==2.10.0 torchvision==0.25.0 \
     && venv/bin/pip install --no-cache-dir --timeout=1200 --retries=10 -r requirements.txt \
     && venv/bin/pip uninstall -y opencv-python \
     && venv/bin/pip install --no-cache-dir --force-reinstall --no-deps \
            "$(grep '^opencv-python-headless==' requirements.txt)" \
     && SOP_DETECTOR_PKL=/opt/sop-detector/models/sop_detector.pkl \
        EASYOCR_MODULE_PATH=/opt/sop-detector/.EasyOCR venv/bin/python warmup.py; \
    fi

COPY start.sh ./

# Models are not baked into the image: MLService downloads them from S3
# (MODEL_S3_BUCKET / MODEL_S3_PREFIX, see app/config.py) into /app/models at startup.
# The detector writes only under its cache/ (uploads go to /tmp).
RUN mkdir -p /app/uploads /app/models /opt/sop-detector/cache \
    && chown -R appuser:appuser /app /opt/sop-detector/cache
USER appuser
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
# The backend on :8000, and the SOP detector beside it on 127.0.0.1:8100 when the image has it
CMD ["sh", "start.sh"]
