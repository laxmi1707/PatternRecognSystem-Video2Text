import { useState } from 'react';
import { apiPost } from '../../services/api/client';

interface SOPStep {
  number: number;
  title: string;
  description: string;
  time_range: string;
}

interface SOPResponse {
  title: string;
  purpose: string;
  prerequisites: string[];
  steps: SOPStep[];
  expected_outcome: string;
  troubleshooting: string[];
}

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

  async function generateSOP() {
    setLoading('sop');
    setError(null);
    try {
      const result = await apiPost<SOPResponse>(`/knowledge/sop/${jobId}`);
      setSop(result);
    } catch (e) {
      setError('Failed to generate SOP. Is the backend running?');
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
      setError('Failed to generate Runbook. Is the backend running?');
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="knowledge-panel" style={{ marginTop: 'var(--space-6, 2rem)' }}>
      <h6 style={{ color: 'var(--color-accent-700)', marginBottom: 'var(--space-2, 0.5rem)' }}>
        Knowledge Generation
      </h6>
      <p className="text-muted" style={{ marginBottom: 'var(--space-3, 1rem)', fontSize: 14 }}>
        Generate structured documentation from the classified activities.
      </p>

      <div style={{ display: 'flex', gap: 'var(--space-3, 1rem)', marginBottom: 'var(--space-4, 1.5rem)' }}>
        <button
          className="btn btn-secondary"
          onClick={generateSOP}
          disabled={loading !== null}
        >
          {loading === 'sop' ? 'Generating...' : 'Generate SOP'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={generateRunbook}
          disabled={loading !== null}
        >
          {loading === 'runbook' ? 'Generating...' : 'Generate Runbook'}
        </button>
      </div>

      {error && (
        <p style={{ color: 'var(--color-error, red)', fontSize: 14 }}>{error}</p>
      )}

      {sop && (
        <div className="knowledge-doc" style={{
          background: 'var(--color-surface-50, #f9fafb)',
          border: '1px solid var(--color-border, #e5e7eb)',
          borderRadius: 8,
          padding: 'var(--space-4, 1.5rem)',
          marginBottom: 'var(--space-4, 1.5rem)',
        }}>
          <h3 style={{ marginTop: 0 }}>{sop.title}</h3>
          <p><strong>Purpose:</strong> {sop.purpose}</p>
          <p><strong>Prerequisites:</strong></p>
          <ul>{sop.prerequisites.map((p, i) => <li key={i}>{p}</li>)}</ul>
          <p><strong>Procedure:</strong></p>
          <ol>
            {sop.steps.map((step) => (
              <li key={step.number} style={{ marginBottom: 8 }}>
                <strong>{step.title}</strong>
                {step.time_range && <span className="text-muted" style={{ fontSize: 12, marginLeft: 8 }}>[{step.time_range}]</span>}
                <br />
                <span style={{ fontSize: 14 }}>{step.description}</span>
              </li>
            ))}
          </ol>
          <p><strong>Expected Outcome:</strong> {sop.expected_outcome}</p>
          {sop.troubleshooting.length > 0 && (
            <>
              <p><strong>Troubleshooting:</strong></p>
              <ul>{sop.troubleshooting.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </>
          )}
        </div>
      )}

      {runbook && (
        <div className="knowledge-doc" style={{
          background: 'var(--color-surface-50, #f9fafb)',
          border: '1px solid var(--color-border, #e5e7eb)',
          borderRadius: 8,
          padding: 'var(--space-4, 1.5rem)',
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
