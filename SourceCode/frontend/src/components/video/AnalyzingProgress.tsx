interface AnalyzingProgressProps {
  fileName: string;
  videoUrl: string | null;
  progress: number;
  showPreview?: boolean;
}

export function AnalyzingProgress({ fileName, videoUrl, progress, showPreview = true }: AnalyzingProgressProps) {
  const pct = Math.round(progress);
  return (
    <div className="analyzing">
      {showPreview && videoUrl && (
        <video src={videoUrl} muted className="analyzing-preview" />
      )}
      <div className="spinner" role="status" aria-label="Analyzing" />
      <h3>Analyzing your recording</h3>
      <p className="text-muted">{fileName}</p>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: pct + '%' }} data-testid="progress-fill" />
      </div>
      <p className="text-muted" style={{ fontSize: 12 }}>{pct}% - reading interface actions</p>
    </div>
  );
}
