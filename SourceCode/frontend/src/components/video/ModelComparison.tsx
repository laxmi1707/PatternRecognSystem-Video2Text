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

      <div style={{ marginTop: '2rem' }}>
        <h4 style={{ marginBottom: '0.75rem', fontSize: 14, fontWeight: 600, color: 'var(--color-accent-700)' }}>
          How the best model is selected
        </h4>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', fontSize: 13 }}>
          {[
            { tier: 'tier3', label: 'Ensemble', sublabel: 'Stacking · Voting · Late Fusion' },
            { tier: 'tier2', label: 'Deep Learning', sublabel: 'LSTM · Transformer · CNN1D · MLP' },
            { tier: 'tier1', label: 'Classical ML', sublabel: 'SVM · RF · KNN · XGBoost · …' },
          ].map((block, idx) => {
            const isWinner = comparison.some(
              m => m.model_name === bestModel && m.tier === block.tier
            );
            return (
              <div key={block.tier} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {idx > 0 && (
                  <span style={{ color: '#9ca3af', fontSize: 18, fontWeight: 300 }}>→</span>
                )}
                <div style={{
                  border: `2px solid ${isWinner ? TIER_COLORS[block.tier] : '#e5e7eb'}`,
                  borderRadius: 8,
                  padding: '8px 14px',
                  background: isWinner ? `${TIER_COLORS[block.tier]}18` : 'rgba(255,255,255,0.06)',
                  minWidth: 140,
                  position: 'relative',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                    <span style={{
                      display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
                      background: TIER_COLORS[block.tier],
                    }} />
                    <strong style={{ fontSize: 13 }}>{block.label}</strong>
                    {isWinner && (
                      <span style={{
                        fontSize: 10, fontWeight: 700, color: '#fff',
                        background: TIER_COLORS[block.tier],
                        borderRadius: 4, padding: '1px 5px', marginLeft: 2,
                      }}>SELECTED</span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: '#6b7280' }}>{block.sublabel}</div>
                  <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                    Priority {idx + 1} — {idx === 0 ? 'highest' : idx === 1 ? 'medium' : 'lowest'}
                  </div>
                </div>
              </div>
            );
          })}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: '#9ca3af', fontSize: 18, fontWeight: 300 }}>→</span>
            <div style={{ border: '1px dashed #d1d5db', borderRadius: 8, padding: '8px 14px', fontSize: 11, color: '#6b7280', minWidth: 100 }}>
              Tie within tier?<br />
              <strong style={{ color: '#374151' }}>Higher confidence wins</strong>
            </div>
          </div>
        </div>
        {bestModel && (
          <p style={{ marginTop: 10, fontSize: 12, color: '#6b7280' }}>
            ✓ SOP and Runbook use predictions from{' '}
            <strong style={{ color: '#111827' }}>
              {bestModel.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
            </strong>
          </p>
        )}
      </div>
    </div>
  );
}
