import type { ClassificationResult } from '../types/analysis';

interface HistoryPageProps {
  history: ClassificationResult[];
  onView: (item: ClassificationResult) => void;
  onViewReport: (item: ClassificationResult) => void;
}

export function HistoryPage({ history, onView, onViewReport }: HistoryPageProps) {
  return (
    <div className="page page-medium">
      <h6 style={{ color: 'var(--color-accent-700)' }}>Past analyses</h6>
      <h1>History</h1>
      <div className="table-wrap" style={{ marginTop: 'var(--space-4)' }}>
        <table className="table">
          <thead>
            <tr><th>File</th><th>Analyzed</th><th>Duration</th><th>Label</th><th>Confidence</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {history.map(item => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.date}</td>
                <td>{item.duration}</td>
                <td><span className="tag tag-outline">{item.label}</span></td>
                <td>{(item.confidence * 100).toFixed(0)}%</td>
                <td><span className="tag tag-accent">{item.status}</span></td>
                <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <button className="btn btn-ghost" onClick={() => onView(item)}>View</button>
                  <button className="btn btn-ghost" onClick={() => onViewReport(item)}>Report</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
