import { useState, useEffect } from 'react';
import { apiPost, ApiError } from '../../services/api/client';

interface SOPStep {
  number: number;
  title: string;
  description: string;
  time_range: string;
  delay_s?: number | null;
  screen_output?: string[];
  screen_removed?: string[];
  risk_level?: 'high' | 'medium' | 'none';
  risk_reason?: string;
}

const riskBadgeStyle: Record<string, React.CSSProperties> = {
  high: {
    display: 'inline-block', marginLeft: 8, padding: '1px 8px',
    borderRadius: 4, fontSize: 11, fontWeight: 700,
    background: '#fef2f2', color: '#dc2626', border: '1px solid #fca5a5',
  },
  medium: {
    display: 'inline-block', marginLeft: 8, padding: '1px 8px',
    borderRadius: 4, fontSize: 11, fontWeight: 700,
    background: '#fffbeb', color: '#d97706', border: '1px solid #fcd34d',
  },
};

interface SOPResponse {
  title: string;
  purpose: string;
  prerequisites: string[];
  steps: SOPStep[];
  expected_outcome: string;
  troubleshooting: string[];
  platform?: string;
  source_recording?: string;
  generated_at?: string;
}

const screenTextStyle = {
  background: '#1e1e1e', color: '#d4d4d4',
  padding: '8px 12px', borderRadius: 4, fontSize: 13,
  marginTop: 4, marginBottom: 0, overflow: 'auto', whiteSpace: 'pre-wrap' as const,
};

interface RunbookStep {
  number: number;
  action: string;
  details: string;
  command: string;
}

interface RunbookResponse {
  title: string;
  description: string;
  when_to_use: string;
  prerequisites: string[];
  steps: RunbookStep[];
  verification: string[];
  rollback: string[];
}

interface KnowledgePanelProps {
  jobId: string;
}

export function KnowledgePanel({ jobId }: KnowledgePanelProps) {
  const [sop, setSop] = useState<SOPResponse | null>(null);
  const [runbook, setRunbook] = useState<RunbookResponse | null>(null);
  const [loading, setLoading] = useState<'sop' | 'runbook' | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setSop(null); setRunbook(null); setError(null); }, [jobId]);

  function errorMessage(e: unknown, action: string): string {
    if (e instanceof ApiError) {
      if (e.status === 404) return `Analysis job not found — this recording may be from a previous session. Upload it again to generate a ${action}.`;
      if (e.status >= 500) return `Server error (${e.status}): ${e.detail}`;
      return e.detail;
    }
    return `Failed to generate ${action}. Is the backend running?`;
  }

  async function generateSOP() {
    setLoading('sop');
    setError(null);
    try {
      const result = await apiPost<SOPResponse>(`/knowledge/sop/${jobId}`);
      setSop(result);
    } catch (e) {
      setError(errorMessage(e, 'SOP'));
    } finally {
      setLoading(null);
    }
  }

  async function generateRunbook() {
    setLoading('runbook');
    setError(null);
    try {
      const result = await apiPost<RunbookResponse>(`/knowledge/runbook/${jobId}`);
      setRunbook(result);
    } catch (e) {
      setError(errorMessage(e, 'Runbook'));
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="knowledge-panel" style={{ marginTop: 'var(--space-6, 2rem)' }}>
      <h6 style={{
        fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase',
        color: '#EF7C00', marginBottom: 6,
      }}>
        Knowledge Generation
      </h6>
      <p style={{ marginBottom: 'var(--space-3, 1rem)', fontSize: 14, color: '#4b5563' }}>
        Generate structured documentation from the classified activities.
      </p>

      <div style={{ display: 'flex', gap: 10, marginBottom: 'var(--space-4, 1.5rem)', flexWrap: 'wrap' }}>
        <button
          onClick={generateSOP}
          disabled={loading !== null}
          style={{
            padding: '10px 20px',
            borderRadius: 8,
            border: 'none',
            cursor: loading !== null ? 'wait' : 'pointer',
            fontWeight: 700,
            fontSize: 14,
            background: loading === 'sop'
              ? 'rgba(239,124,0,0.5)'
              : 'linear-gradient(135deg, #EF7C00, #d46a00)',
            color: '#fff',
            boxShadow: '0 2px 8px rgba(239,124,0,0.35)',
            transition: 'opacity 0.15s',
            opacity: loading !== null && loading !== 'sop' ? 0.5 : 1,
            display: 'flex', alignItems: 'center', gap: 7,
          }}
        >
          <span style={{ fontSize: 16 }}>📄</span>
          {loading === 'sop' ? 'Generating...' : sop ? 'Regenerate SOP' : 'Generate SOP'}
        </button>
        <button
          onClick={generateRunbook}
          disabled={loading !== null}
          style={{
            padding: '10px 20px',
            borderRadius: 8,
            border: '2px solid #EF7C00',
            cursor: loading !== null ? 'wait' : 'pointer',
            fontWeight: 700,
            fontSize: 14,
            background: loading === 'runbook'
              ? 'rgba(239,124,0,0.15)'
              : 'transparent',
            color: '#EF7C00',
            transition: 'opacity 0.15s, background 0.15s',
            opacity: loading !== null && loading !== 'runbook' ? 0.5 : 1,
            display: 'flex', alignItems: 'center', gap: 7,
          }}
        >
          <span style={{ fontSize: 16 }}>📋</span>
          {loading === 'runbook' ? 'Generating...' : runbook ? 'Regenerate Runbook' : 'Generate Runbook'}
        </button>
      </div>

      {error && (
        <p style={{ color: 'var(--color-error, red)', fontSize: 14 }}>{error}</p>
      )}

      {sop && (
        <div className="knowledge-doc" style={{
          background: '#ffffff',
          border: '1px solid #e5e7eb',
          borderRadius: 8,
          padding: 'var(--space-4, 1.5rem)',
          marginBottom: 'var(--space-4, 1.5rem)',
          color: '#111827',
          position: 'relative',
          zIndex: 1,
        }}>
          <h3 style={{ marginTop: 0 }}>{sop.title}</h3>
          {sop.platform && (
            <p style={{ fontSize: 14, color: '#4b5563' }}>
              <strong>Application / platform:</strong> {sop.platform}<br />
              <strong>Source recording:</strong> {sop.source_recording}<br />
              <strong>Generated:</strong> {sop.generated_at}
            </p>
          )}
          <p><strong>Procedure:</strong></p>
          <ol>
            {sop.steps.map((step) => (
              <li key={step.number} style={{ marginBottom: 8 }}>
                <strong>{step.title}</strong>
                {step.time_range && <span className="text-muted" style={{ fontSize: 12, marginLeft: 8 }}>[{step.time_range}]</span>}
                {(step.risk_level === 'high' || step.risk_level === 'medium') && (
                  <span style={riskBadgeStyle[step.risk_level]} title={step.risk_reason}>
                    {step.risk_level === 'high' ? '⚠ HIGH RISK' : '⚠ MEDIUM RISK'}
                  </span>
                )}
                <br />
                {(step.risk_level === 'high' || step.risk_level === 'medium') && step.risk_reason && (
                  <span style={{ fontSize: 12, color: step.risk_level === 'high' ? '#dc2626' : '#d97706' }}>
                    {step.risk_reason}
                  </span>
                )}
                <br />
                <span style={{ fontSize: 14 }}>{step.description}</span>
                {step.screen_output && step.screen_output.length > 0 && (
                  <pre style={screenTextStyle}>{step.screen_output.join('\n')}</pre>
                )}
                {step.screen_removed && step.screen_removed.length > 0 && (
                  <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>
                    <em>No longer shown:</em> {step.screen_removed.join(' · ')}
                  </div>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      {runbook && (
        <div className="knowledge-doc" style={{
          background: '#ffffff',
          border: '1px solid #e5e7eb',
          borderRadius: 8,
          padding: 'var(--space-4, 1.5rem)',
          color: '#111827',
          position: 'relative',
          zIndex: 1,
        }}>
          <h3 style={{ marginTop: 0 }}>{runbook.title}</h3>
          <p>{runbook.description}</p>
          <p><strong>When to use:</strong> {runbook.when_to_use}</p>
          <p><strong>Prerequisites:</strong></p>
          <ul>{runbook.prerequisites.map((p, i) => <li key={i}>{p}</li>)}</ul>
          <p><strong>Steps:</strong></p>
          <ol>
            {runbook.steps.map((step) => (
              <li key={step.number} style={{ marginBottom: 8 }}>
                <strong>{step.action}</strong>
                <br />
                <span style={{ fontSize: 14 }}>{step.details}</span>
                {step.command && (
                  <pre style={{
                    background: '#1e1e1e', color: '#d4d4d4',
                    padding: '8px 12px', borderRadius: 4, fontSize: 13,
                    marginTop: 4, overflow: 'auto',
                  }}>
                    {step.command}
                  </pre>
                )}
              </li>
            ))}
          </ol>
          <p><strong>Verification:</strong></p>
          <ul>{runbook.verification.map((v, i) => <li key={i}>{v}</li>)}</ul>
          {runbook.rollback.length > 0 && (
            <>
              <p><strong>Rollback:</strong></p>
              <ul>{runbook.rollback.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
