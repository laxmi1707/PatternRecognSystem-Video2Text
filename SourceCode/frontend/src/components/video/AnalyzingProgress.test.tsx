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

  it('distinguishes uploading from processing', () => {
    render(<AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={10} phase="uploading" />);
    expect(screen.getByText('Uploading your recording')).toBeInTheDocument();
    expect(screen.getByText('10% - sending your file')).toBeInTheDocument();
  });

  it('exposes the progress bar to assistive technology', () => {
    render(<AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={42} />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '42');
    expect(bar).toHaveAttribute('aria-valuemin', '0');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('offers a cancel button only when a handler is given', () => {
    const onCancel = vi.fn();
    const { rerender } = render(
      <AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={10} onCancel={onCancel} />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onCancel).toHaveBeenCalledTimes(1);

    rerender(<AnalyzingProgress fileName="clip.mp4" videoUrl={null} progress={10} />);
    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument();
  });
});
