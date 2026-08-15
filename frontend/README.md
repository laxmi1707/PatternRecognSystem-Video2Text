# Runbook frontend

React + TypeScript implementation of the video-analysis workflow UI (upload, analyzing, results, history), styled with the Broadsheet design system tokens.

## Structure
- `src/pages/` — Upload, Analyzing, Results, History screens
- `src/components/video/` — dropzone, progress, workflow steps, results view
- `src/components/common/` — NavBar
- `src/hooks/useVideoAnalysis.ts` — screen state machine + mock analysis flow
- `src/services/api/analysisService.ts` — mock analysis pipeline (swap for a real API call)
- `src/styles/broadsheet.css` — design system tokens/components (copied from the bound design system)

## Setup
```
npm install
npm run dev      # start dev server
npm run build    # production build
npm test         # run the test suite once (Vitest)
npm run test:watch
```

## Integrating into your existing `frontend/` project
Copy the contents of `src/` into your project's `src/`, merge `package.json` dependencies, and copy `vite.config.ts` test config into your existing Vite config (or your test runner's config) if you use one already.

## Notes
- The analysis pipeline is mocked (`analysisService.ts`) — it simulates progress and returns a fixed set of workflow steps. Replace `analyzeVideo` with a real upload + polling/websocket call to your backend when ready.
- `useVideoAnalysis`'s `analysisSeconds` argument controls the simulated analysis duration.
