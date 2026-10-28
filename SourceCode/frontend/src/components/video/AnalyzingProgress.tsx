import { useEffect, useRef, useState } from 'react';

interface AnalyzingProgressProps {
  fileName: string;
  videoUrl: string | null;
  progress: number;
  stage?: string;
  showPreview?: boolean;
  analysisReady?: boolean;   // backend done — animate remaining tasks then call onAnimationDone
  onAnimationDone?: () => void;
}

const TASKS = [
  { icon: '📤', label: 'Uploading video',                minPct: 0,  maxPct: 4  },
  { icon: '🎬', label: 'Preparing video analysis',       minPct: 5,  maxPct: 9  },
  { icon: '🔍', label: 'Extracting segments & keyframes',minPct: 10, maxPct: 59 },
  { icon: '🧠', label: 'Engineering features',           minPct: 60, maxPct: 64, highlight: true },
  { icon: '⚡', label: 'Classifying activities',         minPct: 65, maxPct: 95 },
  { icon: '💾', label: 'Saving results',                 minPct: 96, maxPct: 100 },
];

// ms each task stays visible when fast-forwarding at the end
const TASK_REVEAL_MS = 600;

function clamp(v: number, lo: number, hi: number) { return Math.min(hi, Math.max(lo, v)); }

function taskFill(pct: number, minPct: number, maxPct: number): number {
  if (pct <= minPct) return 0;
  if (pct >= maxPct) return 100;
  return Math.round(((pct - minPct) / (maxPct - minPct)) * 100);
}

function taskStatus(pct: number, minPct: number, maxPct: number): 'done' | 'active' | 'pending' {
  if (pct >= maxPct) return 'done';
  if (pct >= minPct) return 'active';
  return 'pending';
}

export function AnalyzingProgress({
  fileName, videoUrl, progress, stage, showPreview = true,
  analysisReady = false, onAnimationDone,
}: AnalyzingProgressProps) {

  // displayPct drives the visual — smoothly trails behind the real progress
  const [displayPct, setDisplayPct] = useState(0);
  const displayRef  = useRef(0);
  const realRef     = useRef(progress);
  const doneRef     = useRef(false);

  // Keep realRef in sync with incoming progress prop
  useEffect(() => { realRef.current = progress; }, [progress]);

  // Smooth crawl: every 80ms, nudge displayPct toward realPct
  useEffect(() => {
    const id = setInterval(() => {
      if (doneRef.current) return;
      const real = realRef.current;
      const cur  = displayRef.current;
      if (cur >= real) return;
      const step = real - cur > 10 ? 2 : 0.6;
      const next = clamp(cur + step, 0, real);
      displayRef.current = next;
      setDisplayPct(next);
    }, 80);
    return () => clearInterval(id);
  }, []);

  // When backend is ready: fast-forward through remaining tasks one by one,
  // each staying visible for TASK_REVEAL_MS, then call onAnimationDone
  useEffect(() => {
    if (!analysisReady || doneRef.current) return;

    // Find first task not yet done
    const firstPending = TASKS.findIndex(
      t => displayRef.current < t.maxPct
    );
    const startIdx = firstPending === -1 ? TASKS.length : firstPending;

    let step = startIdx;

    function advanceTask() {
      if (step >= TASKS.length) {
        doneRef.current = true;
        displayRef.current = 100;
        setDisplayPct(100);
        setTimeout(() => onAnimationDone?.(), 400);
        return;
      }
      const task = TASKS[step];
      // Jump display to the end of this task
      displayRef.current = task.maxPct;
      setDisplayPct(task.maxPct);
      step++;
      setTimeout(advanceTask, TASK_REVEAL_MS);
    }

    // Small delay before starting fast-forward so last real state is visible
    setTimeout(advanceTask, 300);
  }, [analysisReady, onAnimationDone]);

  const pct = Math.round(displayPct);
  const stageText = analysisReady && pct >= 100
    ? 'Analysis complete ✓'
    : (stage || 'starting analysis…');

  return (
    <div className="analyzing" style={{ cursor: 'wait' }}>
      {showPreview && videoUrl && (
        <video src={videoUrl} muted className="analyzing-preview" />
      )}

      {/* Hourglass + title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'center', marginBottom: 4 }}>
        <span style={{ fontSize: 26, animation: 'spin 2s linear infinite', display: 'inline-block' }}>⏳</span>
        <h3 style={{ margin: 0 }}>Analysing your recording</h3>
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 14 }}>
        <span
          title={fileName}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            maxWidth: 420, padding: '6px 14px',
            border: '1px solid rgba(239,124,0,0.35)', borderRadius: 999,
            background: 'rgba(239,124,0,0.08)',
            fontSize: 15, fontWeight: 700, color: '#111827',
          }}
        >
          <span aria-hidden>🎞️</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{fileName}</span>
        </span>
      </div>

      {/* Overall progress bar */}
      <div className="progress-track">
        <div className="progress-fill" style={{ width: pct + '%' }} data-testid="progress-fill" />
      </div>
      <p className="text-muted" style={{ fontSize: 12, marginBottom: 20 }}>{pct}% — {stageText}</p>

      {/* Per-task checklist */}
      <div style={{
        border: '1px solid rgba(239,124,0,0.2)',
        borderRadius: 10,
        overflow: 'hidden',
        width: '100%',
        maxWidth: 420,
        margin: '0 auto',
        background: '#fff',
      }}>
        {TASKS.map((task, idx) => {
          const status = taskStatus(pct, task.minPct, task.maxPct);
          const fill   = taskFill(pct, task.minPct, task.maxPct);
          const isLast = idx === TASKS.length - 1;

          return (
            <div key={task.label} style={{
              borderBottom: isLast ? 'none' : '1px solid rgba(0,0,0,0.06)',
              borderLeft: 'highlight' in task ? '3px solid #EF7C00' : undefined,
              background: 'highlight' in task ? 'rgba(239,124,0,0.06)' : undefined,
              position: 'relative',
              overflow: 'hidden',
            }}>
              {/* Tinted background for active/done rows */}
              {status === 'active' && (
                <div style={{
                  position: 'absolute', inset: 0,
                  width: Math.max(fill, 8) + '%',
                  background: 'linear-gradient(90deg,rgba(239,124,0,0.1),rgba(239,124,0,0.05))',
                  transition: 'width 0.25s linear',
                  zIndex: 0,
                }} />
              )}
              {status === 'done' && (
                <div style={{ position: 'absolute', inset: 0, background: 'rgba(16,185,129,0.05)', zIndex: 0 }} />
              )}

              <div style={{
                position: 'relative', zIndex: 1,
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '11px 16px',
              }}>
                <span style={{ fontSize: 16, flexShrink: 0, minWidth: 22, textAlign: 'center' }}>
                  {status === 'done'   ? '✅'
                  : status === 'active' ? '🔄'
                  :                      '⬜'}
                </span>
                <span style={{ fontSize: 15, flexShrink: 0 }}>{task.icon}</span>
                <span style={{
                  fontSize: 'highlight' in task ? 14 : 13,
                  fontWeight: status === 'active' || 'highlight' in task ? 700 : 400,
                  color: 'highlight' in task ? '#111827'
                       : status === 'done'   ? '#6b7280'
                       : status === 'active' ? '#111827'
                       :                      '#9ca3af',
                  flex: 1,
                }}>
                  {task.label}
                </span>
                {status === 'done'    && <span style={{ fontSize: 11, color: '#10b981', fontWeight: 600 }}>Done</span>}
                {status === 'active'  && (
                  fill > 0
                    ? <span style={{ fontSize: 12, color: '#EF7C00', fontWeight: 700 }}>{fill}%</span>
                    : <span style={{ fontSize: 12, color: '#EF7C00', fontWeight: 700, animation: 'pulse-dot 1s ease-in-out infinite' }}>●●●</span>
                )}
                {status === 'pending' && <span style={{ fontSize: 11, color: '#d1d5db' }}>Waiting</span>}
              </div>

              {/* Bottom progress line for active task */}
              {status === 'active' && (
                <div style={{ height: 2, background: 'rgba(239,124,0,0.12)' }}>
                  <div style={{
                    height: '100%', width: Math.max(fill, 8) + '%',
                    background: '#EF7C00',
                    transition: 'width 0.25s linear',
                    borderRadius: 2,
                  }} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
