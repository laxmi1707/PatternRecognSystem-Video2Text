import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NavBar } from './NavBar';

function renderNavBar(overrides: Partial<Parameters<typeof NavBar>[0]> = {}) {
  const props = {
    screen: 'upload' as const,
    onUpload: vi.fn(),
    onHistory: vi.fn(),
    onDashboard: vi.fn(),
    onSearch: vi.fn(),
    ...overrides,
  };
  render(<NavBar {...props} />);
  return props;
}

describe('NavBar', () => {
  it('marks the active screen with aria-current', () => {
    renderNavBar({ screen: 'history' });
    expect(screen.getByText('History')).toHaveAttribute('aria-current', 'page');
    expect(screen.getByText('Upload')).not.toHaveAttribute('aria-current');
  });

  it('calls handlers on click', () => {
    const props = renderNavBar();
    fireEvent.click(screen.getByText('History'));
    expect(props.onHistory).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Upload'));
    expect(props.onUpload).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Dashboard'));
    expect(props.onDashboard).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Search'));
    expect(props.onSearch).toHaveBeenCalledTimes(1);
  });
});
