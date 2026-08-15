import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkflowSteps } from './WorkflowSteps';

const steps = [
  { n: 1, time: '0:00-0:07', title: 'Opened the editor', description: 'desc one' },
  { n: 2, time: '0:07-0:16', title: 'Opened the terminal', description: 'desc two' },
];

describe('WorkflowSteps', () => {
  it('renders one row per step with title and time', () => {
    render(<WorkflowSteps steps={steps} />);
    expect(screen.getAllByText(/Opened the/).length).toBe(2);
    expect(screen.getByText('0:00-0:07')).toBeInTheDocument();
    expect(screen.getByText('desc two')).toBeInTheDocument();
  });

  it('renders nothing for an empty list', () => {
    const { container } = render(<WorkflowSteps steps={[]} />);
    expect(container.querySelectorAll('.workflow-step').length).toBe(0);
  });
});
