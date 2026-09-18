import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import type { AnalysisResult } from '../types/analysis';

const { fetchSopReport } = vi.hoisted(() => ({ fetchSopReport: vi.fn() }));
vi.mock('../services/api/evaluationService', () => ({ fetchSopReport }));

import { ReportPage } from './ReportPage';

const target: AnalysisResult = {
  id: '7', jobId: 42, name: 'session.mp4', date: 'Today', duration: '1:00', stepCount: 1,
  status: 'Complete', videoUrl: null, summary: '', steps: [],
  label: 'coding_editing', confidence: 0.8,
};

const sop = {
  title: 'Set up the project',
  purpose: 'Bring a new machine to a working state.',
  prerequisites: ['Git installed'],
  steps: [{ number: 1, title: 'Cloned the repository', description: 'git clone was run.', time_range: '0:00-0:20' }],
  expected_outcome: 'The app runs locally.',
  troubleshooting: ['If the clone fails, check credentials.'],
};

describe('ReportPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows a spinner while the report is generated', () => {
    fetchSopReport.mockReturnValue(new Promise(() => {}));
    render(<ReportPage target={target} onBack={() => {}} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders the generated SOP', async () => {
    fetchSopReport.mockResolvedValue(sop);
    render(<ReportPage target={target} onBack={() => {}} />);

    await waitFor(() => expect(screen.getByText('Set up the project')).toBeInTheDocument());
    expect(screen.getByText('Cloned the repository')).toBeInTheDocument();
    expect(screen.getByText('The app runs locally.')).toBeInTheDocument();
    expect(fetchSopReport).toHaveBeenCalledWith(42);
  });

  it('surfaces a failure instead of spinning forever', async () => {
    fetchSopReport.mockRejectedValue(new Error('offline'));
    render(<ReportPage target={target} onBack={() => {}} />);

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('explains when the analysis has no job to report on', () => {
    render(<ReportPage target={{ ...target, jobId: undefined }} onBack={() => {}} />);
    expect(screen.getByRole('alert')).toHaveTextContent('no job attached');
    expect(fetchSopReport).not.toHaveBeenCalled();
  });
});
