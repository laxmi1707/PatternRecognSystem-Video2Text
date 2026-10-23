import { useState } from 'react';
import { BASE_URL } from '../../services/api/client';

const API_KEY = import.meta.env.VITE_API_KEY ?? '';

interface ReportViewProps {
  jobId: string;
  videoName: string;
}

export function ReportView({ jobId, videoName }: ReportViewProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloaded, setDownloaded] = useState(false);

  async function handleDownload() {
    setLoading(true);
    setError(null);
    try {
      const headers: Record<string, string> = API_KEY ? { 'X-API-Key': API_KEY } : {};
      const res = await fetch(`${BASE_URL}/knowledge/report/${jobId}`, { method: 'POST', headers });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Server error ${res.status}`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${jobId}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setDownloaded(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Download failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: 12,
        padding: '2rem',
        boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <span style={{ fontSize: 32 }}>📝</span>
          <div>
            <h3 style={{ margin: 0, fontSize: 18 }}>Analysis Report</h3>
            <p style={{ margin: 0, fontSize: 13, color: '#6b7280' }}>{videoName}</p>
          </div>
        </div>

        <p style={{ fontSize: 14, color: '#374151', marginBottom: 20, lineHeight: 1.6 }}>
          The Word document (.docx) includes:
        </p>
        <ul style={{ fontSize: 14, color: '#374151', lineHeight: 2, marginBottom: 24, paddingLeft: 20 }}>
          <li>Keyframes extracted every 5 seconds with timestamps</li>
          <li>Classification results table (segment, label, confidence, model)</li>
          <li>Standard Operating Procedure (SOP) steps</li>
        </ul>

        <button
          onClick={handleDownload}
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px 24px',
            borderRadius: 8,
            border: 'none',
            cursor: loading ? 'wait' : 'pointer',
            fontWeight: 700,
            fontSize: 15,
            background: downloaded
              ? 'linear-gradient(135deg, #10b981, #059669)'
              : loading
              ? 'rgba(239,124,0,0.5)'
              : 'linear-gradient(135deg, #EF7C00, #d46a00)',
            color: '#fff',
            boxShadow: '0 2px 8px rgba(239,124,0,0.30)',
            transition: 'background 0.2s',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
          }}
        >
          <span style={{ fontSize: 18 }}>{downloaded ? '✓' : '⬇'}</span>
          {loading
            ? 'Generating report… (extracting frames)'
            : downloaded
            ? 'Downloaded — click to download again'
            : 'Download Report (.docx)'}
        </button>

        {error && (
          <p style={{ color: '#ef4444', fontSize: 13, marginTop: 12, textAlign: 'center' }}>
            {error}
          </p>
        )}

        <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 16, textAlign: 'center' }}>
          Generation may take 10–30 seconds depending on video length.
        </p>
      </div>
    </div>
  );
}
