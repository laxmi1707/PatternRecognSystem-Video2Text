import { useState } from 'react';
import type { AnalysisResult } from '../../types/analysis';
import { WorkflowSteps } from './WorkflowSteps';
import { KnowledgePanel } from './KnowledgePanel';
import { ModelComparison } from './ModelComparison';
import { ReportView } from './ReportView';

interface VideoResultsProps {
  result: AnalysisResult;
  onAnalyzeAnother: () => void;
}

type ViewMode = 'screen' | 'report';

export function VideoResults({ result, onAnalyzeAnother }: VideoResultsProps) {
  const [selectedModel, setSelectedModel] = useState<string | null>(result.bestModel);
  const [showComparison, setShowComparison] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('screen');

  const displaySteps =
    selectedModel && result.allResults[selectedModel]
      ? result.allResults[selectedModel]
      : result.steps;

  const displayLabel = selectedModel
    ? selectedModel.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    : null;

  const toggleStyle = (active: boolean): React.CSSProperties => ({
    padding: '8px 20px',
    borderRadius: 8,
    border: active ? 'none' : '1px solid #d1d5db',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 13,
    background: active ? 'linear-gradient(135deg, #EF7C00, #d46a00)' : '#fff',
    color: active ? '#fff' : '#374151',
    transition: 'all 0.15s',
  });

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
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10 }}>
          <button className="btn btn-secondary" onClick={onAnalyzeAnother} style={{background:'linear-gradient(135deg,#EF7C00,#d46a00)',color:'#fff',border:'none',fontWeight:600}}>Analyze another video</button>
          <div style={{ display: 'flex', gap: 6, background: '#f3f4f6', borderRadius: 10, padding: 4 }}>
            <button style={toggleStyle(viewMode === 'screen')} onClick={() => setViewMode('screen')}>
              🖥 Screen View
            </button>
            <button style={toggleStyle(viewMode === 'report')} onClick={() => setViewMode('report')}>
              📝 Report View
            </button>
          </div>
        </div>
      </div>

      <p className="results-summary">{result.summary}</p>

      {viewMode === 'report' && (
        <ReportView jobId={result.jobId || result.id} videoName={result.name} />
      )}

      {viewMode === 'screen' && result.modelComparison.length > 0 && (
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

      {viewMode === 'screen' && (
        <>
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
        </>
      )}
    </div>
  );
}
