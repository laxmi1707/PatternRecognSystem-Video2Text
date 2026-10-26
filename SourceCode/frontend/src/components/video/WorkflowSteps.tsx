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
  return (
    <div className="workflow-steps">
      {steps.map(step => {
        const badge = step.risk_level && step.risk_level !== 'none' ? RISK_BADGE[step.risk_level] : null;
        return (
          <div className="workflow-step" key={step.n} style={badge ? { borderLeft: `3px solid ${step.risk_level === 'high' ? '#dc2626' : '#d97706'}`, paddingLeft: 8 } : undefined}>
            <div className="workflow-step-num" style={badge ? { background: step.risk_level === 'high' ? '#dc2626' : '#d97706' } : undefined}>{step.n}</div>
            <div className="workflow-step-body">
              <div className="workflow-step-head">
                <h4>
                  {step.title}
                  {badge && <span style={badge.style} title={step.risk_reason}>{badge.label}</span>}
                </h4>
                <span className="tag tag-outline">{step.time}</span>
              </div>
              {badge && step.risk_reason && (
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
