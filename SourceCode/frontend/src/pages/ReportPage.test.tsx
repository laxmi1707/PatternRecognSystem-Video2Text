import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReportPage } from './ReportPage';
import type { ClassificationResult } from '../types/analysis';

const target: ClassificationResult = {
  id: 'h1', name: 'demo.mp4', date: 'Today', duration: '1:00',
  status: 'Complete', videoUrl: null,
  label: 'coding_editing', confidence: 0.8, probabilities: { coding_editing: 0.8, other: 0.2 },
};

describe('ReportPage', () => {
  it('shows a loading spinner while the report is being fetched', () => {
    render(<ReportPage target={target} report={null} loading={true} error={null} onBack={() => {}} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows the error and a way back when the fetch fails', () => {
    const onBack = vi.fn();
    render(<ReportPage target={target} report={null} loading={false} error="network down" onBack={onBack} />);
    expect(screen.getByRole('alert')).toHaveTextContent('network down');
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('renders the report once loaded', () => {
    render(
      <ReportPage
        target={target}
        report={{ summary: 'A summary.', steps: [{ n: 1, time: '0:00-0:05', title: 'Step one', description: 'did a thing' }] }}
        loading={false}
        error={null}
        onBack={() => {}}
      />
    );
    expect(screen.getByText('A summary.')).toBeInTheDocument();
    expect(screen.getByText('Step one')).toBeInTheDocument();
  });
});
