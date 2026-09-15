import type { AnalysisResult, WorkflowStep } from '../../types/analysis';
import type { VideoUploadResponse, VideoResponse, JobResultsResponse } from '../../types/api';
import { apiPost, apiPostFile, apiGet } from './client';
import { mapResultsToSteps } from './labelMap';
import { formatSeconds } from '../../utils/formatTime';

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
      status: 'Complete', videoUrl: null,
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
      status: 'Complete', videoUrl: null,
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
      status: 'Complete', videoUrl: null,
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

export interface AnalyzeHandle {
  cancel: () => void;
}

function buildSummary(labels: string[]): string {
  const uniqueLabels = [...new Set(labels)];
  const readable = uniqueLabels.map((l) => l.replace(/_/g, ' ')).slice(0, 4);
  if (readable.length === 0) return 'No activities were detected in this recording.';
  if (readable.length === 1) return `The recording shows activity classified as ${readable[0]}.`;
  const last = readable.pop()!;
  return `The recording shows activities including ${readable.join(', ')} and ${last}.`;
}

export function analyzeVideo(
  file: File,
  durationSeconds: number,
  onProgress: (pct: number) => void,
  onComplete: (result: AnalysisResult) => void,
  modelName?: string,
): AnalyzeHandle {
  const controller = new AbortController();
  const videoUrl = URL.createObjectURL(file);

  let progress = 0;
  const tickMs = 180;
  const maxSyntheticPct = 90;
  const stepPct = maxSyntheticPct / ((durationSeconds * 1000) / tickMs);
  const timer = setInterval(() => {
    if (controller.signal.aborted) {
      clearInterval(timer);
      return;
    }
    progress = Math.min(maxSyntheticPct, progress + stepPct);
    onProgress(Math.round(progress));
  }, tickMs);

  (async () => {
    try {
      const upload = await apiPostFile<VideoUploadResponse>(
        '/videos/upload', file,
        modelName ? { model_name: modelName } : undefined,
      );
      if (controller.signal.aborted) return;

      const jobResults = await apiPost<JobResultsResponse>(`/jobs/${upload.job_id}/run`);
      if (controller.signal.aborted) return;

      const steps = mapResultsToSteps(jobResults.results);

      clearInterval(timer);
      onProgress(100);

      const lastStep = steps[steps.length - 1];
      const summary = buildSummary(jobResults.results.map((r) => r.label));

      onComplete({
        id: String(upload.id),
        name: file.name,
        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
        duration: lastStep ? lastStep.time.split('-')[1] : '0:00',
        stepCount: steps.length,
        status: 'Complete',
        videoUrl,
        summary,
        steps,
      });
    } catch (err) {
      clearInterval(timer);
      if (controller.signal.aborted) return;
      console.error('Analysis API failed, falling back to mock:', err);
      onProgress(100);
      onComplete({
        id: String(Date.now()),
        name: file.name,
        date: 'Today',
        duration: SCREEN_RECORDING_STEPS[SCREEN_RECORDING_STEPS.length - 1].time.split('-')[1],
        stepCount: SCREEN_RECORDING_STEPS.length,
        status: 'Complete',
        videoUrl,
        summary:
          'The recording shows a developer pulling the latest changes, installing dependencies, and verifying the app in the browser. (Offline fallback — backend unavailable)',
        steps: SCREEN_RECORDING_STEPS,
      });
    }
  })();

  return {
    cancel: () => {
      controller.abort();
      clearInterval(timer);
    },
  };
}

export async function fetchHistory(): Promise<AnalysisResult[]> {
  try {
    const videos = await apiGet<VideoResponse[]>('/videos/');
    return videos.map((v) => ({
      id: String(v.id),
      name: v.original_filename,
      date: 'Earlier',
      duration: v.duration_seconds ? formatSeconds(v.duration_seconds) : '--',
      stepCount: 0,
      status: 'Complete' as const,
      videoUrl: null,
      summary: '',
      steps: [],
    }));
  } catch {
    return [];
  }
}
