import type { AnalysisResult } from '../types/analysis';

interface DashboardPageProps {
  history: AnalysisResult[];
}

function categoryCounts(history: AnalysisResult[]): [string, number][] {
  const counts = new Map<string, number>();
  for (const item of history) {
    counts.set(item.category, (counts.get(item.category) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

export function DashboardPage({ history }: DashboardPageProps) {
  const counts = categoryCounts(history);
  const maxCount = Math.max(1, ...counts.map(([, n]) => n));
  const totalSteps = history.reduce((sum, item) => sum + item.stepCount, 0);
  const avgSteps = history.length ? (totalSteps / history.length).toFixed(1) : '0';

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
          <span className="stat-label">Categories seen</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{avgSteps}</span>
          <span className="stat-label">Avg. steps per video</span>
        </div>
      </div>

      <h4 style={{ marginTop: 'var(--space-8)' }}>Analyses by category</h4>
      {counts.length === 0 ? (
        <p className="text-muted">No completed analyses yet.</p>
      ) : (
        <div className="bar-chart">
          {counts.map(([category, count]) => (
            <div className="bar-row" key={category}>
              <span className="bar-label">{category}</span>
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
