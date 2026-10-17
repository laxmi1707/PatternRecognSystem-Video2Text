import { useState } from 'react';
import type { AnalysisResult } from '../../types/analysis';
import { WorkflowSteps } from './WorkflowSteps';
import { KnowledgePanel } from './KnowledgePanel';
import { ModelComparison } from './ModelComparison';
import { DetectedSteps } from './DetectedSteps';
import { useDetection } from '../../hooks/useDetection';

interface VideoResultsProps {
  result: AnalysisResult;
  onAnalyzeAnother: () => void;
}

export function VideoResults({ result, onAnalyzeAnother }: VideoResultsProps) {
  const [selectedModel, setSelectedModel] = useState<string | null>(result.bestModel);
  const [showComparison, setShowComparison] = useState(false);
  const detection = useDetection(result.detectorJobId);

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
        <button className="btn btn-secondary" onClick={onAnalyzeAnother} style={{background:'linear-gradient(135deg,#EF7C00,#d46a00)',color:'#fff',border:'none',fontWeight:600}}>Analyze another video</button>
      </div>

      <p className="results-summary">{result.summary}</p>

      {result.modelComparison.length > 0 && (
        <div style={{ marginBottom: 'var(--space-4, 1.5rem)' }}>
          <button
            onClick={() => setShowComparison(v => !v)}
            style={{
              fontSize: 13, fontWeight: 600, cursor: 'pointer',
              padding: '8px 18px', borderRadius: 8, border: 'none',
              background: showComparison
                ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                : 'linear-gradient(135deg, #3b82f6, #6366f1)',
              color: '#fff',
              boxShadow: '0 2px 8px rgba(99,102,241,0.35)',
              transition: 'opacity 0.15s',
            }}
          >
            {showComparison ? '▲ Hide Model Comparison' : `▼ Show Model Comparison (${result.modelComparison.length} classifiers)`}
          </button>
          {showComparison && (
            <ModelComparison
              comparison={result.modelComparison}
              bestModel={result.bestModel}
              allResults={result.allResults}
              onSelectModel={setSelectedModel}
              selectedModel={selectedModel}
            />
          )}
        </div>
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

      <DetectedSteps jobId={result.detectorJobId} job={detection.job} error={detection.error} />

      <KnowledgePanel jobId={result.jobId || result.id} detectedSteps={detection.job?.result?.steps} />
    </div>
  );
}
