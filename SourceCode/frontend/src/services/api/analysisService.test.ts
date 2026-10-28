import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { analyzeVideo, getMockHistory, fetchHistory, SCREEN_RECORDING_STEPS } from './analysisService';

// Answers each request by its method and path; anything unrouted gets a 500.
function mockFetchRoutes(routes: Record<string, { status: number; body: unknown }>) {
  return vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? 'GET';
    const key = Object.keys(routes).find((k) => {
      const [m, path] = k.split(' ');
      return m === method && url.endsWith(path);
    });
    const resp = key ? routes[key] : { status: 500, body: { detail: 'unexpected call' } };
    return Promise.resolve({
      ok: resp.status >= 200 && resp.status < 300,
      status: resp.status,
      statusText: resp.status < 300 ? 'OK' : 'Error',
      json: () => Promise.resolve(resp.body),
    } as Response);
  });
}

describe('getMockHistory', () => {
  it('returns entries whose stepCount matches their steps array', () => {
    const history = getMockHistory();
    expect(history.length).toBeGreaterThan(0);
    history.forEach((item) => {
      expect(item.stepCount).toBe(item.steps.length);
    });
  });
});

describe('analyzeVideo', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('uploads, runs, polls the job, maps the best model\'s results to steps, and completes', async () => {
    const results = [
      { label: 'git_operations', confidence: 0.92, probabilities: {}, model_name: 'svm', latency_ms: 5, start_time: 0, end_time: 5 },
      { label: 'coding_editing', confidence: 0.87, probabilities: {}, model_name: 'svm', latency_ms: 3, start_time: 5, end_time: 10 },
      { label: 'coding_editing', confidence: 0.6, probabilities: {}, model_name: 'knn', latency_ms: 2, start_time: 0, end_time: 10 },
    ];
    globalThis.fetch = mockFetchRoutes({
      'POST /sop-detector/jobs': { status: 200, body: { job_id: 'det-1' } },
      'POST /videos/upload': {
        status: 201,
        body: { id: 1, filename: 'abc_clip.mp4', original_filename: 'clip.mp4', status: 'uploaded', job_id: 42 },
      },
      'POST /jobs/42/run': { status: 200, body: { job_id: 42, status: 'processing' } },
      'GET /jobs/42': { status: 200, body: { id: 42, status: 'completed', progress_pct: 100, progress_stage: 'analysis complete' } },
      'GET /jobs/42/results': {
        status: 200,
        body: { job_id: 42, status: 'completed', results, model_comparison: [], best_model: 'svm' },
      },
    });

    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    const onProgress = vi.fn();
    const onComplete = vi.fn();
    analyzeVideo(file, 1, onProgress, onComplete);

    await vi.advanceTimersByTimeAsync(1500);

    expect(onComplete).toHaveBeenCalledTimes(1);
    const result = onComplete.mock.calls[0][0];
    expect(result.name).toBe('clip.mp4');
    expect(result.jobId).toBe('42');
    expect(result.bestModel).toBe('svm');
    // the SOP detector is switched off by default: the video is not sent to it
    expect(result.detectorJobId).toBeNull();
    expect(vi.mocked(globalThis.fetch).mock.calls.some(([url]) => String(url).includes('/sop-detector'))).toBe(false);
    expect(result.steps).toHaveLength(2);
    expect(result.steps[0].title).toBe('Performed Git operations');
    expect(result.steps[1].title).toBe('Edited code in the editor');
    expect(Object.keys(result.allResults).sort()).toEqual(['knn', 'svm']);
    expect(result.status).toBe('Complete');
    expect(onProgress).toHaveBeenLastCalledWith(100, 'analysis complete');
  });

  it('falls back to example steps and reports the backend error when the API fails', async () => {
    globalThis.fetch = vi.fn(() => Promise.reject(new Error('Network error')));

    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    const onProgress = vi.fn();
    const onComplete = vi.fn();
    analyzeVideo(file, 1, onProgress, onComplete);

    await vi.advanceTimersByTimeAsync(1500);

    expect(onComplete).toHaveBeenCalledTimes(1);
    const result = onComplete.mock.calls[0][0];
    expect(result.steps).toHaveLength(SCREEN_RECORDING_STEPS.length);
    expect(result.summary).toContain('Backend error — Network error');
    expect(result.detectorJobId).toBeNull();
    expect(onProgress).toHaveBeenLastCalledWith(100, 'offline fallback');
  });

  it('cancel aborts the fetch and stops progress', async () => {
    globalThis.fetch = vi.fn(() => new Promise<Response>(() => {}));

    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    const onProgress = vi.fn();
    const onComplete = vi.fn();
    const handle = analyzeVideo(file, 5, onProgress, onComplete);

    await vi.advanceTimersByTimeAsync(400);
    handle.cancel();
    const callsBefore = onProgress.mock.calls.length;

    await vi.advanceTimersByTimeAsync(2000);
    expect(onProgress.mock.calls.length).toBe(callsBefore);
    expect(onComplete).not.toHaveBeenCalled();
  });
});

describe('fetchHistory', () => {
  afterEach(() => vi.restoreAllMocks());

  it('returns mapped video entries from the backend', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve([
            { id: 1, filename: 'abc.mp4', original_filename: 'demo.mp4', file_size_bytes: 1000, duration_seconds: 120, status: 'uploaded' },
          ]),
      } as Response),
    );
    const result = await fetchHistory();
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('demo.mp4');
    expect(result[0].duration).toBe('2:00');
  });

  it('returns empty array on network error', async () => {
    globalThis.fetch = vi.fn(() => Promise.reject(new Error('fail')));
    const result = await fetchHistory();
    expect(result).toEqual([]);
  });
});
