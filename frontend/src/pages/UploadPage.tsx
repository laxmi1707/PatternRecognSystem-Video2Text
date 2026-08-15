import { VideoDropzone } from '../components/video/VideoDropzone';

interface UploadPageProps {
  onFileSelected: (file: File) => void;
}

export function UploadPage({ onFileSelected }: UploadPageProps) {
  return (
    <div className="page page-narrow">
      <h6 style={{ color: 'var(--color-accent-700)' }}>New analysis</h6>
      <h1 style={{ marginBottom: 'var(--space-2)' }}>Upload a screen recording</h1>
      <p className="text-muted" style={{ maxWidth: 480 }}>
        Runbook watches the recording and writes out what happened as a plain-language workflow -
        the tools opened, the commands run, the actions taken.
      </p>
      <VideoDropzone onFileSelected={onFileSelected} />
    </div>
  );
}
