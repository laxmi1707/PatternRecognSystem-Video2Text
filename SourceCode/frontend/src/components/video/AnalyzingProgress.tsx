interface AnalyzingProgressProps {
  fileName: string;
  videoUrl: string | null;
  progress: number;
  showPreview?: boolean;
  phase?: 'uploading' | 'processing';
  onCancel?: () => void;
}

const PHASE_COPY = {
  uploading: { heading: 'Uploading your recording', caption: 'sending your file' },
  processing: { heading: 'Analyzing your recording', caption: 'reading interface actions' },
};

export function AnalyzingProgress({
  fileName, videoUrl, progress, showPreview = true, phase = 'processing', onCancel,
}: AnalyzingProgressProps) {
  const pct = Math.round(progress);
  const copy = PHASE_COPY[phase];
  return (
    <div className="analyzing">
      {showPreview && videoUrl && (
        <video src={videoUrl} muted className="analyzing-preview" />
      )}
      <div className="spinner" role="status" aria-label="Analyzing" />
      <h3>{copy.heading}</h3>
      <p className="text-muted">{fileName}</p>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: pct + '%' }} data-testid="progress-fill" />
      </div>
      <p className="text-muted" style={{ fontSize: 12 }}>{pct}% - {copy.caption}</p>
      {onCancel && (
        <button className="btn btn-secondary" style={{ marginTop: 'var(--space-4)' }} onClick={onCancel}>
          Cancel
        </button>
      )}
    </div>
  );
}
