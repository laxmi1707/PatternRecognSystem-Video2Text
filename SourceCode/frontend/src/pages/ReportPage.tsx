import type { ClassificationResult, SopReport } from '../types/analysis';
import { SopReportView } from '../components/video/SopReportView';

interface ReportPageProps {
  target: ClassificationResult;
  report: SopReport | null;
  loading: boolean;
  onBack: () => void;
}

export function ReportPage({ target, report, loading, onBack }: ReportPageProps) {
  return (
    <div className="page page-wide">
      {loading || !report ? (
        <div className="page-center">
          <div className="spinner" />
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
