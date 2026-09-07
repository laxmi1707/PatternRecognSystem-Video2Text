import type { ClassificationResult, SearchResultItem, SopReport, WorkflowStep } from '../../types/analysis';

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

/** Prototype SOP writeup -- not produced by a real LLM/RAG stage yet, so
 * every job gets the same canned content in mock mode (mirrors the backend
 * stub's behavior). */
const MOCK_SOP_REPORT: SopReport = {
  summary: 'The recording shows a developer pulling the latest changes, installing dependencies, and verifying the app in the browser.',
  steps: SCREEN_RECORDING_STEPS,
};

export function getMockHistory(): ClassificationResult[] {
  return [
    {
      id: 'h1', name: 'onboarding-demo.mov', date: 'Aug 5, 2026', duration: '2:14',
      status: 'Complete', videoUrl: null,
      label: 'coding_editing', confidence: 0.82,
      probabilities: { coding_editing: 0.82, documentation: 0.09, debugging: 0.05, other: 0.04 },
    },
    {
      id: 'h2', name: 'bug-repro.mp4', date: 'Aug 3, 2026', duration: '0:58',
      status: 'Complete', videoUrl: null,
      label: 'debugging', confidence: 0.74,
      probabilities: { debugging: 0.74, coding_editing: 0.15, other: 0.11 },
    },
    {
      id: 'h3', name: 'deploy-walkthrough.webm', date: 'Jul 29, 2026', duration: '3:02',
      status: 'Complete', videoUrl: null,
      label: 'jenkins_ci_cd', confidence: 0.68,
      probabilities: { jenkins_ci_cd: 0.68, docker_workflow: 0.18, aws_console: 0.09, other: 0.05 },
    },
  ];
}

/** Fetches the real backend's job list. Only call when `isRealApi` is true. */
export async function fetchHistory(): Promise<ClassificationResult[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/jobs`);
  if (!res.ok) throw new Error(`Failed to load history (HTTP ${res.status})`);
  return (await res.json()) as ClassificationResult[];
}

/** Real backend: GET /api/v1/jobs/{id}/sop. Mock mode: one canned report. */
export async function fetchSopReport(id: string): Promise<SopReport> {
  if (!isRealApi) return MOCK_SOP_REPORT;
  const res = await fetch(`${API_BASE_URL}/api/v1/jobs/${id}/sop`);
  if (!res.ok) throw new Error(`Failed to load report (HTTP ${res.status})`);
  return (await res.json()) as SopReport;
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

function fakeMockPrediction(filename: string): { label: string; confidence: number; probabilities: Record<string, number> } {
  const labels = ['git_operations', 'docker_workflow', 'kubernetes_ops', 'terraform_iac', 'aws_console', 'jenkins_ci_cd', 'coding_editing', 'debugging', 'documentation', 'other'];
  let hash = 0;
  for (let i = 0; i < filename.length; i++) hash = (hash * 31 + filename.charCodeAt(i)) >>> 0;
  const label = labels[hash % labels.length];
  const confidence = Math.round((0.55 + (hash % 41) / 100) * 100) / 100;
  const remaining = Math.round((1 - confidence) * 100) / 100;
  return { label, confidence, probabilities: { [label]: confidence, other: remaining } };
}

function simulateAnalysis(
  file: File,
  durationSeconds: number,
  onProgress: (pct: number) => void,
  onComplete: (result: ClassificationResult) => void,
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
      const { label, confidence, probabilities } = fakeMockPrediction(file.name);
      onComplete({
        id: String(Date.now()),
        name: file.name,
        date: 'Today',
        duration: SCREEN_RECORDING_STEPS[SCREEN_RECORDING_STEPS.length - 1].time.split('-')[1],
        status: 'Complete',
        videoUrl,
        label,
        confidence,
        probabilities,
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
  onComplete: (result: ClassificationResult) => void,
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
            const result = (await resultsRes.json()) as ClassificationResult;
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
  onComplete: (result: ClassificationResult) => void,
  onError?: (message: string) => void,
  onPhaseChange?: (phase: AnalysisPhase) => void
): AnalyzeHandle {
  if (API_BASE_URL) {
    return runRealAnalysis(file, onProgress, onComplete, onError ?? (() => {}), onPhaseChange);
  }
  return simulateAnalysis(file, durationSeconds, onProgress, onComplete, onPhaseChange);
}
