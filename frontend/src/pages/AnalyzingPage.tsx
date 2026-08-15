import { AnalyzingProgress } from '../components/video/AnalyzingProgress';

interface AnalyzingPageProps {
  fileName: string;
  videoUrl: string | null;
  progress: number;
}

export function AnalyzingPage({ fileName, videoUrl, progress }: AnalyzingPageProps) {
  return (
    <div className="page page-center">
      <AnalyzingProgress fileName={fileName} videoUrl={videoUrl} progress={progress} />
    </div>
  );
}
