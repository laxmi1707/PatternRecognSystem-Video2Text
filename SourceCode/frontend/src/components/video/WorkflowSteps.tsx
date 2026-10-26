import type { WorkflowStep } from '../../types/analysis';

interface WorkflowStepsProps {
  steps: WorkflowStep[];
}

const RISK_BADGE: Record<string, { label: string; style: React.CSSProperties }> = {
  high: {
    label: '⚠ HIGH RISK',
    style: { display: 'inline-block', marginLeft: 8, padding: '1px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, background: '#fef2f2', color: '#dc2626', border: '1px solid #fca5a5' },
  },
  medium: {
    label: '⚠ MEDIUM RISK',
    style: { display: 'inline-block', marginLeft: 8, padding: '1px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, background: '#fffbeb', color: '#d97706', border: '1px solid #fcd34d' },
  },
};

export function WorkflowSteps({ steps }: WorkflowStepsProps) {
  const riskySteps = steps.filter(s => s.risk_level && s.risk_level !== 'none');

  if (riskySteps.length === 0) {
    return (
      <div className="workflow-steps">
        <p className="text-muted" style={{ padding: '16px 0', textAlign: 'center' }}>No anomalies detected in this recording.</p>
      </div>
    );
  }

  return (
    <div className="workflow-steps">
      <p style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>
        {riskySteps.length} anomaly{riskySteps.length > 1 ? 'ies' : ''} detected
      </p>
      {riskySteps.map(step => {
        const badge = RISK_BADGE[step.risk_level!];
        return (
          <div className="workflow-step" key={step.n} style={{ borderLeft: `3px solid ${step.risk_level === 'high' ? '#dc2626' : '#d97706'}`, paddingLeft: 8 }}>
            <div className="workflow-step-num" style={{ background: step.risk_level === 'high' ? '#dc2626' : '#d97706' }}>{step.n}</div>
            <div className="workflow-step-body">
              <div className="workflow-step-head">
                <h4>
                  {step.title}
                  {badge && <span style={badge.style} title={step.risk_reason}>{badge.label}</span>}
                </h4>
                <span className="tag tag-outline">{step.time}</span>
              </div>
              {step.risk_reason && (
                <p style={{ fontSize: 12, color: step.risk_level === 'high' ? '#dc2626' : '#d97706', margin: '2px 0 4px' }}>{step.risk_reason}</p>
              )}
              <p className="text-muted">{step.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
