import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NavBar } from './NavBar';

const noop = () => {};

describe('NavBar', () => {
  it('marks the active screen with aria-current', () => {
    render(
      <NavBar screen="history" onUpload={noop} onHistory={noop} onDashboard={noop} onSearch={noop} />,
    );
    expect(screen.getByText('History')).toHaveAttribute('aria-current', 'page');
    expect(screen.getByText('Upload')).not.toHaveAttribute('aria-current');
  });

  it('calls handlers on click', () => {
    const onUpload = vi.fn();
    const onHistory = vi.fn();
    const onDashboard = vi.fn();
    const onSearch = vi.fn();
    render(
      <NavBar
        screen="upload"
        onUpload={onUpload}
        onHistory={onHistory}
        onDashboard={onDashboard}
        onSearch={onSearch}
      />,
    );

    fireEvent.click(screen.getByText('History'));
    expect(onHistory).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Upload'));
    expect(onUpload).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Dashboard'));
    expect(onDashboard).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Search'));
    expect(onSearch).toHaveBeenCalledTimes(1);
  });

  it('uses real buttons so the nav is keyboard operable', () => {
    render(
      <NavBar screen="upload" onUpload={noop} onHistory={noop} onDashboard={noop} onSearch={noop} />,
    );
    expect(screen.getAllByRole('button')).toHaveLength(4);
  });
});
