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

  it('renders one bar per category present in history', () => {
    const history = getMockHistory();
    render(<DashboardPage history={history} />);
    const categories = new Set(history.map(h => h.category));
    categories.forEach(category => {
      expect(screen.getByText(category)).toBeInTheDocument();
    });
  });

  it('shows an empty state with no history', () => {
    render(<DashboardPage history={[]} />);
    expect(screen.getByText('No completed analyses yet.')).toBeInTheDocument();
  });
});
