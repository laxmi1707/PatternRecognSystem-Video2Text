import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
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
});
