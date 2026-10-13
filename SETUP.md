# TRACE — Local Setup Guide
**NUS ISS M.Tech AIS — Pattern Recognition System (Group-21)**

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| PostgreSQL | 14+ | https://postgresql.org |
| Git | any | https://git-scm.com |

---

## 1. Clone the Repository

```bash
git clone git@github.com:YOUR_ORG/PatternRecognSystem-Video2Text.git
cd PatternRecognSystem-Video2Text
```

---

## 2. Database Setup (PostgreSQL)

```bash
psql -U postgres
```
```sql
CREATE DATABASE video2knowledge;
\q
```

---

## 3. Backend Setup

```bash
cd SourceCode/backend

# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

# Install all dependencies (core + ML)
pip install -e ".[ml,dev]"

# Copy environment config
cp .env.example .env               # edit DATABASE_URL if needed
```

Default `.env` values (edit if your PostgreSQL differs):
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/video2knowledge
```

### Run the Backend

**v1 models (HOG features — default):**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**v2 models (CNN features — better accuracy):**
```bash
FEATURE_BACKEND=cnn MODEL_DIR=./models/v2 uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> The `models/v2/` folder must be present. Copy it from a teammate who has trained models,
> or retrain (see Section 5).

Backend runs at: http://localhost:8000  
API docs at: http://localhost:8000/docs

---

## 4. Frontend Setup

```bash
cd SourceCode/frontend

npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## 5. (Optional) Retrain Models

Only needed if you want to retrain from scratch. Requires the dataset and ~15 hours on GPU.

```bash
cd SourceCode/backend
source .venv/bin/activate

# Full training (extracts features + trains all 16 models)
python -m app.train --dataset-root ./dataset --model-dir ./models/v2

# Fast retrain (skip feature extraction, reuse cached features)
python -m app.train --dataset-root ./dataset --model-dir ./models/v2 --load-features
```

---

## 6. Quick Test

1. Open http://localhost:5173
2. Upload any screen recording (`.mp4`)
3. Watch the analyzing progress — 6 stages
4. View classification results + generated SOP/Runbook

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `address already in use` on port 8000 | `lsof -ti:8000 \| xargs kill -9` |
| `address already in use` on port 5173 | `lsof -ti:5173 \| xargs kill -9` |
| PostgreSQL connection refused | Ensure PostgreSQL is running: `brew services start postgresql` |
| `ModuleNotFoundError` | Ensure venv is activated: `source .venv/bin/activate` |
| Models not found / poor accuracy | Copy `models/v2/` from a teammate or retrain |
| OCR slow on first run | EasyOCR downloads model weights on first use (~500MB) |
