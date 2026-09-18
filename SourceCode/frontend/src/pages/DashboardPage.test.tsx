import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import type { AnalysisResult } from '../types/analysis';

const { fetchAvailableModels, runEvaluation } = vi.hoisted(() => ({
  fetchAvailableModels: vi.fn(),
  runEvaluation: vi.fn(),
}));

vi.mock('../services/api/evaluationService', () => ({ fetchAvailableModels, runEvaluation }));

import { DashboardPage } from './DashboardPage';

function entry(id: string, label?: string, confidence?: number): AnalysisResult {
  return {
    id, name: `${id}.mp4`, date: 'Today', duration: '1:00', stepCount: 1,
    status: 'Complete', videoUrl: null, summary: '', steps: [],
    label, confidence,
  };
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchAvailableModels.mockResolvedValue({ models: ['svm', 'knn'], tiers: {} });
    runEvaluation.mockResolvedValue({
      comparison_table: [
        {
          model_name: 'svm', tier: 'tier1', accuracy: 0.9, precision_macro: 0.9,
          recall_macro: 0.9, f1_macro: 0.9, auc_macro: 0.95, latency_ms: 12.3,
        },
      ],
      generated_at: '2026-09-18T00:00:00Z',
    });
  });

  it('counts analyses and distinct activities', () => {
    const history = [entry('a', 'coding_editing', 0.8), entry('b', 'coding_editing', 0.6), entry('c', 'debugging', 0.4)];
    render(<DashboardPage history={history} />);

    const analyses = screen.getByText('Analyses').closest('.stat-card');
    expect(analyses).toHaveTextContent('3');
    const activities = screen.getByText('Activities seen').closest('.stat-card');
    expect(activities).toHaveTextContent('2');
    const confidence = screen.getByText('Avg. confidence').closest('.stat-card');
    expect(confidence).toHaveTextContent('60%');
  });

  it('tells the user when nothing has been classified yet', () => {
    render(<DashboardPage history={[entry('a')]} />);
    expect(screen.getByText(/No classified analyses yet/)).toBeInTheDocument();
  });

  it('renders the model comparison table after running an evaluation', async () => {
    render(<DashboardPage history={[]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Run evaluation' }));

    await waitFor(() => expect(screen.getByText('svm')).toBeInTheDocument());
    expect(screen.getByText('0.950')).toBeInTheDocument();
    expect(runEvaluation).toHaveBeenCalledTimes(1);
  });

  it('shows an error when the evaluation fails', async () => {
    runEvaluation.mockRejectedValue(new Error('offline'));
    render(<DashboardPage history={[]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Run evaluation' }));

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
  });
});
