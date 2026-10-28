import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { describeStep, detectorEnabled, detectorExpected, formatClock, parseTimeRange, startDetection, stepsInRange } from './sopDetector';
import type { DetectedStep } from '../../types/detection';

const steps: DetectedStep[] = [
  { t: 1.8, action: 'Click', text: 'Package Explorer' },
  { t: 12.0, action: 'Type', text: 'sudo adduser priya' },
  { t: 30.5, action: 'Click', text: 'Apply and Close' },
];

describe('parseTimeRange', () => {
  it('reads the backend SOP time range', () => {
    expect(parseTimeRange('12.0s - 30.5s')).toEqual([12, 30.5]);
  });
  it('returns null for anything else', () => {
    expect(parseTimeRange('')).toBeNull();
  });
});

describe('stepsInRange', () => {
  it('keeps steps from the start up to, not including, the end', () => {
    expect(stepsInRange(steps, '0.0s - 12.0s').map((s) => s.text)).toEqual(['Package Explorer']);
    expect(stepsInRange(steps, '12.0s - 30.5s').map((s) => s.text)).toEqual(['sudo adduser priya']);
  });
  it('lets the last SOP step keep a step at its end', () => {
    expect(stepsInRange(steps, '12.0s - 30.5s', true)).toHaveLength(2);
  });
});

describe('formatting', () => {
  it('writes clicks and typing as SOP lines', () => {
    expect(describeStep(steps[0])).toBe("Click 'Package Explorer'");
    expect(describeStep(steps[1])).toBe('Type "sudo adduser priya"');
    expect(describeStep({ t: 5, action: 'Click', text: '' })).toBe('Click (icon)');
  });
  it('writes seconds as m:ss', () => {
    expect(formatClock(75.4)).toBe('1:15');
  });
});

describe('switched off (the default)', () => {
  afterEach(() => vi.restoreAllMocks());

  it('sends nothing to the detector and expects no panel', async () => {
    const fetchMock = vi.fn();
    globalThis.fetch = fetchMock;
    expect(detectorEnabled()).toBe(false);
    expect(detectorExpected()).toBe(false);
    expect(await startDetection(new File(['x'], 'clip.mp4'))).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('startDetection', () => {
  beforeEach(() => vi.stubEnv('VITE_SOP_DETECTOR_ENABLED', 'true'));
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('returns the job id', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ job_id: 'abc' }) } as Response));
    expect(await startDetection(new File(['x'], 'clip.mp4'))).toBe('abc');
  });
  it('returns null at once when the service is not running', async () => {
    const fetchMock = vi.fn(() => Promise.reject(new Error('connection refused')));
    globalThis.fetch = fetchMock;
    expect(await startDetection(new File(['x'], 'clip.mp4'), 3, 0)).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it('waits for a detector that answers "not ready"', async () => {
    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 502 } as Response)
      .mockResolvedValueOnce({ ok: false, status: 503 } as Response)
      .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ job_id: 'late' }) } as Response);
    expect(await startDetection(new File(['x'], 'clip.mp4'), 4, 0)).toBe('late');
  });
});
