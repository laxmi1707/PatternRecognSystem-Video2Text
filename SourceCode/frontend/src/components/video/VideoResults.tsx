import { useState } from 'react';
import type { AnalysisResult } from '../../types/analysis';
import { WorkflowSteps } from './WorkflowSteps';
import { KnowledgePanel } from './KnowledgePanel';
import { ModelComparison } from './ModelComparison';

interface VideoResultsProps {
  result: AnalysisResult;
  onAnalyzeAnother: () => void;
}

export function VideoResults({ result, onAnalyzeAnother }: VideoResultsProps) {
  const [selectedModel, setSelectedModel] = useState<string | null>(result.bestModel);

  const displaySteps =
    selectedModel && result.allResults[selectedModel]
      ? result.allResults[selectedModel]
      : result.steps;

  const displayLabel = selectedModel
    ? selectedModel.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    : null;

  return (
    <div className="results">
      <div className="results-head">
        <div>
          <h6 style={{ color: 'var(--color-accent-700)' }}>Analysis complete</h6>
          <h1 style={{ marginBottom: 4 }}>{result.name}</h1>
          <p className="text-muted" style={{ margin: 0 }}>
            {result.date} &middot; {result.duration} &middot; {result.stepCount} steps
            {displayLabel && <> &middot; Viewing: <strong>{displayLabel}</strong></>}
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onAnalyzeAnother}>Analyze another video</button>
      </div>

      <p className="results-summary">{result.summary}</p>

      {result.modelComparison.length > 0 && (
        <ModelComparison
          comparison={result.modelComparison}
          bestModel={result.bestModel}
          allResults={result.allResults}
          onSelectModel={setSelectedModel}
          selectedModel={selectedModel}
        />
      )}

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
        <WorkflowSteps steps={displaySteps} />
      </div>

      <KnowledgePanel jobId={result.jobId || result.id} />
    </div>
  );
}
