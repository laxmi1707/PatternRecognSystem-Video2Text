import type { ReactNode } from 'react';
import type { DetectedStep, DetectionJob } from '../../types/detection';
import { formatClock } from '../../services/api/sopDetector';

interface DetectedStepsProps {
  /** undefined: no detection for this result; null: the detector service was not reachable */
  jobId: string | null | undefined;
  job: DetectionJob | null;
  error: string | null;
  /** jump the video to this many seconds */
  onSeek?: (t: number) => void;
  /** the video's playback position, to highlight the step being shown */
  currentTime?: number;
}

const ORANGE = '#EF7C00';
const ORANGE_TINT = '#fff4e8';
const TEAL = '#006786';
const TEAL_TINT = '#e9f8ff';
const INK = '#0a303e';
// the app's .text-muted is too light on this white card
const MUTED = '#5b6470';

const ACTION_STYLE: Record<DetectedStep['action'], { fg: string; bg: string; icon: string; label: string }> = {
  Click: { fg: ORANGE, bg: ORANGE_TINT, icon: '🖱', label: 'Click' },
  Type: { fg: TEAL, bg: TEAL_TINT, icon: '⌨', label: 'Type' },
};

/** Index of the step on screen at time t: the last one that started at or before it. */
export function activeStep(steps: DetectedStep[], t: number | undefined): number {
  if (t == null) return -1;
  let k = -1;
  steps.forEach((s, i) => { if (s.t <= t + 0.25) k = i; });
  return k;
}

function Header({ right }: { right?: JSX.Element }) {
  return (
    <div style={{
      background: INK, color: '#fff', padding: '14px 20px', display: 'flex',
      alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
    }}>
      <div>
        <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: ORANGE }}>
          SOP Detector
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, marginTop: 2 }}>Steps read from the video</div>
        <div style={{ fontSize: 13, color: '#c9d6dc', marginTop: 2 }}>
          Clicks and typing found in the screen recording alone, without an action log.
        </div>
      </div>
      {right}
    </div>
  );
}

function Pill({ children, fg, bg }: { children: ReactNode; fg: string; bg: string }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 999,
      fontSize: 13, fontWeight: 600, color: fg, background: bg, whiteSpace: 'nowrap',
    }}>
      {children}
    </span>
  );
}

export function DetectedSteps({ jobId, job, error, onSeek, currentTime }: DetectedStepsProps) {
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
    body = <p style={{ color: 'var(--color-error, #b91c1c)', fontSize: 14, margin: 0 }}>{error ?? job?.error}</p>;
  } else if (!job || job.status === 'running') {
    const pct = Math.round(job?.progress_pct ?? 0);
    body = (
      <div>
        <p style={{ color: INK, fontSize: 15, fontWeight: 600, margin: '0 0 8px' }}>
          {pct}% — {job?.stage ?? 'starting'}
        </p>
        <div style={{ height: 10, borderRadius: 5, background: '#f1f3f5', overflow: 'hidden' }}>
          <div data-testid="detector-progress" style={{
            width: `${pct}%`, height: '100%', background: ORANGE, transition: 'width 0.6s ease',
          }} />
        </div>
        <p style={{ color: MUTED, fontSize: 13, margin: '8px 0 0' }}>
          Tracking the mouse pointer and reading the screen; a new video takes a few minutes.
        </p>
      </div>
    );
  } else {
    const r = job.result!;
    const clicks = r.steps.filter(s => s.action === 'Click').length;
    const icons = r.steps.filter(s => s.action === 'Click' && !s.text).length;
    const typed = r.steps.length - clicks;
    const active = activeStep(r.steps, currentTime);
    body = (
      <>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', marginBottom: 14 }}>
          <Pill fg={INK} bg="#eef2f4">
            Application: <strong>{r.app}</strong>
            {r.app_confidence != null && <span style={{ fontWeight: 400 }}>({Math.round(r.app_confidence * 100)}%)</span>}
          </Pill>
          <Pill fg={ORANGE} bg={ORANGE_TINT}>
            {ACTION_STYLE.Click.icon} {clicks} clicks{icons > 0 && <span style={{ fontWeight: 400 }}>({icons} on icons)</span>}
          </Pill>
          <Pill fg={TEAL} bg={TEAL_TINT}>{ACTION_STYLE.Type.icon} {typed} typed</Pill>
          {onSeek && r.steps.length > 0 && (
            <span style={{ color: MUTED, fontSize: 13 }}>Select a time to jump to that moment in the video.</span>
          )}
        </div>
        {r.steps.length === 0 ? (
          <p style={{ color: MUTED, fontSize: 14, margin: 0 }}>No clicks or typing were found.</p>
        ) : (
          <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 6 }}>
            {r.steps.map((s, i) => {
              const st = ACTION_STYLE[s.action];
              const on = i === active;
              return (
                <li key={i} data-testid="detected-step" aria-current={on ? 'step' : undefined} style={{
                  display: 'grid', gridTemplateColumns: '28px 64px 86px 1fr', alignItems: 'center', gap: 10,
                  padding: '8px 10px', borderRadius: 8,
                  background: on ? ORANGE_TINT : '#fafbfc',
                  border: `1px solid ${on ? ORANGE : '#eceff2'}`,
                  transition: 'background 0.2s, border-color 0.2s',
                }}>
                  <span style={{ color: MUTED, fontSize: 13, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {i + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => onSeek?.(s.t)}
                    disabled={!onSeek}
                    title={onSeek ? `Play the video from ${formatClock(s.t)}` : undefined}
                    style={{
                      font: 'inherit', fontSize: 13, fontVariantNumeric: 'tabular-nums', fontWeight: 600,
                      color: TEAL, background: '#fff', border: `1px solid ${TEAL}`, borderRadius: 6,
                      padding: '3px 0', cursor: onSeek ? 'pointer' : 'default',
                    }}
                  >
                    ▶ {formatClock(s.t)}
                  </button>
                  <Pill fg={st.fg} bg={st.bg}>{st.icon} {st.label}</Pill>
                  {s.action === 'Click' && !s.text ? (
                    <span style={{ fontSize: 14, fontStyle: 'italic', color: MUTED }}>
                      an icon or unlabelled control — play the video to see it
                    </span>
                  ) : (
                    <span style={{ fontSize: 15, fontWeight: on ? 700 : 500, color: '#111827', overflowWrap: 'anywhere' }}>
                      {s.action === 'Click' ? `'${s.text}'` : `"${s.text}"`}
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
        )}
      </>
    );
  }

  return (
    <section className="detected-steps" aria-label="Steps detected from the video" style={{
      marginTop: 'var(--space-6, 2rem)', background: '#ffffff', borderRadius: 12, overflow: 'hidden',
      boxShadow: '0 6px 24px rgba(10, 48, 62, 0.18)', border: `2px solid ${ORANGE}`,
      color: '#111827', position: 'relative', zIndex: 1,
    }}>
      <Header right={<Pill fg={INK} bg={ORANGE}>VIDEO ONLY · NO ACTION LOG</Pill>} />
      <div style={{ padding: '16px 20px 20px' }}>{body}</div>
    </section>
  );
}
