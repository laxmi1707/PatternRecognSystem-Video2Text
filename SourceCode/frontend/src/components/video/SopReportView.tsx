import type { WorkflowStep } from '../../types/analysis';
import { WorkflowSteps } from './WorkflowSteps';

interface SopReportViewProps {
  name: string;
  date: string;
  duration: string;
  videoUrl: string | null;
  summary: string;
  steps: WorkflowStep[];
  onBack: () => void;
}

export function SopReportView({ name, date, duration, videoUrl, summary, steps, onBack }: SopReportViewProps) {
  return (
    <div className="results">
      <div className="results-head">
        <div>
          <h6 style={{ color: 'var(--color-accent-700)' }}>SOP report</h6>
          <h1 style={{ marginBottom: 4 }}>{name}</h1>
          <p className="text-muted" style={{ margin: 0 }}>
            {date} &middot; {duration} &middot; {steps.length} steps
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onBack}>Back to results</button>
      </div>

      <p className="results-summary">{summary}</p>

      <div className="results-grid">
        <div>
          {videoUrl ? (
            <video src={videoUrl} controls className="results-video" />
          ) : (
            <div className="halftone results-video-placeholder">
              <span className="text-muted" style={{ fontFamily: 'monospace', fontSize: 11 }}>
                original recording not stored
              </span>
            </div>
          )}
        </div>
        <WorkflowSteps steps={steps} />
      </div>
    </div>
  );
}
