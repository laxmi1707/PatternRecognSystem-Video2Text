import type { AnalysisResult } from '../../types/analysis';
import { WorkflowSteps } from './WorkflowSteps';

interface VideoResultsProps {
  result: AnalysisResult;
  onAnalyzeAnother: () => void;
}

export function VideoResults({ result, onAnalyzeAnother }: VideoResultsProps) {
  return (
    <div className="results">
      <div className="results-head">
        <div>
          <h6 style={{ color: 'var(--color-accent-700)' }}>Analysis complete</h6>
          <h1 style={{ marginBottom: 4 }}>{result.name}</h1>
          <p className="text-muted" style={{ margin: 0 }}>
            {result.date} &middot; {result.duration} &middot; {result.stepCount} steps
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onAnalyzeAnother}>Analyze another video</button>
      </div>

      <p className="results-summary">{result.summary}</p>

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
        <WorkflowSteps steps={result.steps} />
      </div>
    </div>
  );
}
