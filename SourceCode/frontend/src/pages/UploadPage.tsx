import { CircuitBackground } from '../components/common/CircuitBackground';
import { VideoDropzone } from '../components/video/VideoDropzone';

interface UploadPageProps {
  onFileSelected: (file: File) => void;
}

export function UploadPage({ onFileSelected }: UploadPageProps) {
  return (
    <div className="upload-page">
      <CircuitBackground />
      <div className="upload-content">
        <span className="upload-badge">New analysis</span>
        <h1 className="upload-title">Upload a screen recording</h1>
        <p className="upload-desc">
          Video2Knowledge watches the recording and extracts structured workflow knowledge —
          the activities performed, the tools used, the commands run, and the outcomes observed.
        </p>

        <VideoDropzone onFileSelected={onFileSelected} />
      </div>
    </div>
  );
}
