import type { ClassificationResult, SopReport } from '../types/analysis';
import { SopReportView } from '../components/video/SopReportView';

interface ReportPageProps {
  target: ClassificationResult;
  report: SopReport | null;
  loading: boolean;
  error: string | null;
  onBack: () => void;
}

export function ReportPage({ target, report, loading, error, onBack }: ReportPageProps) {
  if (error) {
    return (
      <div className="page page-center">
        <p className="dropzone-error" role="alert">{error}</p>
        <button className="btn btn-secondary" style={{ marginTop: 'var(--space-4)' }} onClick={onBack}>
          Back to results
        </button>
      </div>
    );
  }

  return (
    <div className="page page-wide">
      {loading || !report ? (
        <div className="page-center">
          <div className="spinner" role="status" aria-label="Generating report" />
          <p className="text-muted">Generating report…</p>
        </div>
      ) : (
        <SopReportView
          name={target.name}
          date={target.date}
          duration={target.duration}
          videoUrl={target.videoUrl}
          summary={report.summary}
          steps={report.steps}
          onBack={onBack}
        />
      )}
    </div>
  );
}
