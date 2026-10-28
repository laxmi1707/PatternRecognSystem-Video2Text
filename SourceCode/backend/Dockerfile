# CPU-only image for serving (ECS Fargate has no GPU). Training on a GPU
# machine uses Dockerfile.gpu (docker-compose.yml).
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
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

# Models are not baked into the image: MLService downloads them from S3
# (MODEL_S3_BUCKET / MODEL_S3_PREFIX, see app/config.py) into /app/models at startup.
RUN mkdir -p /app/uploads /app/models && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
