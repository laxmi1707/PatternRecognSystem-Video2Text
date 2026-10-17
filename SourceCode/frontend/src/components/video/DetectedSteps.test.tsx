import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DetectedSteps } from './DetectedSteps';
import { KnowledgePanel } from './KnowledgePanel';
import type { DetectionJob } from '../../types/detection';

const done: DetectionJob = {
  job_id: 'abc', status: 'completed', progress_pct: 100, stage: 'done', error: null,
  result: {
    app: 'Eclipse', app_confidence: 0.997, duration: 37.8,
    steps: [
      { t: 1.8, action: 'Click', text: 'Package Explorer' },
      { t: 35.8, action: 'Click', text: 'Apply and Close' },
    ],
  },
};

describe('DetectedSteps', () => {
  it('shows nothing for a result without a detection', () => {
    const { container } = render(<DetectedSteps jobId={undefined} job={null} error={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('says how to start the detector when it was not reachable', () => {
    render(<DetectedSteps jobId={null} job={null} error={null} />);
    expect(screen.getByText(/SOP detector is not running/)).toBeInTheDocument();
  });

  it('shows progress while the detector runs', () => {
    render(<DetectedSteps jobId="abc" job={{ ...done, status: 'running', progress_pct: 45, stage: 'tracking the mouse pointer', result: null }} error={null} />);
    expect(screen.getByText('45% — tracking the mouse pointer')).toBeInTheDocument();
  });

  it('lists the detected steps with the application', () => {
    render(<DetectedSteps jobId="abc" job={done} error={null} />);
    expect(screen.getByText('Eclipse')).toBeInTheDocument();
    expect(screen.getByText("Click 'Package Explorer'")).toBeInTheDocument();
    expect(screen.getByText("Click 'Apply and Close'")).toBeInTheDocument();
  });
});

describe('KnowledgePanel with detected steps', () => {
  afterEach(() => vi.restoreAllMocks());

  it('lists each detected step under the SOP step whose time range holds it', async () => {
    const sop = {
      title: 'SOP: add a JAR', purpose: 'p', prerequisites: [], expected_outcome: 'o', troubleshooting: [],
      steps: [
        { number: 1, title: 'Navigate Eclipse IDE', description: 'd1', time_range: '0.0s - 20.0s' },
        { number: 2, title: 'Configure settings', description: 'd2', time_range: '20.0s - 37.8s' },
      ],
    };
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(sop) } as Response));
    render(<KnowledgePanel jobId="1" detectedSteps={done.result!.steps} />);
    const lists = await screen.findAllByTestId('sop-step-actions');
    expect(lists).toHaveLength(2);
    expect(lists[0]).toHaveTextContent("Click 'Package Explorer'");
    expect(lists[1]).toHaveTextContent("Click 'Apply and Close'");
  });
});
