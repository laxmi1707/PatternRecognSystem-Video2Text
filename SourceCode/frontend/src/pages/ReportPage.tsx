import { useEffect, useState } from 'react';
import type { AnalysisResult } from '../types/analysis';
import type { SOPResponse } from '../types/knowledge';
import { fetchSopReport } from '../services/api/evaluationService';
import { SopReportView } from '../components/video/SopReportView';

interface ReportPageProps {
  target: AnalysisResult;
  onBack: () => void;
}

export function ReportPage({ target, onBack }: ReportPageProps) {
  const [report, setReport] = useState<SOPResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setReport(null);
    setError(null);

    const jobId = target.jobId;
    if (jobId === undefined) {
      setError('This analysis has no job attached, so a report cannot be generated.');
      return;
    }

    fetchSopReport(jobId)
      .then(result => { if (!cancelled) setReport(result); })
      .catch(() => {
        if (!cancelled) setError('Could not generate the report. Is the backend running?');
      });

    return () => { cancelled = true; };
  }, [target]);

  if (error) {
    return (
      <div className="page page-center">
        <p className="dropzone-error" role="alert">{error}</p>
        <button className="btn btn-secondary" onClick={onBack}>Back to results</button>
      </div>
    );
  }

  return (
    <div className="page page-wide">
      {!report ? (
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
          report={report}
          onBack={onBack}
        />
      )}
    </div>
  );
}
