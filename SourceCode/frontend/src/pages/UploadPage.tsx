import { useState } from 'react';
import { CircuitBackground } from '../components/common/CircuitBackground';
import { VideoDropzone } from '../components/video/VideoDropzone';

const MODELS = {
  'Tier 1 — Classical ML': ['svm', 'naive_bayes', 'decision_tree', 'random_forest', 'knn', 'xgboost', 'lightgbm'],
  'Tier 2 — Deep Learning': ['mlp', 'cnn1d', 'lstm', 'transformer'],
  'Tier 3 — Ensemble': ['voting', 'stacking', 'late_fusion'],
} as const;

interface UploadPageProps {
  onFileSelected: (file: File, model?: string) => void;
}

export function UploadPage({ onFileSelected }: UploadPageProps) {
  const [model, setModel] = useState('svm');

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

        <div className="upload-model-picker">
          <label htmlFor="model-select">Classifier Model</label>
          <select
            id="model-select"
            value={model}
            onChange={e => setModel(e.target.value)}
          >
            {Object.entries(MODELS).map(([tier, names]) => (
              <optgroup key={tier} label={tier}>
                {names.map(name => (
                  <option key={name} value={name}>
                    {name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        <VideoDropzone onFileSelected={(file) => onFileSelected(file, model)} />
      </div>
    </div>
  );
}
