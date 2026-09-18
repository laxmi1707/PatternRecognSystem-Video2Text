import type { AnalysisResult } from '../../types/analysis';

interface ClassificationResultsProps {
  result: AnalysisResult;
  onViewReport: () => void;
}

/** Dominant activity for the recording, with the probability spread behind it.
 *  Renders nothing when the backend did not return classification output. */
export function ClassificationResults({ result, onViewReport }: ClassificationResultsProps) {
  if (!result.label) return null;

  const ranked = Object.entries(result.probabilities ?? {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);
  const maxProb = Math.max(...ranked.map(([, p]) => p), 0.01);

  return (
    <div className="classification">
      <div className="classification-headline">
        <span className="tag tag-accent classification-label">{result.label}</span>
        {result.confidence !== undefined && (
          <span className="classification-confidence">
            {(result.confidence * 100).toFixed(0)}% confidence
          </span>
        )}
      </div>

      {ranked.length > 0 && (
        <>
          <h4 style={{ marginTop: 'var(--space-4)' }}>Class probabilities</h4>
          <div className="bar-chart">
            {ranked.map(([label, prob]) => (
              <div className="bar-row" key={label}>
                <span className="bar-label" title={label}>{label}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(prob / maxProb) * 100}%` }} />
                </div>
                <span className="bar-count">{(prob * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </>
      )}

      <button
        className="btn btn-primary"
        style={{ marginTop: 'var(--space-4)' }}
        onClick={onViewReport}
      >
        View full report (SOP)
      </button>
    </div>
  );
}
