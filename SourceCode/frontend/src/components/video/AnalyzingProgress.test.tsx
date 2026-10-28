import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { AnalyzingProgress } from './AnalyzingProgress';

describe('AnalyzingProgress', () => {
  afterEach(() => vi.useRealTimers());

  it('renders the file name and eases the bar up to the progress percentage', () => {
    vi.useFakeTimers();
    render(<AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={42} stage="reading interface actions" />);
    expect(screen.getByText('clip.mp4')).toBeInTheDocument();
    expect(screen.getByText('0% — reading interface actions')).toBeInTheDocument();

    act(() => { vi.advanceTimersByTime(5000); });
    expect(screen.getByText('42% — reading interface actions')).toBeInTheDocument();
    expect(screen.getByTestId('progress-fill')).toHaveStyle({ width: '42%' });
  });

  it('fast-forwards to 100% and calls onAnimationDone once the analysis is ready', () => {
    vi.useFakeTimers();
    const onAnimationDone = vi.fn();
    render(
      <AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={100} analysisReady onAnimationDone={onAnimationDone} />
    );

    act(() => { vi.advanceTimersByTime(10000); });
    expect(screen.getByText('100% — Analysis complete ✓')).toBeInTheDocument();
    expect(onAnimationDone).toHaveBeenCalledTimes(1);
  });

  it('hides the preview video when showPreview is false', () => {
    const { container } = render(
      <AnalyzingProgress fileName="clip.mp4" videoUrl="blob:mock" progress={10} showPreview={false} />
    );
    expect(container.querySelector('video')).toBeNull();
  });
});
