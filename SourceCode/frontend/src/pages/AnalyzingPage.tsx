import { AnalyzingProgress } from '../components/video/AnalyzingProgress';

interface AnalyzingPageProps {
  fileName: string;
  videoUrl: string | null;
  progress: number;
  phase?: 'uploading' | 'processing';
  onCancel?: () => void;
}

export function AnalyzingPage({ fileName, videoUrl, progress, phase, onCancel }: AnalyzingPageProps) {
  return (
    <div className="page page-center">
      <AnalyzingProgress fileName={fileName} videoUrl={videoUrl} progress={progress} phase={phase} onCancel={onCancel} />
    </div>
  );
}
