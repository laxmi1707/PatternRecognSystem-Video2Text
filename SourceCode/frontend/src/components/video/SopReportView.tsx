import type { SOPResponse } from '../../types/knowledge';

interface SopReportViewProps {
  name: string;
  date: string;
  duration: string;
  videoUrl: string | null;
  report: SOPResponse;
  onBack: () => void;
}

export function SopReportView({ name, date, duration, videoUrl, report, onBack }: SopReportViewProps) {
  return (
    <div className="results">
      <div className="results-head">
        <div>
          <h6 style={{ color: 'var(--color-accent-700)' }}>Generated SOP</h6>
          <h1 style={{ marginBottom: 4 }}>{report.title || name}</h1>
          <p className="text-muted" style={{ margin: 0 }}>
            {name} &middot; {date} &middot; {duration}
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onBack}>Back to results</button>
      </div>

      <p className="results-summary">{report.purpose}</p>

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

          {report.prerequisites.length > 0 && (
            <div style={{ marginTop: 'var(--space-4)' }}>
              <h4>Prerequisites</h4>
              <ul className="plain-list">
                {report.prerequisites.map(item => <li key={item}>{item}</li>)}
              </ul>
            </div>
          )}
        </div>

        <div className="workflow-steps">
          {report.steps.map(step => (
            <div className="workflow-step" key={step.number}>
              <div className="workflow-step-num">{step.number}</div>
              <div className="workflow-step-body">
                <div className="workflow-step-head">
                  <h4>{step.title}</h4>
                  <span className="tag tag-outline">{step.time_range}</span>
                </div>
                <p className="text-muted">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {report.expected_outcome && (
        <div style={{ marginTop: 'var(--space-6)' }}>
          <h4>Expected outcome</h4>
          <p className="text-muted">{report.expected_outcome}</p>
        </div>
      )}

      {report.troubleshooting.length > 0 && (
        <div style={{ marginTop: 'var(--space-4)' }}>
          <h4>Troubleshooting</h4>
          <ul className="plain-list">
            {report.troubleshooting.map(item => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
