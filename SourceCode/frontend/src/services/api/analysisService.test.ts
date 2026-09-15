import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { analyzeVideo, getMockHistory, fetchHistory, SCREEN_RECORDING_STEPS } from './analysisService';

function mockFetchSequence(responses: Array<{ status: number; body: unknown }>) {
  let callIndex = 0;
  return vi.fn(() => {
    const resp = responses[callIndex++] ?? { status: 500, body: { detail: 'unexpected call' } };
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

  it('calls upload then run, maps results to WorkflowSteps, and completes', async () => {
    const uploadResponse = {
      id: 1, filename: 'abc_clip.mp4', original_filename: 'clip.mp4', status: 'uploaded', job_id: 42,
    };
    const runResponse = {
      job_id: 42,
      status: 'completed',
      results: [
        { label: 'git_operations', confidence: 0.92, probabilities: {}, model_name: 'svm', latency_ms: 5 },
        { label: 'coding_editing', confidence: 0.87, probabilities: {}, model_name: 'svm', latency_ms: 3 },
      ],
    };
    globalThis.fetch = mockFetchSequence([
      { status: 201, body: uploadResponse },
      { status: 200, body: runResponse },
    ]);

    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    const onProgress = vi.fn();
    const onComplete = vi.fn();
    analyzeVideo(file, 1, onProgress, onComplete);

    await vi.advanceTimersByTimeAsync(1500);

    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(onComplete).toHaveBeenCalledTimes(1);
    const result = onComplete.mock.calls[0][0];
    expect(result.name).toBe('clip.mp4');
    expect(result.steps).toHaveLength(2);
    expect(result.steps[0].title).toBe('Performed Git operations');
    expect(result.steps[1].title).toBe('Edited code in the editor');
    expect(result.status).toBe('Complete');
    expect(onProgress).toHaveBeenLastCalledWith(100);
  });

  it('falls back to mock steps when the API fails', async () => {
    globalThis.fetch = vi.fn(() => Promise.reject(new Error('Network error')));

    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    const onProgress = vi.fn();
    const onComplete = vi.fn();
    analyzeVideo(file, 1, onProgress, onComplete);

    await vi.advanceTimersByTimeAsync(1500);

    expect(onComplete).toHaveBeenCalledTimes(1);
    const result = onComplete.mock.calls[0][0];
    expect(result.steps).toHaveLength(SCREEN_RECORDING_STEPS.length);
    expect(result.summary).toContain('Offline fallback');
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
