import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { analyzeVideo, getMockHistory } from './analysisService';

describe('getMockHistory', () => {
  it('returns entries whose label appears in their own probabilities', () => {
    const history = getMockHistory();
    expect(history.length).toBeGreaterThan(0);
    history.forEach(item => {
      expect(item.probabilities[item.label]).toBe(item.confidence);
    });
  });
});

describe('analyzeVideo', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('reports progress up to 100 and completes with a classification', () => {
    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    const onProgress = vi.fn();
    const onComplete = vi.fn();
    analyzeVideo(file, 1, onProgress, onComplete);

    vi.advanceTimersByTime(1200);

    expect(onComplete).toHaveBeenCalledTimes(1);
    const result = onComplete.mock.calls[0][0];
    expect(result.name).toBe('clip.mp4');
    expect(typeof result.label).toBe('string');
    expect(result.confidence).toBeGreaterThan(0);
    expect(result.confidence).toBeLessThanOrEqual(1);
    expect(onProgress).toHaveBeenLastCalledWith(100);
  });

  it('cancel stops further progress callbacks', () => {
    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    const onProgress = vi.fn();
    const onComplete = vi.fn();
    const handle = analyzeVideo(file, 5, onProgress, onComplete);
    vi.advanceTimersByTime(200);
    handle.cancel();
    const callsBefore = onProgress.mock.calls.length;
    vi.advanceTimersByTime(2000);
    expect(onProgress.mock.calls.length).toBe(callsBefore);
    expect(onComplete).not.toHaveBeenCalled();
  });
});
