import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VideoResults } from './VideoResults';
import { getMockHistory } from '../../services/api/analysisService';

describe('VideoResults', () => {
  it('shows a placeholder when no video is stored', () => {
    const result = getMockHistory()[0];
    render(<VideoResults result={result} onAnalyzeAnother={() => {}} />);
    expect(screen.getByText('original recording not stored')).toBeInTheDocument();
    expect(screen.getAllByText(new RegExp(result.steps[0].title)).length).toBeGreaterThan(0);
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
