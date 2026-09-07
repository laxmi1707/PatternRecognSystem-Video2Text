import type { ClassificationResult } from '../types/analysis';
import { ClassificationResults } from '../components/video/ClassificationResults';

interface ResultsPageProps {
  result: ClassificationResult;
  onAnalyzeAnother: () => void;
  onViewReport: () => void;
}

export function ResultsPage({ result, onAnalyzeAnother, onViewReport }: ResultsPageProps) {
  return (
    <div className="page page-wide">
      <ClassificationResults result={result} onAnalyzeAnother={onAnalyzeAnother} onViewReport={onViewReport} />
    </div>
  );
}
