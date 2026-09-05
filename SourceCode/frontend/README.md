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

## Setup

    npm install
    npm run dev          # http://localhost:5173
    npm run build        # Production build
    npm run test         # Run tests

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
