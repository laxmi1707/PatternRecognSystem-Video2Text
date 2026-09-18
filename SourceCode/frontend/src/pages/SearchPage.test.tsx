import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import type { AnalysisResult } from '../types/analysis';
import { SearchPage } from './SearchPage';

const history: AnalysisResult[] = [
  {
    id: '1', name: 'deploy-walkthrough.webm', date: 'Today', duration: '3:02', stepCount: 1,
    status: 'Complete', videoUrl: null, summary: 'A production deploy is walked through.',
    steps: [{ n: 1, time: '0:00-0:24', title: 'Merged the release branch', description: 'A pull request is merged into main.' }],
    label: 'jenkins_ci_cd',
  },
  {
    id: '2', name: 'notes.mov', date: 'Today', duration: '0:30', stepCount: 0,
    status: 'Complete', videoUrl: null, summary: 'Documentation was edited.', steps: [],
    label: 'documentation',
  },
];

describe('SearchPage', () => {
  it('finds an analysis by file name', () => {
    render(<SearchPage history={history} onView={() => {}} />);
    fireEvent.change(screen.getByLabelText('Search query'), { target: { value: 'deploy' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(screen.getByText('deploy-walkthrough.webm')).toBeInTheDocument();
    expect(screen.getByText('1 match for “deploy”')).toBeInTheDocument();
  });

  it('finds an analysis by step text', () => {
    render(<SearchPage history={history} onView={() => {}} />);
    fireEvent.change(screen.getByLabelText('Search query'), { target: { value: 'pull request' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(screen.getByText(/A pull request is merged into main/)).toBeInTheDocument();
  });

  it('reports when nothing matches', () => {
    render(<SearchPage history={history} onView={() => {}} />);
    fireEvent.change(screen.getByLabelText('Search query'), { target: { value: 'kubernetes' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(screen.getByText('0 matches for “kubernetes”')).toBeInTheDocument();
  });

  it('opens a result', () => {
    const onView = vi.fn();
    render(<SearchPage history={history} onView={onView} />);
    fireEvent.change(screen.getByLabelText('Search query'), { target: { value: 'notes' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('button', { name: 'Open' }));

    expect(onView).toHaveBeenCalledWith(history[1]);
  });
});
