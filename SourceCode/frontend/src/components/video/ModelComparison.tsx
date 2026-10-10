import type { ModelSummary, WorkflowStep } from '../../types/analysis';

const TIER_COLORS: Record<string, string> = {
  tier1: '#3b82f6',
  tier2: '#8b5cf6',
  tier3: '#f59e0b',
};

const TIER_LABELS: Record<string, string> = {
  tier1: 'Classical ML',
  tier2: 'Deep Learning',
  tier3: 'Ensemble',
};

interface ModelComparisonProps {
  comparison: ModelSummary[];
  bestModel: string | null;
  allResults: Record<string, WorkflowStep[]>;
  onSelectModel: (modelName: string) => void;
  selectedModel: string | null;
}

export function ModelComparison({ comparison, bestModel, allResults, onSelectModel, selectedModel }: ModelComparisonProps) {
  if (comparison.length === 0) return null;

  return (
    <div className="model-comparison">
      <h3 className="model-comparison-title">Model Comparison — {comparison.length} Classifiers</h3>
      <p className="model-comparison-desc">
        All models classified the same video segments. Click a row to view its workflow steps.
      </p>
      <div className="model-comparison-table-wrap">
        <table className="model-comparison-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Model</th>
              <th>Tier</th>
              <th>Avg Confidence</th>
              <th>Latency</th>
            </tr>
          </thead>
          <tbody>
            {comparison.map((m, i) => {
              const isBest = m.model_name === bestModel;
              const isSelected = m.model_name === selectedModel;
              return (
                <tr
                  key={m.model_name}
                  className={`model-row ${isBest ? 'model-row-best' : ''} ${isSelected ? 'model-row-selected' : ''}`}
                  onClick={() => onSelectModel(m.model_name)}
                >
                  <td>{i + 1}</td>
                  <td className="model-name-cell">
                    {m.model_name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    {isBest && <span className="model-best-badge">Best</span>}
                  </td>
                  <td>
                    <span
                      className="model-tier-badge"
                      style={{ background: TIER_COLORS[m.tier] ?? '#6b7280' }}
                    >
                      {TIER_LABELS[m.tier] ?? m.tier}
                    </span>
                  </td>
                  <td>{(m.avg_confidence * 100).toFixed(1)}%</td>
                  <td>{m.latency_ms.toFixed(1)}ms</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
