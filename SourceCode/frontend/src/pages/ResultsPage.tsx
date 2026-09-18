import type { AnalysisResult } from '../types/analysis';
import { VideoResults } from '../components/video/VideoResults';
import { ClassificationResults } from '../components/video/ClassificationResults';

interface ResultsPageProps {
  result: AnalysisResult;
  onAnalyzeAnother: () => void;
  onViewReport: () => void;
}

export function ResultsPage({ result, onAnalyzeAnother, onViewReport }: ResultsPageProps) {
  return (
    <div className="page page-wide">
      <ClassificationResults result={result} onViewReport={onViewReport} />
      <VideoResults result={result} onAnalyzeAnother={onAnalyzeAnother} />
    </div>
  );
}
