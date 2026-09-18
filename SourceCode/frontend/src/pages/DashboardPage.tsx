import { useEffect, useState } from 'react';
import type { AnalysisResult } from '../types/analysis';
import type { AvailableModelsResponse, EvalReportResponse } from '../types/knowledge';
import { fetchAvailableModels, runEvaluation } from '../services/api/evaluationService';

interface DashboardPageProps {
  history: AnalysisResult[];
}

function labelCounts(history: AnalysisResult[]): [string, number][] {
  const counts = new Map<string, number>();
  for (const item of history) {
    if (!item.label) continue;
    counts.set(item.label, (counts.get(item.label) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

export function DashboardPage({ history }: DashboardPageProps) {
  const [models, setModels] = useState<AvailableModelsResponse | null>(null);
  const [report, setReport] = useState<EvalReportResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAvailableModels()
      .then(m => { if (!cancelled) setModels(m); })
      .catch(() => { /* backend offline — the rest of the page still works */ });
    return () => { cancelled = true; };
  }, []);

  async function handleRunEvaluation() {
    setRunning(true);
    setError(null);
    try {
      setReport(await runEvaluation());
    } catch {
      setError('Could not run the evaluation. Is the backend running?');
    } finally {
      setRunning(false);
    }
  }

  const counts = labelCounts(history);
  const maxCount = Math.max(1, ...counts.map(([, n]) => n));
  const scored = history.filter(h => h.confidence !== undefined);
  const avgConfidence = scored.length
    ? ((scored.reduce((sum, h) => sum + (h.confidence ?? 0), 0) / scored.length) * 100).toFixed(0)
    : '--';

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
          <span className="stat-label">Activities seen</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{avgConfidence}{avgConfidence === '--' ? '' : '%'}</span>
          <span className="stat-label">Avg. confidence</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{models ? models.models.length : '--'}</span>
          <span className="stat-label">Models registered</span>
        </div>
      </div>

      <h4 style={{ marginTop: 'var(--space-8)' }}>Analyses by activity</h4>
      {counts.length === 0 ? (
        <p className="text-muted">No classified analyses yet. Upload a recording to populate this chart.</p>
      ) : (
        <div className="bar-chart">
          {counts.map(([label, count]) => (
            <div className="bar-row" key={label}>
              <span className="bar-label" title={label}>{label}</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(count / maxCount) * 100}%` }} />
              </div>
              <span className="bar-count">{count}</span>
            </div>
          ))}
        </div>
      )}

      <div className="results-head" style={{ marginTop: 'var(--space-8)' }}>
        <h4 style={{ margin: 0 }}>Model comparison</h4>
        <button className="btn btn-secondary" onClick={handleRunEvaluation} disabled={running}>
          {running ? 'Running evaluation…' : 'Run evaluation'}
        </button>
      </div>
      <p className="text-muted" style={{ marginTop: 'var(--space-2)' }}>
        Trains every registered classifier and scores them on the same test split.
      </p>

      {error && <p className="dropzone-error" role="alert">{error}</p>}

      {report && (
        <>
          <div className="table-wrap" style={{ marginTop: 'var(--space-4)' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Model</th><th>Tier</th><th>Accuracy</th><th>Precision</th>
                  <th>Recall</th><th>F1</th><th>AUC</th><th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {report.comparison_table.map(row => (
                  <tr key={row.model_name}>
                    <td>{row.model_name}</td>
                    <td><span className="tag tag-outline">{row.tier}</span></td>
                    <td>{row.accuracy.toFixed(3)}</td>
                    <td>{row.precision_macro.toFixed(3)}</td>
                    <td>{row.recall_macro.toFixed(3)}</td>
                    <td>{row.f1_macro.toFixed(3)}</td>
                    <td>{row.auc_macro.toFixed(3)}</td>
                    <td>{row.latency_ms.toFixed(1)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-muted" style={{ fontSize: 12, marginTop: 'var(--space-2)' }}>
            Generated {report.generated_at}
          </p>
        </>
      )}
    </div>
  );
}
