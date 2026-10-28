import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';

const { mockSteps, mockHistoryEntries } = vi.hoisted(() => {
  const mockSteps = [
    { n: 1, time: '0:00-0:05', title: 'Mock step', description: 'mock description' },
  ];
  const noModels = { modelComparison: [], bestModel: null, allResults: {} };
  const mockHistoryEntries = [
    { id: 'h1', name: 'onboarding-demo.mov', date: 'Aug 5, 2026', duration: '2:14', stepCount: 1, status: 'Complete' as const, videoUrl: null, summary: 'A new engineer clones the starter repo.', steps: mockSteps, ...noModels },
    { id: 'h2', name: 'bug-repro.mp4', date: 'Aug 3, 2026', duration: '0:58', stepCount: 1, status: 'Complete' as const, videoUrl: null, summary: 'A reported bug is reproduced.', steps: mockSteps, ...noModels },
    { id: 'h3', name: 'deploy-walkthrough.webm', date: 'Jul 29, 2026', duration: '3:02', stepCount: 1, status: 'Complete' as const, videoUrl: null, summary: 'A production deploy.', steps: mockSteps, ...noModels },
  ];
  return { mockSteps, mockHistoryEntries };
});

vi.mock('./services/api/analysisService', () => ({
  getMockHistory: vi.fn(() => [...mockHistoryEntries]),
  fetchHistory: vi.fn(() => Promise.resolve([...mockHistoryEntries])),
  analyzeVideo: vi.fn((_file: File, _dur: number, onProgress: (pct: number) => void, onComplete: (r: unknown) => void) => {
    setTimeout(() => {
      onProgress(100);
      onComplete({
        id: '999', name: _file.name, date: 'Today', duration: '0:05',
        stepCount: 1, status: 'Complete', videoUrl: 'blob:mock',
        summary: 'Test analysis complete.', steps: mockSteps,
        modelComparison: [], bestModel: null, allResults: {},
      });
    }, 100);
    return { cancel: vi.fn() };
  }),
  SCREEN_RECORDING_STEPS: mockSteps,
}));

import App from './App';

describe('App', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('walks through upload -> analyzing -> results', async () => {
    render(<App />);
    expect(screen.getByText('Drop a video here, or click to browse')).toBeInTheDocument();

    const file = new File(['x'], 'session.mp4', { type: 'video/mp4' });
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    act(() => {
      fireEvent.change(input, { target: { files: [file] } });
    });
    expect(screen.getByText('Analysing your recording')).toBeInTheDocument();

    // the result arrives at 100 ms; the progress animation then runs to 100% before the results show.
    // Step the clock so each re-render can schedule the animation's next timer.
    for (let i = 0; i < 20; i++) {
      await act(async () => { vi.advanceTimersByTime(500); });
    }
    expect(screen.getByText('session.mp4', { selector: 'h1' })).toBeInTheDocument();
    expect(screen.getByText('Analyze another video')).toBeInTheDocument();
  });

  it('shows the history loaded from the backend and can open an entry', async () => {
    render(<App />);
    await act(async () => {});
    fireEvent.click(screen.getByText('History'));
    expect(screen.getByText('onboarding-demo.mov')).toBeInTheDocument();

    const viewButtons = screen.getAllByText('View');
    fireEvent.click(viewButtons[0]);
    expect(screen.getByText('onboarding-demo.mov', { selector: 'h1' })).toBeInTheDocument();
  });

  it('returns to upload from results', async () => {
    render(<App />);
    await act(async () => {});
    fireEvent.click(screen.getByText('History'));
    fireEvent.click(screen.getAllByText('View')[0]);
    fireEvent.click(screen.getByText('Analyze another video'));
    expect(screen.getByText('Drop a video here, or click to browse')).toBeInTheDocument();
  });
});
