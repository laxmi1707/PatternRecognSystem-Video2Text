import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VideoResults } from './VideoResults';
import { getMockHistory } from '../../services/api/analysisService';

describe('VideoResults', () => {
  it('shows a placeholder when there is neither a local video nor a backend id', () => {
    const result = { ...getMockHistory()[0], id: '', videoUrl: null };
    render(<VideoResults result={result} onAnalyzeAnother={() => {}} />);
    expect(screen.getByText('original recording not available')).toBeInTheDocument();
    expect(screen.getByText(result.name)).toBeInTheDocument();
  });

  it('streams a history entry from the backend when its local video is gone', () => {
    const result = { ...getMockHistory()[0], id: '7', videoUrl: null };
    const { container } = render(<VideoResults result={result} onAnalyzeAnother={() => {}} />);
    expect(container.querySelector('video')?.getAttribute('src')).toMatch(/\/videos\/7\/stream$/);
  });

  it('renders a video element when a videoUrl is present', () => {
    const result = { ...getMockHistory()[0], videoUrl: 'blob:mock' };
    const { container } = render(<VideoResults result={result} onAnalyzeAnother={() => {}} />);
    expect(container.querySelector('video')).not.toBeNull();
  });

  it('calls onAnalyzeAnother when the button is clicked', () => {
    const onAnalyzeAnother = vi.fn();
    render(<VideoResults result={getMockHistory()[0]} onAnalyzeAnother={onAnalyzeAnother} />);
    fireEvent.click(screen.getByText('Analyze another video'));
    expect(onAnalyzeAnother).toHaveBeenCalledTimes(1);
  });
});
