import type { DetectedStep, DetectionJob } from '../../types/detection';

// The SOP detector runs as its own small service (Evaluation/sop_detector_service.py);
// the dev server proxies /sop-detector to it.
const BASE = import.meta.env.VITE_SOP_DETECTOR_URL ?? '/sop-detector';

/** Send the video to the detector. Returns null if the service is not running. */
export async function startDetection(file: File): Promise<string | null> {
  try {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/jobs`, { method: 'POST', body: form });
    if (!res.ok) return null;
    const body = await res.json();
    return typeof body.job_id === 'string' ? body.job_id : null;
  } catch {
    return null;
  }
}

export async function getDetection(jobId: string): Promise<DetectionJob> {
  const res = await fetch(`${BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`SOP detector ${res.status}`);
  return res.json();
}

/** "12.0s - 30.5s", the backend SOP's time_range, as [12, 30.5]. */
export function parseTimeRange(range: string): [number, number] | null {
  const m = /([\d.]+)\s*s?\s*-\s*([\d.]+)\s*s?/.exec(range);
  return m ? [parseFloat(m[1]), parseFloat(m[2])] : null;
}

/** The detected steps inside one SOP step's time range; the last step also keeps its end. */
export function stepsInRange(steps: DetectedStep[], range: string, isLast = false): DetectedStep[] {
  const r = parseTimeRange(range);
  if (!r) return [];
  const [start, end] = r;
  return steps.filter((s) => s.t >= start && (s.t < end || (isLast && s.t <= end + 1)));
}

export function formatClock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

export function describeStep(step: DetectedStep): string {
  return step.action === 'Click' ? `Click '${step.text}'` : `Type "${step.text}"`;
}
