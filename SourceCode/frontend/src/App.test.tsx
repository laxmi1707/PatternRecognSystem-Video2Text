import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import App from './App';

describe('App', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('walks through upload -> analyzing -> results', () => {
    render(<App />);
    expect(screen.getByText('Upload a screen recording')).toBeInTheDocument();

    const file = new File(['x'], 'session.mp4', { type: 'video/mp4' });
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    act(() => {
      fireEvent.change(input, { target: { files: [file] } });
    });
    expect(screen.getByText('Analyzing your recording')).toBeInTheDocument();

    act(() => { vi.advanceTimersByTime(3500); });
    expect(screen.getByText('session.mp4')).toBeInTheDocument();
    expect(screen.getByText('Analyze another video')).toBeInTheDocument();
  });

  it('shows history with the mock entries and can open one', () => {
    render(<App />);
    fireEvent.click(screen.getByText('History'));
    expect(screen.getByText('onboarding-demo.mov')).toBeInTheDocument();

    const viewButtons = screen.getAllByText('View');
    fireEvent.click(viewButtons[0]);
    expect(screen.getByText('onboarding-demo.mov', { selector: 'h1' })).toBeInTheDocument();
  });

  it('returns to upload from results', () => {
    render(<App />);
    fireEvent.click(screen.getByText('History'));
    fireEvent.click(screen.getAllByText('View')[0]);
    fireEvent.click(screen.getByText('Analyze another video'));
    expect(screen.getByText('Upload a screen recording')).toBeInTheDocument();
  });
});
