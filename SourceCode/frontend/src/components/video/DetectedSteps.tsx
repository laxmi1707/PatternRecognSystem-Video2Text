import type { DetectionJob } from '../../types/detection';
import { describeStep, formatClock } from '../../services/api/sopDetector';

interface DetectedStepsProps {
  /** undefined: no detection for this result; null: the detector service was not reachable */
  jobId: string | null | undefined;
  job: DetectionJob | null;
  error: string | null;
}

const ORANGE = '#EF7C00';
// the app's .text-muted is too light on this white card
const MUTED = '#6b7280';

export function DetectedSteps({ jobId, job, error }: DetectedStepsProps) {
  if (jobId === undefined) return null;

  let body: JSX.Element;
  if (jobId === null) {
    body = (
      <p style={{ color: MUTED, fontSize: 14, margin: 0 }}>
        The SOP detector is not running, so no steps were read from the video.
        Start it with <code>python Evaluation/sop_detector_service.py</code>.
      </p>
    );
  } else if (error || job?.status === 'failed') {
    body = <p style={{ color: 'var(--color-error, red)', fontSize: 14, margin: 0 }}>{error ?? job?.error}</p>;
  } else if (!job || job.status === 'running') {
    const pct = Math.round(job?.progress_pct ?? 0);
    body = (
      <div>
        <p style={{ color: MUTED, fontSize: 13, margin: '0 0 6px' }}>
          {pct}% — {job?.stage ?? 'starting'}
        </p>
        <div style={{ height: 6, borderRadius: 3, background: '#f3f4f6', overflow: 'hidden' }}>
          <div data-testid="detector-progress" style={{ width: `${pct}%`, height: '100%', background: ORANGE }} />
        </div>
      </div>
    );
  } else {
    const r = job.result!;
    body = (
      <>
        <p style={{ fontSize: 14, color: '#4b5563', margin: '0 0 10px' }}>
          Application: <strong>{r.app}</strong>
          {r.app_confidence != null && <> ({Math.round(r.app_confidence * 100)}% confident)</>}
          {' '}&middot; {r.steps.length} steps
        </p>
        {r.steps.length === 0 ? (
          <p style={{ color: MUTED, fontSize: 14, margin: 0 }}>No clicks or typing were found.</p>
        ) : (
          <ol style={{ margin: 0, paddingLeft: 22 }}>
            {r.steps.map((s, i) => (
              <li key={i} style={{ marginBottom: 4, fontSize: 14 }}>
                <span style={{ color: MUTED, fontSize: 12, marginRight: 8 }}>{formatClock(s.t)}</span>
                {describeStep(s)}
              </li>
            ))}
          </ol>
        )}
      </>
    );
  }

  return (
    <div className="detected-steps" style={{
      marginTop: 'var(--space-6, 2rem)', background: '#ffffff', border: '1px solid #e5e7eb',
      borderRadius: 8, padding: 'var(--space-4, 1.5rem)', color: '#111827', position: 'relative', zIndex: 1,
    }}>
      <h6 style={{
        fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase',
        color: ORANGE, margin: '0 0 6px',
      }}>
        Steps detected from the video
      </h6>
      <p style={{ color: MUTED, fontSize: 13, margin: '0 0 12px' }}>
        Clicks and typing read from the screen recording alone, without an action log.
      </p>
      {body}
    </div>
  );
}
