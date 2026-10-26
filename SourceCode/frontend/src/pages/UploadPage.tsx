import { VideoDropzone } from '../components/video/VideoDropzone';

interface UploadPageProps {
  onFileSelected: (file: File) => void;
}

const PIPELINE_STEPS = [
  { icon: '🎬', label: 'Frame Extraction', detail: 'Keyframe sampling via OpenCV' },
  { icon: '🔍', label: 'OCR + UI Detection', detail: 'EasyOCR + element recognition' },
  { icon: '🧠', label: 'Feature Engineering', detail: 'HOG + CNN visual embeddings' },
  { icon: '⚡', label: 'Activity Classification', detail: 'Ensemble ML classifiers' },
  { icon: '📄', label: 'Knowledge Export', detail: 'SOP + Runbook generation' },
];

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
            <h1 className="upload-title">TRACE</h1>
            <p className="upload-engine-tag">Task Recognition &amp; Activity Capture Engine</p>
            <p className="upload-desc">
              Drop a screen recording and the pipeline automatically recognises developer
              activities, extracts structured workflows, and generates SOP + Runbook documents.
            </p>
          </div>
          <VideoDropzone onFileSelected={onFileSelected} />
        </div>

        {/* Right column: info cards */}
        <div className="upload-sidebar">

          {/* Pipeline card */}
          <div className="info-card">
            <div className="info-card-header">
              <span className="info-card-icon">⚙️</span>
              <span className="info-card-title">Processing Pipeline</span>
            </div>
            <ol className="pipeline-list">
              {PIPELINE_STEPS.map((s, i) => (
                <li key={i} className="pipeline-step">
                  <span className="pipeline-step-num">{i + 1}</span>
                  <span className="pipeline-step-icon">{s.icon}</span>
                  <span className="pipeline-step-body">
                    <span className="pipeline-step-label">{s.label}</span>
                    <span className="pipeline-step-detail">{s.detail}</span>
                  </span>
                </li>
              ))}
            </ol>
          </div>

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
              <span className="format-limit">Up to 500 MB</span>
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
