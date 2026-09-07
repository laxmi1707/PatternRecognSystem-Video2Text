import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardPage } from './DashboardPage';
import { getMockHistory } from '../services/api/analysisService';

describe('DashboardPage', () => {
  it('shows a stat card with the total analysis count', () => {
    const history = getMockHistory();
    render(<DashboardPage history={history} />);
    const card = screen.getByText('Analyses').closest('.stat-card');
    expect(card).toHaveTextContent(String(history.length));
  });

  it('renders one bar per label present in history', () => {
    const history = getMockHistory();
    render(<DashboardPage history={history} />);
    const labels = new Set(history.map(h => h.label));
    labels.forEach(label => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it('shows an empty state with no history', () => {
    render(<DashboardPage history={[]} />);
    expect(screen.getByText('No completed analyses yet.')).toBeInTheDocument();
  });
});
