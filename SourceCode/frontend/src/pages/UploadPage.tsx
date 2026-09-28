import { CircuitBackground } from '../components/common/CircuitBackground';
import { VideoDropzone } from '../components/video/VideoDropzone';

interface UploadPageProps {
  onFileSelected: (file: File) => void;
  fastMode: boolean;
  onToggleFastMode: () => void;
}

export function UploadPage({ onFileSelected, fastMode, onToggleFastMode }: UploadPageProps) {
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

        <div className="mode-toggle" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, margin: '16px 0' }}>
          <span style={{ fontSize: 14, color: fastMode ? '#999' : '#007acc', fontWeight: fastMode ? 400 : 600 }}>
            Full Mode (14 models, ~5 min)
          </span>
          <label className="toggle-switch" style={{ position: 'relative', display: 'inline-block', width: 48, height: 26 }}>
            <input
              type="checkbox"
              checked={fastMode}
              onChange={onToggleFastMode}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span style={{
              position: 'absolute', cursor: 'pointer', inset: 0,
              backgroundColor: fastMode ? '#28a745' : '#ccc',
              borderRadius: 26, transition: 'background-color 0.3s',
            }}>
              <span style={{
                position: 'absolute', height: 20, width: 20,
                left: fastMode ? 24 : 4, bottom: 3,
                backgroundColor: 'white', borderRadius: '50%',
                transition: 'left 0.3s',
              }} />
            </span>
          </label>
          <span style={{ fontSize: 14, color: fastMode ? '#28a745' : '#999', fontWeight: fastMode ? 600 : 400 }}>
            Fast Mode (9 models, ~10 sec)
          </span>
        </div>

        <VideoDropzone onFileSelected={onFileSelected} />
      </div>
    </div>
  );
}
