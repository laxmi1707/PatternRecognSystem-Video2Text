import { describe, it, expect, vi, afterEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
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

  it('shows nothing when the detector was not reachable', () => {
    const { container } = render(<DetectedSteps jobId={null} job={null} error={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows progress while the detector runs', () => {
    render(<DetectedSteps jobId="abc" job={{ ...done, status: 'running', progress_pct: 45, stage: 'tracking the mouse pointer', result: null }} error={null} />);
    expect(screen.getByText('45% — tracking the mouse pointer')).toBeInTheDocument();
  });

  it('lists the detected steps with the application and the counts', () => {
    render(<DetectedSteps jobId="abc" job={done} error={null} />);
    expect(screen.getByText('Eclipse')).toBeInTheDocument();
    expect(screen.getByText("'Package Explorer'")).toBeInTheDocument();
    expect(screen.getByText("'Apply and Close'")).toBeInTheDocument();
    expect(screen.getByText(/2 clicks/)).toBeInTheDocument();
    expect(screen.getByText(/0 typed/)).toBeInTheDocument();
  });

  it('jumps the video to a step when its time is selected', () => {
    const onSeek = vi.fn();
    render(<DetectedSteps jobId="abc" job={done} error={null} onSeek={onSeek} />);
    fireEvent.click(screen.getByRole('button', { name: /0:35/ }));
    expect(onSeek).toHaveBeenCalledWith(35.8);
  });

  it('shows a click with no text as a click on an icon', () => {
    const withIcon: DetectionJob = { ...done, result: { ...done.result!, steps: [
      ...done.result!.steps, { t: 36.5, action: 'Click', text: '' } ] } };
    render(<DetectedSteps jobId="abc" job={withIcon} error={null} />);
    expect(screen.getByText(/3 clicks/)).toBeInTheDocument();
    expect(screen.getByText(/1 on icons/)).toBeInTheDocument();
    expect(screen.getByText(/an icon or unlabelled control/)).toBeInTheDocument();
  });

  it('highlights the step shown at the current playback time', () => {
    render(<DetectedSteps jobId="abc" job={done} error={null} currentTime={20} />);
    const rows = screen.getAllByTestId('detected-step');
    expect(rows[0]).toHaveAttribute('aria-current', 'step');
    expect(rows[1]).not.toHaveAttribute('aria-current');
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
    fireEvent.click(screen.getByRole('button', { name: /Generate SOP/ }));   // the SOP is made on request
    const lists = await screen.findAllByTestId('sop-step-actions');
    expect(lists).toHaveLength(2);
    expect(lists[0]).toHaveTextContent("Click 'Package Explorer'");
    expect(lists[1]).toHaveTextContent("Click 'Apply and Close'");
  });
});
