import { useEffect, useState } from 'react';
import { getDetection } from '../services/api/sopDetector';
import type { DetectionJob } from '../types/detection';

const POLL_MS = 2000;

/** Polls the SOP detector until its job completes or fails. */
export function useDetection(jobId: string | null | undefined): { job: DetectionJob | null; error: string | null } {
  const [job, setJob] = useState<DetectionJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setJob(null);
    setError(null);
    if (!jobId) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    async function poll() {
      try {
        const next = await getDetection(jobId!);
        if (stopped) return;
        setJob(next);
        if (next.status === 'running') timer = setTimeout(poll, POLL_MS);
      } catch {
        if (!stopped) setError('The SOP detector stopped responding.');
      }
    }
    poll();
    return () => {
      stopped = true;
      if (timer) clearTimeout(timer);
    };
  }, [jobId]);

  return { job, error };
}
