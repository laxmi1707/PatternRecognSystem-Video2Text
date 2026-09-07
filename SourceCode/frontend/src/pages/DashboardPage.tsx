import type { ClassificationResult } from '../types/analysis';

interface DashboardPageProps {
  history: ClassificationResult[];
}

function labelCounts(history: ClassificationResult[]): [string, number][] {
  const counts = new Map<string, number>();
  for (const item of history) {
    counts.set(item.label, (counts.get(item.label) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

export function DashboardPage({ history }: DashboardPageProps) {
  const counts = labelCounts(history);
  const maxCount = Math.max(1, ...counts.map(([, n]) => n));
  const totalConfidence = history.reduce((sum, item) => sum + item.confidence, 0);
  const avgConfidence = history.length ? ((totalConfidence / history.length) * 100).toFixed(0) : '0';

  return (
    <div className="page page-wide">
      <h6 style={{ color: 'var(--color-accent-700)' }}>Overview</h6>
      <h1>Dashboard</h1>

      <div className="stat-row">
        <div className="stat-card">
          <span className="stat-value">{history.length}</span>
          <span className="stat-label">Analyses</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{counts.length}</span>
          <span className="stat-label">Labels seen</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{avgConfidence}%</span>
          <span className="stat-label">Avg. confidence</span>
        </div>
      </div>

      <h4 style={{ marginTop: 'var(--space-8)' }}>Analyses by label</h4>
      {counts.length === 0 ? (
        <p className="text-muted">No completed analyses yet.</p>
      ) : (
        <div className="bar-chart">
          {counts.map(([label, count]) => (
            <div className="bar-row" key={label}>
              <span className="bar-label">{label}</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(count / maxCount) * 100}%` }} />
              </div>
              <span className="bar-count">{count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
