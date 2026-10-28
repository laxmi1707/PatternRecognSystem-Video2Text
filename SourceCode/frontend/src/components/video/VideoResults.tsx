import { useRef, useState } from 'react';
import { BASE_URL } from '../../services/api/client';
import type { AnalysisResult } from '../../types/analysis';
import { WorkflowSteps } from './WorkflowSteps';
import { KnowledgePanel } from './KnowledgePanel';
import { ModelComparison } from './ModelComparison';
import { ReportView } from './ReportView';
import { DetectedSteps } from './DetectedSteps';
import { useDetection } from '../../hooks/useDetection';

interface VideoResultsProps {
  result: AnalysisResult;
  onAnalyzeAnother: () => void;
}

type ViewMode = 'screen' | 'report';

export function VideoResults({ result, onAnalyzeAnother }: VideoResultsProps) {
  const [selectedModel, setSelectedModel] = useState<string | null>(result.bestModel);
  const [showComparison, setShowComparison] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('screen');
  const detection = useDetection(result.detectorJobId);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoTime, setVideoTime] = useState<number | undefined>(undefined);

  // a detected step's time: play the recording from there, with the video in view
  const seek = (t: number) => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = t;
    setVideoTime(t);
    v.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
    void v.play?.()?.catch?.(() => undefined);
  };

  // the upload's own object URL, or the backend's stream when it is gone (history)
  const videoSrc = result.videoUrl ?? (result.id ? `${BASE_URL}/videos/${result.id}/stream` : null);

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
          <h1 style={{ marginBottom: 4, fontSize: 22, wordBreak: 'break-all' }}>{result.name}</h1>
          <p style={{ margin: 0, fontSize: 13, color: '#4b5563' }}>
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
              {videoSrc ? (
                <video
                  ref={videoRef}
                  src={videoSrc}
                  controls
                  className="results-video"
                  onTimeUpdate={e => setVideoTime(e.currentTarget.currentTime)}
                />
              ) : (
                <div className="halftone results-video-placeholder">
                  <span className="text-muted" style={{ fontFamily: 'monospace', fontSize: 11 }}>
                    original recording not available
                  </span>
                </div>
              )}
            </div>
            <WorkflowSteps steps={displaySteps} />
          </div>

          <DetectedSteps
            jobId={result.detectorJobId}
            job={detection.job}
            error={detection.error}
            onSeek={videoSrc ? seek : undefined}
            currentTime={videoTime}
          />

          <KnowledgePanel jobId={result.jobId || result.id} detectedSteps={detection.job?.result?.steps} />
        </>
      )}
    </div>
  );
}
