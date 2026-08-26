import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useVideoAnalysis } from './useVideoAnalysis';

describe('useVideoAnalysis', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('starts on the upload screen with mock history preloaded', () => {
    const { result } = renderHook(() => useVideoAnalysis(1));
    expect(result.current.screen).toBe('upload');
    expect(result.current.history.length).toBe(3);
  });

  it('moves upload -> analyzing -> results on file selection', () => {
    const { result } = renderHook(() => useVideoAnalysis(1));
    const file = new File(['x'], 'demo.mp4', { type: 'video/mp4' });

    act(() => { result.current.startAnalysis(file); });
    expect(result.current.screen).toBe('analyzing');
    expect(result.current.fileName).toBe('demo.mp4');

    act(() => { vi.advanceTimersByTime(1200); });
    expect(result.current.screen).toBe('results');
    expect(result.current.current?.name).toBe('demo.mp4');
    expect(result.current.history[0].name).toBe('demo.mp4');
  });

  it('viewHistory shows a past result without re-analyzing', () => {
    const { result } = renderHook(() => useVideoAnalysis(1));
    const item = result.current.history[1];
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
