import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { describeStep, detectorEnabled, detectorExpected, detectorUrl, formatClock, parseTimeRange, startDetection, stepsInRange } from './sopDetector';
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
  it('posts to the backend\'s host in a production build', async () => {
    vi.stubEnv('PROD', true);
    vi.stubEnv('VITE_SOP_DETECTOR_URL', '');
    vi.stubEnv('VITE_API_BASE_URL', 'https://d123.cloudfront.net/api/v1');
    const fetchMock = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ job_id: 'abc' }) } as Response));
    globalThis.fetch = fetchMock;
    await startDetection(new File(['x'], 'clip.mp4'));
    expect(fetchMock).toHaveBeenCalledWith(
      'https://d123.cloudfront.net/sop-detector/jobs', expect.objectContaining({ method: 'POST' }));
  });
  it('sends the API key, as the backend\'s own calls do', async () => {
    vi.stubEnv('VITE_API_KEY', 'k');
    vi.resetModules();
    const { getDetection } = await import('./sopDetector');
    const fetchMock = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'running' }) } as Response));
    globalThis.fetch = fetchMock;
    await getDetection('0123456789ab');
    expect(fetchMock).toHaveBeenCalledWith(
      '/sop-detector/jobs/0123456789ab', { headers: { 'X-API-Key': 'k' } });
  });
});

describe('where the detector answers', () => {
  afterEach(() => vi.unstubAllEnvs());

  it('uses VITE_SOP_DETECTOR_URL when the build sets it', () => {
    vi.stubEnv('VITE_SOP_DETECTOR_URL', 'http://localhost:8100/sop-detector');
    expect(detectorUrl()).toBe('http://localhost:8100/sop-detector');
  });
  it('is /sop-detector on the backend\'s host in a production build (on AWS it runs in the backend\'s container)', () => {
    vi.stubEnv('PROD', true);
    vi.stubEnv('DEV', false);
    vi.stubEnv('VITE_SOP_DETECTOR_URL', '');
    vi.stubEnv('VITE_API_BASE_URL', 'https://d123.cloudfront.net/api/v1');
    expect(detectorUrl()).toBe('https://d123.cloudfront.net/sop-detector');
    vi.stubEnv('VITE_SOP_DETECTOR_ENABLED', 'true');
    expect(detectorExpected()).toBe(true);
  });
  it('stays /sop-detector on the dev server, which proxies it', () => {
    vi.stubEnv('PROD', false);
    vi.stubEnv('VITE_SOP_DETECTOR_URL', '');
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000/api/v1');
    expect(detectorUrl()).toBe('/sop-detector');
  });
});
