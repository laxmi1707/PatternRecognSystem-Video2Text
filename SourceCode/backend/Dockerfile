FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --timeout=1200 --retries=10 \
    torch --index-url https://download.pytorch.org/whl/cu124 && \
    pip install --timeout=1200 --retries=10 ".[ml]"

RUN useradd --create-home --uid 1000 appuser
COPY models ./models

RUN mkdir -p /app/uploads /app/models && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
ENV PYTHONUNBUFFERED=1 NVIDIA_VISIBLE_DEVICES=all NVIDIA_DRIVER_CAPABILITIES=compute,utility
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
