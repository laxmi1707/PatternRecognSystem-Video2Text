import type { WorkflowStep } from '../../types/analysis';

interface WorkflowStepsProps {
  steps: WorkflowStep[];
}

export function WorkflowSteps({ steps }: WorkflowStepsProps) {
  return (
    <div className="workflow-steps">
      {steps.map(step => (
        <div className="workflow-step" key={step.n}>
          <div className="workflow-step-num">{step.n}</div>
          <div className="workflow-step-body">
            <div className="workflow-step-head">
              <h4>{step.title}</h4>
              <span className="tag tag-outline">{step.time}</span>
            </div>
            <p className="text-muted">{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
