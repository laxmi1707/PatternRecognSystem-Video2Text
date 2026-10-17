# How to Run Video2Knowledge

## Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://docs.docker.com/get-docker/) with Docker Compose
- Minimum **8 GB RAM** allocated to Docker

## Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/laxmi1707/PatternRecognSystem-Video2Text.git
cd PatternRecognSystem-Video2Text

# Start all services
docker compose up --build
```

First build takes 10-15 minutes (downloads PyTorch, YOLO, EasyOCR models).

Once you see all three services running:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### Upload and Analyze

1. Open http://localhost:5173
2. Drop a screen recording video (MP4, MOV, or WebM)
3. Wait for analysis — all 14 classifiers run on your video
4. View the Model Comparison table and workflow steps

### Stop

```bash
docker compose down
```

## Docker Memory Configuration

The backend requires ~4-6 GB for YOLO + EasyOCR + PyTorch + classifiers.

### Docker Desktop (macOS/Windows)

1. Open Docker Desktop
2. Go to **Settings** (gear icon) → **Resources**
3. Set **Memory** to **8 GB** (minimum)
4. Click **Apply & restart**

### Linux

Docker uses host memory directly — no configuration needed if you have 8 GB+ RAM.

## Local Development (without Docker)

### Backend

```bash
cd SourceCode/backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[ml,dev]"

# Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Note**: On macOS, YOLO + PyTorch cause an OpenMP crash. The backend auto-detects macOS and uses synthetic features. Real feature extraction works in Docker (Linux) or on a Linux machine.

### Frontend

```bash
cd SourceCode/frontend

# Install dependencies
npm install

# Start dev server
npx vite --host 127.0.0.1 --port 5173
```

### Database

Local development uses SQLite by default (no setup needed). Docker uses PostgreSQL with pgvector.

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5173 | React UI (Vite dev / nginx in Docker) |
| Backend | 8000 | FastAPI + ML pipeline |
| Database | 5434 | PostgreSQL 16 + pgvector (Docker only) |

## Architecture

```
Upload Video → Feature Extraction → 14 Classifiers → Model Comparison
                    │
    ┌───────────────┼───────────────┐
    │               │               │
  OCR (EasyOCR)  UI (YOLOv8)  Visual (OpenCV)
  50 features    30 features   40 features
                                    │
                            Interaction (action log)
                              30 features
                                    │
                        ┌───────────┴───────────┐
                        │    150-dim vector      │
                        └───────────┬───────────┘
                                    │
            ┌───────────┬───────────┼───────────┬───────────┐
         Tier 1      Tier 2     Tier 3
      Classical ML  Deep Learning  Ensemble
       (7 models)   (4 models)    (3 models)
```

## Model Training

Models must be trained on the CUA-Suite dataset before the system can produce meaningful results. Without training, classifiers run on synthetic (random) data.

### Dataset

The project uses [CUA-Suite (VideoCUA)](https://huggingface.co/datasets/ServiceNow/VideoCUA) by ServiceNow (MIT license) — 7,021 tasks, 6,991 videos, ~48 GB.

Download the dataset:

```bash
pip install huggingface_hub
hf download ServiceNow/VideoCUA --local-dir ./dataset/VideoCUA --repo-type dataset
```

### Train Locally (existing subset or full dataset)

```bash
cd SourceCode/backend

# Train on existing subset (~80 tasks)
# Use --skip-deep on macOS to avoid YOLO/PyTorch crash
.venv/bin/python -m app.train --dataset-root ../../dataset --model-dir ./models --skip-deep

# Train on full downloaded dataset
.venv/bin/python -m app.train --dataset-root ../../dataset/VideoCUA --model-dir ./models --skip-deep
```

After training, the backend loads saved models automatically on startup.

### Train on AWS EC2 (recommended for full dataset)

The full 48 GB dataset takes 8-12 hours to train. Use a cloud server for faster processing.

```bash
# 1. Launch EC2 instance
#    - AMI: Ubuntu 24.04
#    - Instance type: t3.xlarge (4 vCPU, 16 GB RAM) — ~$0.17/hr
#    - Storage: 100 GB EBS (gp3)
#    - Security group: open port 22 (SSH), 8000 (API), 5173 (Frontend)

# 2. SSH into the instance
ssh -i your-key.pem ubuntu@<ec2-public-ip>

# 3. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# 4. Clone the repository
git clone https://github.com/laxmi1707/PatternRecognSystem-Video2Text.git
cd PatternRecognSystem-Video2Text

# 5. Download the full CUA-Suite dataset
sudo apt install -y python3-pip
pip install huggingface_hub
hf download ServiceNow/VideoCUA --local-dir ./dataset/VideoCUA --repo-type dataset

# 6. Build the backend container
docker compose build backend

# 7. Start database and run training (all 14 models — no --skip-deep on Linux)
docker compose up -d db
docker compose run --rm backend python -m app.train \
    --dataset-root /app/dataset \
    --model-dir /app/models

# 8. After training, start the full stack
docker compose up -d

# 9. Access the app
#    Frontend: http://<ec2-public-ip>:5173
#    Backend:  http://<ec2-public-ip>:8000/docs

# 10. When done, stop the instance to save costs
#     (models are saved in the Docker volume)
```

**Estimated cost**: ~$1.50-2.00 for full dataset training on t3.xlarge.

### Train on Google Colab (free, limited)

Google Colab provides free GPU access (up to ~12 hours per session).

1. Go to [Google Colab](https://colab.research.google.com/)
2. Create a new notebook
3. Set runtime to **GPU** (Runtime → Change runtime type → T4 GPU)
4. Run the following cells:

```python
# Cell 1: Clone repo and install dependencies
!git clone https://github.com/laxmi1707/PatternRecognSystem-Video2Text.git
%cd PatternRecognSystem-Video2Text/SourceCode/backend
!pip install -e ".[ml]" -q

# Cell 2: Download dataset (full or subset)
!pip install huggingface_hub -q
!hf download ServiceNow/VideoCUA --local-dir ../../dataset/VideoCUA --repo-type dataset

# Cell 3: Run training (all 14 models — Linux, no crash)
!python -m app.train --dataset-root ../../dataset/VideoCUA --model-dir ./models

# Cell 4: Download trained models to your local machine
!zip -r /content/trained_models.zip ./models/
from google.colab import files
files.download('/content/trained_models.zip')
```

5. After downloading `trained_models.zip`, extract it into `SourceCode/backend/models/` on your local machine
6. Start the backend — it will load the pre-trained models automatically

**Limitations**: Colab sessions timeout after ~12 hours. For the full 48 GB dataset, the download + training may exceed this limit. Use a smaller subset or AWS EC2 for the full dataset.

### Training Output

The training script prints a comparison table:

```
================================================================================
MODEL COMPARISON (sorted by F1 macro)
================================================================================
  #  Model                 Tier          Accuracy    F1 Macro     Latency     Train
--------------------------------------------------------------------------------
  1  random_forest         tier1           0.8491      0.6583      27.6ms      0.1s
  2  decision_tree         tier1           0.8868      0.5808       0.2ms      0.0s
  3  svm                   tier1           0.7925      0.4964       1.5ms      0.0s
  ...
================================================================================
```

Trained models are saved to `./models/` and loaded automatically when the backend starts.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend OOM in Docker | Increase Docker memory to 8 GB |
| Python crash on macOS | Expected — use Docker for real feature extraction |
| Port 5432 already in use | Change db port in docker-compose.yml |
| Frontend shows "backend unavailable" | Check backend is running: `curl http://localhost:8000/health` |
| EasyOCR download slow on first run | Wait — models download once and are cached |
