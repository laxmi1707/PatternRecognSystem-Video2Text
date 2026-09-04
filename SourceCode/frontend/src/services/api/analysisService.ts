import type { AnalysisResult, SearchResultItem, WorkflowStep } from '../../types/analysis';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
export const isRealApi = Boolean(API_BASE_URL);

export const SCREEN_RECORDING_STEPS: WorkflowStep[] = [
  { n: 1, time: '0:00-0:07', title: 'Opened the code editor', description: 'The project folder loads in the editor with the file tree visible in the sidebar.' },
  { n: 2, time: '0:07-0:16', title: 'Opened the integrated terminal', description: 'A terminal panel opens at the bottom of the editor window.' },
  { n: 3, time: '0:16-0:29', title: 'Ran a shell command', description: '"git pull origin main" is typed and run, pulling the latest changes.' },
  { n: 4, time: '0:29-0:58', title: 'Installed dependencies', description: '"npm install" runs in the terminal, updating the project\'s packages.' },
  { n: 5, time: '0:58-1:12', title: 'Opened a browser tab', description: 'A new tab opens and navigates to localhost:3000.' },
  { n: 6, time: '1:12-1:30', title: 'Copied and pasted a value', description: 'A key is copied from the browser tab and pasted into the .env file back in the editor.' },
  { n: 7, time: '1:30-1:47', title: 'Verified the result', description: 'The dev server restarts and the running app is reviewed in the browser.' },
];

export function getMockHistory(): AnalysisResult[] {
  return [
    {
      id: 'h1', name: 'onboarding-demo.mov', date: 'Aug 5, 2026', duration: '2:14', stepCount: 4,
      status: 'Complete', videoUrl: null, category: 'coding_editing',
      summary: 'A new engineer clones the starter repo, installs dependencies, and runs the app for the first time.',
      steps: [
        { n: 1, time: '0:00-0:18', title: 'Cloned the starter repository', description: '"git clone" is run in a fresh terminal window.' },
        { n: 2, time: '0:18-0:52', title: 'Installed dependencies', description: '"npm install" runs, pulling down the project\'s packages.' },
        { n: 3, time: '0:52-1:40', title: 'Configured environment variables', description: 'A .env file is created and filled in with local credentials.' },
        { n: 4, time: '1:40-2:14', title: 'Started the dev server', description: '"npm run dev" starts the app, opened and reviewed in the browser.' },
      ],
    },
    {
      id: 'h2', name: 'bug-repro.mp4', date: 'Aug 3, 2026', duration: '0:58', stepCount: 4,
      status: 'Complete', videoUrl: null, category: 'debugging',
      summary: 'A reported bug is reproduced by navigating to a settings page and triggering a failing action.',
      steps: [
        { n: 1, time: '0:00-0:11', title: 'Opened the app in the browser', description: 'The staging environment loads in a new tab.' },
        { n: 2, time: '0:11-0:27', title: 'Navigated to the settings page', description: 'The user opens Settings from the left sidebar.' },
        { n: 3, time: '0:27-0:44', title: 'Triggered the failing action', description: 'Clicking "Save" produces an error toast.' },
        { n: 4, time: '0:44-0:58', title: 'Opened developer tools', description: 'The console is opened to inspect the error.' },
      ],
    },
    {
      id: 'h3', name: 'deploy-walkthrough.webm', date: 'Jul 29, 2026', duration: '3:02', stepCount: 5,
      status: 'Complete', videoUrl: null, category: 'jenkins_ci_cd',
      summary: 'A production deploy is walked through, from branch merge to live verification.',
      steps: [
        { n: 1, time: '0:00-0:24', title: 'Merged the release branch', description: 'A pull request is merged into main.' },
        { n: 2, time: '0:24-1:10', title: 'Triggered the deploy pipeline', description: 'The CI dashboard shows the build starting.' },
        { n: 3, time: '1:10-2:05', title: 'Watched the build complete', description: 'Build and deploy stages finish successfully.' },
        { n: 4, time: '2:05-2:40', title: 'Opened the production URL', description: 'The live site loads in a new browser tab.' },
        { n: 5, time: '2:40-3:02', title: 'Verified the change', description: 'The updated feature is checked on the live site.' },
      ],
    },
  ];
}

/** Fetches the real backend's job list. Only call when `isRealApi` is true. */
export async function fetchHistory(): Promise<AnalysisResult[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/jobs`);
  if (!res.ok) throw new Error(`Failed to load history (HTTP ${res.status})`);
  return (await res.json()) as AnalysisResult[];
}

const MOCK_SEARCH_RESULTS: SearchResultItem[] = [
  { jobId: 'h3', videoName: 'deploy-walkthrough.webm', snippet: 'The CI dashboard shows the build starting.', score: 0.82 },
  { jobId: 'h1', videoName: 'onboarding-demo.mov', snippet: 'A .env file is created and filled in with local credentials.', score: 0.41 },
];

/** Real backend: POST /api/v1/search. Mock mode: a couple of canned results. */
export async function searchVideos(query: string): Promise<SearchResultItem[]> {
  if (!isRealApi) return query.trim() ? MOCK_SEARCH_RESULTS : [];
  const res = await fetch(`${API_BASE_URL}/api/v1/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Search failed (HTTP ${res.status})`);
  const data = (await res.json()) as { results: SearchResultItem[] };
  return data.results;
}

export interface AnalyzeHandle {
  cancel: () => void;
}

/** Wire shape the backend speaks (see SourceCode/backend/app/schemas/analysis.py). */
interface JobStatusResponse {
  status: 'processing' | 'complete' | 'failed';
  progress: number;
  error: string | null;
}

export type AnalysisPhase = 'uploading' | 'processing';

function simulateAnalysis(
  file: File,
  durationSeconds: number,
  onProgress: (pct: number) => void,
  onComplete: (result: AnalysisResult) => void,
  onPhaseChange?: (phase: AnalysisPhase) => void
): AnalyzeHandle {
  onPhaseChange?.('processing');
  const videoUrl = URL.createObjectURL(file);
  let progress = 0;
  const tickMs = 180;
  const stepPct = 100 / ((durationSeconds * 1000) / tickMs);
  const timer = setInterval(() => {
    progress = Math.min(100, progress + stepPct);
    onProgress(progress);
    if (progress >= 100) {
      clearInterval(timer);
      const steps = SCREEN_RECORDING_STEPS;
      const last = steps[steps.length - 1];
      onComplete({
        id: String(Date.now()),
        name: file.name,
        date: 'Today',
        duration: last.time.split('-')[1],
        stepCount: steps.length,
        status: 'Complete',
        videoUrl,
        category: 'coding_editing',
        summary: 'The recording shows a developer pulling the latest changes, installing dependencies, and verifying the app in the browser.',
        steps,
      });
    }
  }, tickMs);
  return { cancel: () => clearInterval(timer) };
}

function toMessage(err: unknown): string {
  if (err instanceof Error) return err.name === 'AbortError' ? 'Cancelled' : err.message;
  return 'Analysis failed';
}

function runRealAnalysis(
  file: File,
  onProgress: (pct: number) => void,
  onComplete: (result: AnalysisResult) => void,
  onError: (message: string) => void,
  onPhaseChange?: (phase: AnalysisPhase) => void
): AnalyzeHandle {
  const controller = new AbortController();
  let pollTimer: ReturnType<typeof setInterval> | undefined;
  let cancelled = false;

  const fail = (message: string) => {
    if (cancelled) return;
    if (pollTimer) clearInterval(pollTimer);
    onError(message);
  };

  onPhaseChange?.('uploading');

  (async () => {
    try {
      const form = new FormData();
      form.append('file', file);
      const uploadRes = await fetch(`${API_BASE_URL}/api/v1/videos/upload`, {
        method: 'POST',
        body: form,
        signal: controller.signal,
      });
      if (!uploadRes.ok) {
        fail(`Upload failed (HTTP ${uploadRes.status})`);
        return;
      }
      const { id } = (await uploadRes.json()) as { id: string };
      if (cancelled) return;
      onPhaseChange?.('processing');

      pollTimer = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/api/v1/jobs/${id}`, {
            signal: controller.signal,
          });
          if (!res.ok) {
            fail(`Status check failed (HTTP ${res.status})`);
            return;
          }
          const data = (await res.json()) as JobStatusResponse;
          onProgress(data.progress);
          if (data.status === 'complete') {
            if (pollTimer) clearInterval(pollTimer);
            const resultsRes = await fetch(`${API_BASE_URL}/api/v1/jobs/${id}/results`, {
              signal: controller.signal,
            });
            if (!resultsRes.ok) {
              fail(`Fetching results failed (HTTP ${resultsRes.status})`);
              return;
            }
            const result = (await resultsRes.json()) as AnalysisResult;
            if (!cancelled) onComplete(result);
          } else if (data.status === 'failed') {
            fail(data.error ?? 'Analysis failed');
          }
        } catch (err) {
          if (!cancelled) fail(toMessage(err));
        }
      }, 1000);
    } catch (err) {
      if (!cancelled) fail(toMessage(err));
    }
  })();

  return {
    cancel: () => {
      cancelled = true;
      controller.abort();
      if (pollTimer) clearInterval(pollTimer);
    },
  };
}

export function analyzeVideo(
  file: File,
  durationSeconds: number,
  onProgress: (pct: number) => void,
  onComplete: (result: AnalysisResult) => void,
  onError?: (message: string) => void,
  onPhaseChange?: (phase: AnalysisPhase) => void
): AnalyzeHandle {
  if (API_BASE_URL) {
    return runRealAnalysis(file, onProgress, onComplete, onError ?? (() => {}), onPhaseChange);
  }
  return simulateAnalysis(file, durationSeconds, onProgress, onComplete, onPhaseChange);
}
