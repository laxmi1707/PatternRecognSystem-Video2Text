import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NavBar } from './NavBar';

describe('NavBar', () => {
  it('marks the active screen with aria-current', () => {
    render(<NavBar screen="history" onUpload={() => {}} onHistory={() => {}} />);
    expect(screen.getByText('History')).toHaveAttribute('aria-current', 'page');
    expect(screen.getByText('Upload')).not.toHaveAttribute('aria-current');
  });

  it('calls handlers on click', () => {
    const onUpload = vi.fn();
    const onHistory = vi.fn();
    render(<NavBar screen="upload" onUpload={onUpload} onHistory={onHistory} />);
    fireEvent.click(screen.getByText('History'));
    expect(onHistory).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Upload'));
    expect(onUpload).toHaveBeenCalledTimes(1);
  });
});
