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
        {riskySteps.length} {riskySteps.length > 1 ? 'anomalies' : 'anomaly'} detected
      </p>
      {riskySteps.map(step => {
        const badge = RISK_BADGE[step.risk_level!];
        const borderColor = step.risk_level === 'high' ? '#dc2626' : '#d97706';
        return (
          <div className="workflow-step" key={step.n} style={{ borderLeft: `3px solid ${borderColor}`, paddingLeft: 8, marginBottom: 10 }}>
            <div className="workflow-step-num" style={{ background: borderColor, fontSize: 11, width: 20, height: 20, minWidth: 20 }}>{step.n}</div>
            <div className="workflow-step-body" style={{ flex: 1 }}>
              <div className="workflow-step-head" style={{ flexWrap: 'wrap', gap: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>
                  {step.title}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  {badge && <span style={badge.style} title={step.risk_reason}>{badge.label}</span>}
                  <span className="tag tag-outline" style={{ fontSize: 11 }}>{step.time}</span>
                </div>
              </div>
              {step.risk_reason && (
                <p style={{ fontSize: 11, color: borderColor, margin: '2px 0 3px', fontWeight: 500 }}>{step.risk_reason}</p>
              )}
              <p className="text-muted" style={{ fontSize: 11, margin: 0, lineHeight: 1.4 }}>{step.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
