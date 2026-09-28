import { AnalyzingProgress } from '../components/video/AnalyzingProgress';

interface AnalyzingPageProps {
  fileName: string;
  videoUrl: string | null;
  progress: number;
  stage?: string;
}

export function AnalyzingPage({ fileName, videoUrl, progress, stage }: AnalyzingPageProps) {
  return (
    <div className="page page-center">
      <AnalyzingProgress fileName={fileName} videoUrl={videoUrl} progress={progress} stage={stage} />
    </div>
  );
}
