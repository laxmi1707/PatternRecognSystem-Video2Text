import { VideoDropzone } from '../components/video/VideoDropzone';

interface UploadPageProps {
  onFileSelected: (file: File) => void;
}

const SUPPORTED_ACTIVITIES = [
  'Git operations', 'Docker workflows', 'Kubernetes ops',
  'AWS Console', 'CI/CD pipelines', 'Coding & debugging',
  'Terminal commands', 'System configuration', 'Web browsing',
];

export function UploadPage({ onFileSelected }: UploadPageProps) {
  return (
    <div className="upload-page">
      <div className="upload-dashboard">

        {/* Left column: headline + dropzone */}
        <div className="upload-main">
          <div className="upload-header-block">
            <div className="nus-iss-brand">
              <span className="nus-iss-logo-text">NUS<span className="nus-iss-iss"> ISS</span></span>
              <span className="nus-iss-sep">|</span>
              <span className="nus-iss-course">Master of Technology in AI Systems</span>
            </div>
            <span className="upload-badge">Pattern Recognition System</span>
            <p className="upload-engine-tag">
              A Multimodal Pattern Recognition Framework<br />
              for <mark className="upload-highlight">Screen Activity Understanding</mark> and <mark className="upload-highlight">Knowledge Extraction</mark>
            </p>
            <p className="upload-anomaly-tag">⚠ with real-time risk &amp; anomaly detection</p>
            <p className="upload-desc">
              Drop a screen recording and the pipeline automatically recognises developer
              activities, extracts structured workflows, and generates SOP + Runbook documents.
            </p>
          </div>
          <VideoDropzone onFileSelected={onFileSelected} />
        </div>

        {/* Right column: info cards */}
        <div className="upload-sidebar">

          {/* Recognised activities card */}
          <div className="info-card">
            <div className="info-card-header">
              <span className="info-card-icon">🏷️</span>
              <span className="info-card-title">Recognised Activities</span>
            </div>
            <div className="activity-tags">
              {SUPPORTED_ACTIVITIES.map(a => (
                <span key={a} className="activity-tag">{a}</span>
              ))}
            </div>
          </div>

          {/* Format card */}
          <div className="info-card info-card-compact">
            <div className="info-card-header">
              <span className="info-card-icon">📁</span>
              <span className="info-card-title">Supported Formats</span>
            </div>
            <div className="format-row">
              {['MP4', 'MOV', 'WebM'].map(f => (
                <span key={f} className="format-badge">{f}</span>
              ))}
              <span className="format-limit">Up to 100 MB</span>
            </div>
          </div>

        </div>
      </div>

      <div className="upload-footer">
        Project Group-21 &middot; NUS ISS Master of Technology in AI Systems
      </div>
    </div>
  );
}
