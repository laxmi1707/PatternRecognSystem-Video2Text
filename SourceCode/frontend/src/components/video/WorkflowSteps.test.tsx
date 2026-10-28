import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkflowSteps } from './WorkflowSteps';

const steps = [
  { n: 1, time: '0:00-0:07', title: 'Ran rm -rf', description: 'desc one', risk_level: 'high' as const, risk_reason: 'Deletes files' },
  { n: 2, time: '0:07-0:16', title: 'Opened the terminal', description: 'desc two' },
  { n: 3, time: '0:16-0:30', title: 'Ran sudo apt install', description: 'desc three', risk_level: 'medium' as const, risk_reason: 'Privilege escalation' },
];

describe('WorkflowSteps', () => {
  it('renders only the risky steps, with their badge, reason and time', () => {
    render(<WorkflowSteps steps={steps} />);
    expect(screen.getByText('2 anomalies detected')).toBeInTheDocument();
    expect(screen.getByText('Ran rm -rf')).toBeInTheDocument();
    expect(screen.getByText('⚠ HIGH RISK')).toBeInTheDocument();
    expect(screen.getByText('Deletes files')).toBeInTheDocument();
    expect(screen.getByText('⚠ MEDIUM RISK')).toBeInTheDocument();
    expect(screen.getByText('0:16-0:30')).toBeInTheDocument();
    expect(screen.queryByText('Opened the terminal')).toBeNull();
  });

  it('says no anomalies were detected when no step is risky', () => {
    render(<WorkflowSteps steps={[steps[1]]} />);
    expect(screen.getByText('No anomalies detected in this recording.')).toBeInTheDocument();
  });

  it('renders nothing for an empty list', () => {
    const { container } = render(<WorkflowSteps steps={[]} />);
    expect(container.querySelectorAll('.workflow-step').length).toBe(0);
  });
});
