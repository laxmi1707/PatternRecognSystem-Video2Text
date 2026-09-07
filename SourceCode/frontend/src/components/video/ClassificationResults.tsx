import type { ClassificationResult } from '../../types/analysis';

interface ClassificationResultsProps {
  result: ClassificationResult;
  onAnalyzeAnother: () => void;
  onViewReport: () => void;
}

export function ClassificationResults({ result, onAnalyzeAnother, onViewReport }: ClassificationResultsProps) {
  const ranked = Object.entries(result.probabilities).sort((a, b) => b[1] - a[1]);
  const maxProb = Math.max(...ranked.map(([, p]) => p), 0.01);

  return (
    <div className="results">
      <div className="results-head">
        <div>
          <h6 style={{ color: 'var(--color-accent-700)' }}>Classification complete</h6>
          <h1 style={{ marginBottom: 4 }}>{result.name}</h1>
          <p className="text-muted" style={{ margin: 0 }}>
            {result.date} &middot; {result.duration}
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onAnalyzeAnother}>Analyze another video</button>
      </div>

      <div className="results-grid">
        <div>
          {result.videoUrl ? (
            <video src={result.videoUrl} controls className="results-video" />
          ) : (
            <div className="halftone results-video-placeholder">
              <span className="text-muted" style={{ fontFamily: 'monospace', fontSize: 11 }}>
                original recording not stored
              </span>
            </div>
          )}
        </div>

        <div>
          <div className="classification-headline">
            <span className="tag tag-accent classification-label">{result.label}</span>
            <span className="classification-confidence">{(result.confidence * 100).toFixed(0)}% confidence</span>
          </div>

          <h4 style={{ marginTop: 'var(--space-6)' }}>Class probabilities</h4>
          <div className="bar-chart">
            {ranked.map(([label, prob]) => (
              <div className="bar-row" key={label}>
                <span className="bar-label">{label}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(prob / maxProb) * 100}%` }} />
                </div>
                <span className="bar-count">{(prob * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>

          <button className="btn btn-primary btn-block" style={{ marginTop: 'var(--space-6)' }} onClick={onViewReport}>
            View full report (SOP)
          </button>
        </div>
      </div>
    </div>
  );
}
