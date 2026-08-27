# Frontend — Video2Knowledge

**Layer 1 (Presentation)**

Owner: Joshua

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | React 18+ |
| Language | TypeScript |
| Build | Vite |
| Styling | CSS (broadsheet theme) |
| Hosting | AWS S3 + CloudFront |

## Structure
- `src/pages/` — Upload, Analyzing, Results, History screens
- `src/components/video/` — dropzone, progress, workflow steps, results view
- `src/components/common/` — NavBar
- `src/hooks/useVideoAnalysis.ts` — screen state machine + analysis flow (mock or real, see below)
- `src/services/api/analysisService.ts` — analysis pipeline: calls the real backend when `VITE_API_BASE_URL` is set, otherwise falls back to a mock
- `src/styles/broadsheet.css` — design system tokens/components (copied from the bound design system)

## Setup

    npm install
    cp .env.example .env   # optional - see "Backend wiring" below
    npm run dev            # http://localhost:5173
    npm run build          # Production build
    npm run test           # Run tests
    npm run test:watch

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Upload | / | Video upload via drag-and-drop |
| Analyzing | /analyzing | Real-time analysis progress |
| Results | /results | Classification results + workflow steps |
| History | /history | Browse past analyses |

## Components

| Component | Description |
|-----------|-------------|
| VideoDropzone | Drag-and-drop video upload |
| AnalyzingProgress | Progress bar during ML processing |
| VideoResults | Classification output display |
| WorkflowSteps | Step-by-step workflow timeline |
| NavBar | Top navigation |

## API Integration

| Service Call | Backend Endpoint |
|-------------|-----------------|
| upload() | POST /api/v1/videos/upload |
| getStatus() | GET /api/v1/jobs/{id} |
| getResults() | GET /api/v1/jobs/{id}/results |

## Backend wiring
- With no `VITE_API_BASE_URL` set, `analysisService.ts` runs entirely on mocked data (simulated progress, fixed workflow steps) — no backend needed.
- Set `VITE_API_BASE_URL` (e.g. `http://localhost:8000`) to switch to real calls, matching the API Integration table above:
  1. `POST {base}/api/v1/videos/upload` — multipart upload, returns `{ id }`
  2. `GET {base}/api/v1/jobs/{id}` — polled every second, returns `{ status, progress, error }`
  3. Once `status` is `complete`, `GET {base}/api/v1/jobs/{id}/results` is fetched once for the `AnalysisResult` — see `SourceCode/backend/app/schemas/analysis.py` for its exact shape
- `useVideoAnalysis`'s `analysisSeconds` argument only affects the mock path's simulated duration.
