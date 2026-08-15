import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VideoDropzone } from './VideoDropzone';

describe('VideoDropzone', () => {
  it('calls onFileSelected when a file is chosen via the input', () => {
    const onFileSelected = vi.fn();
    render(<VideoDropzone onFileSelected={onFileSelected} />);
    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    expect(onFileSelected).toHaveBeenCalledWith(file);
  });

  it('calls onFileSelected on drop', () => {
    const onFileSelected = vi.fn();
    render(<VideoDropzone onFileSelected={onFileSelected} />);
    const file = new File(['x'], 'dropped.mov', { type: 'video/quicktime' });
    const zone = screen.getByRole('button');
    fireEvent.drop(zone, { dataTransfer: { files: [file] } });
    expect(onFileSelected).toHaveBeenCalledWith(file);
  });

  it('toggles the dragover state', () => {
    const { container } = render(<VideoDropzone onFileSelected={() => {}} />);
    const zone = screen.getByRole('button');
    fireEvent.dragOver(zone);
    expect(zone).toHaveAttribute('data-dragover', 'true');
    fireEvent.dragLeave(zone);
    expect(zone).toHaveAttribute('data-dragover', 'false');
  });
});
