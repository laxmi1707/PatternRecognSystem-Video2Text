import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

const { mockSteps, mockHistory } = vi.hoisted(() => {
  const mockSteps = [
    { n: 1, time: '0:00-0:05', title: 'Mock step', description: 'mock' },
  ];
  const mockHistory = [
    { id: 'h1', name: 'mock.mp4', date: 'Aug 1', duration: '1:00', stepCount: 1, status: 'Complete' as const, videoUrl: null, summary: 'mock', steps: mockSteps },
    { id: 'h2', name: 'mock2.mp4', date: 'Aug 2', duration: '2:00', stepCount: 1, status: 'Complete' as const, videoUrl: null, summary: 'mock2', steps: mockSteps },
    { id: 'h3', name: 'mock3.mp4', date: 'Aug 3', duration: '3:00', stepCount: 1, status: 'Complete' as const, videoUrl: null, summary: 'mock3', steps: mockSteps },
  ];
  return { mockSteps, mockHistory };
});

vi.mock('../services/api/analysisService', () => ({
  getMockHistory: vi.fn(() => [...mockHistory]),
  fetchHistory: vi.fn(() => Promise.resolve([...mockHistory])),
  analyzeVideo: vi.fn((_file: File, _dur: number, onProgress: (pct: number) => void, onComplete: (r: unknown) => void) => {
    setTimeout(() => {
      onProgress(100);
      onComplete({
        id: '999', name: _file.name, date: 'Today', duration: '0:05',
        stepCount: 1, status: 'Complete', videoUrl: 'blob:mock',
        summary: 'test', steps: mockSteps,
      });
    }, 100);
    return { cancel: vi.fn() };
  }),
  SCREEN_RECORDING_STEPS: mockSteps,
}));

import { useVideoAnalysis } from './useVideoAnalysis';

describe('useVideoAnalysis', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('starts on the upload screen and loads the history from the backend', async () => {
    const { result } = renderHook(() => useVideoAnalysis(1));
    expect(result.current.screen).toBe('upload');
    expect(result.current.history.length).toBe(0);

    await act(async () => {});
    expect(result.current.history.map(h => h.name)).toEqual(['mock.mp4', 'mock2.mp4', 'mock3.mp4']);
  });

  it('moves upload -> analyzing -> results on file selection', async () => {
    const { result } = renderHook(() => useVideoAnalysis(1));
    const file = new File(['x'], 'demo.mp4', { type: 'video/mp4' });

    act(() => { result.current.startAnalysis(file); });
    expect(result.current.screen).toBe('analyzing');
    expect(result.current.fileName).toBe('demo.mp4');

    // The result arrives, but the results screen waits for the progress animation to finish
    await act(async () => { vi.advanceTimersByTime(200); });
    expect(result.current.analysisReady).toBe(true);
    expect(result.current.screen).toBe('analyzing');

    act(() => { result.current.onAnimationDone(); });
    expect(result.current.screen).toBe('results');
    expect(result.current.current?.name).toBe('demo.mp4');
    expect(result.current.history[0].name).toBe('demo.mp4');
  });

  it('viewHistory shows a past result without re-analyzing', async () => {
    const { result } = renderHook(() => useVideoAnalysis(1));
    await act(async () => {});
    const item = result.current.history[1];
    expect(item).toBeDefined();
    act(() => { result.current.viewHistory(item); });
    expect(result.current.screen).toBe('results');
    expect(result.current.current).toBe(item);
  });

  it('goUpload resets progress and returns to upload', () => {
    const { result } = renderHook(() => useVideoAnalysis(1));
    act(() => { result.current.startAnalysis(new File(['x'], 'a.mp4')); });
    act(() => { result.current.goUpload(); });
    expect(result.current.screen).toBe('upload');
    expect(result.current.progress).toBe(0);
  });
});
