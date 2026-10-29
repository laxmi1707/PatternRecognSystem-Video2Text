import { VideoDropzone } from '../components/video/VideoDropzone';

interface UploadPageProps {
  onFileSelected: (file: File) => void;
  onHistory: () => void;
}

export function UploadPage({ onFileSelected, onHistory }: UploadPageProps) {
  return (
    <div className="upload-page">
      <div className="upload-dashboard">

        <div className="upload-main">
          <div className="upload-header-block">
            <span className="upload-badge">ISY5002 · Pattern Recognition Systems · NUS ISS</span>
            <p className="upload-engine-tag">
              <mark className="upload-highlight">Screen Activity Recognition</mark> &amp; <mark className="upload-highlight">Knowledge Extraction</mark>
            </p>
            <p className="upload-anomaly-tag">⚠ with <mark className="upload-anomaly-highlight">real-time risk &amp; anomaly detection</mark></p>
          </div>
          <VideoDropzone onFileSelected={onFileSelected} />
          <a className="upload-history-link" onClick={e => { e.preventDefault(); onHistory(); }} href="#">
            View History →
          </a>
        </div>

      </div>

    </div>
  );
}
