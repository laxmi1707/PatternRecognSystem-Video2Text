import { useState } from 'react';
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
    <div className="page page-narrow">
      <h6 style={{ color: 'var(--color-accent-700)' }}>New analysis</h6>
      <h1 style={{ marginBottom: 'var(--space-2)' }}>Upload a screen recording</h1>
      <p className="text-muted" style={{ maxWidth: 480 }}>
        Video2Knowledge watches the recording and extracts structured workflow knowledge —
        the activities performed, the tools used, the commands run, and the outcomes observed.
      </p>

      <div style={{ marginBottom: 'var(--space-4, 1.5rem)', maxWidth: 320 }}>
        <label htmlFor="model-select" style={{ display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 6 }}>
          Classifier Model
        </label>
        <select
          id="model-select"
          value={model}
          onChange={e => setModel(e.target.value)}
          style={{
            width: '100%', padding: '8px 12px', borderRadius: 6,
            border: '1px solid var(--color-border, #d1d5db)',
            fontSize: 14, background: 'white',
          }}
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
  );
}
