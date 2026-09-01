import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AnalyzingProgress } from './AnalyzingProgress';

describe('AnalyzingProgress', () => {
  it('renders the file name and progress percentage', () => {
    render(<AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={42} />);
    expect(screen.getByText('clip.mp4')).toBeInTheDocument();
    expect(screen.getByText('42% - reading interface actions')).toBeInTheDocument();
    expect(screen.getByTestId('progress-fill')).toHaveStyle({ width: '42%' });
  });

  it('hides the preview video when showPreview is false', () => {
    const { container } = render(
      <AnalyzingProgress fileName="clip.mp4" videoUrl="blob:mock" progress={10} showPreview={false} />
    );
    expect(container.querySelector('video')).toBeNull();
  });

  it('shows uploading-specific copy when phase is uploading', () => {
    render(<AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={0} phase="uploading" />);
    expect(screen.getByText('Uploading your recording')).toBeInTheDocument();
    expect(screen.getByText('0% - sending your file')).toBeInTheDocument();
  });

  it('has no cancel button when onCancel is not provided', () => {
    render(<AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={10} />);
    expect(screen.queryByText('Cancel')).toBeNull();
  });

  it('calls onCancel when the cancel button is clicked', () => {
    const onCancel = vi.fn();
    render(<AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={10} onCancel={onCancel} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
