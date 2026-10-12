import { AnalyzingProgress } from '../components/video/AnalyzingProgress';

interface AnalyzingPageProps {
  fileName: string;
  videoUrl: string | null;
  progress: number;
  stage?: string;
  analysisReady?: boolean;
  onAnimationDone?: () => void;
}

export function AnalyzingPage({ fileName, videoUrl, progress, stage, analysisReady, onAnimationDone }: AnalyzingPageProps) {
  return (
    <div className="page page-center">
      <AnalyzingProgress
        fileName={fileName}
        videoUrl={videoUrl}
        progress={progress}
        stage={stage}
        analysisReady={analysisReady}
        onAnimationDone={onAnimationDone}
      />
    </div>
  );
}
