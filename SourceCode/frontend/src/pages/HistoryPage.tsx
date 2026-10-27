import type { AnalysisResult } from '../types/analysis';

interface HistoryPageProps {
  history: AnalysisResult[];
  onView: (item: AnalysisResult) => void;
}

export function HistoryPage({ history, onView }: HistoryPageProps) {
  return (
    <div className="page page-medium">
      <h6 style={{ color: 'var(--color-accent-700)' }}>Past analyses</h6>
      <h1>History</h1>
      {history.length === 0 ? (
        <p style={{ color: '#6b7280', marginTop: '2rem' }}>
          No analyses yet. Upload a screen recording to get started.
        </p>
      ) : (
        <table className="table" style={{ marginTop: 'var(--space-4)' }}>
          <thead>
            <tr>
              {['File', 'Analyzed', 'Duration', 'Steps', 'Status', ''].map(h => (
                <th key={h} style={{ color: '#374151', fontWeight: 700 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {history.map(item => (
              <tr key={item.id}>
                <td style={{ fontWeight: 500 }}>{item.name}</td>
                <td style={{ color: '#374151' }}>{item.date}</td>
                <td style={{ color: '#374151' }}>{item.duration}</td>
                <td style={{ color: '#374151' }}>{item.stepCount}</td>
                <td><span className="tag tag-accent">{item.status}</span></td>
                <td style={{ textAlign: 'right' }}>
                  <button className="btn btn-ghost" onClick={() => onView(item)}>View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
