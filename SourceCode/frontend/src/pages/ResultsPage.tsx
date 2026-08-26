import type { AnalysisResult } from '../types/analysis';
import { VideoResults } from '../components/video/VideoResults';

interface ResultsPageProps {
  result: AnalysisResult;
  onAnalyzeAnother: () => void;
}

export function ResultsPage({ result, onAnalyzeAnother }: ResultsPageProps) {
  return (
    <div className="page page-wide">
      <VideoResults result={result} onAnalyzeAnother={onAnalyzeAnother} />
    </div>
  );
}
