import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchPage } from './SearchPage';

describe('SearchPage', () => {
  it('shows mock results after searching', async () => {
    render(<SearchPage />);
    fireEvent.change(screen.getByLabelText('Search query'), { target: { value: 'deploy' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    await waitFor(() => {
      expect(screen.getByText('deploy-walkthrough.webm')).toBeInTheDocument();
    });
  });

  it('does not search on an empty query', () => {
    render(<SearchPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    expect(screen.queryByText(/No matches/)).not.toBeInTheDocument();
  });
});
