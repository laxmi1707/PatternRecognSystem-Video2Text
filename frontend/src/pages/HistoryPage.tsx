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
      <table className="table" style={{ marginTop: 'var(--space-4)' }}>
        <thead>
          <tr><th>File</th><th>Analyzed</th><th>Duration</th><th>Steps</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          {history.map(item => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.date}</td>
              <td>{item.duration}</td>
              <td>{item.stepCount}</td>
              <td><span className="tag tag-accent">{item.status}</span></td>
              <td style={{ textAlign: 'right' }}>
                <button className="btn btn-ghost" onClick={() => onView(item)}>View</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
