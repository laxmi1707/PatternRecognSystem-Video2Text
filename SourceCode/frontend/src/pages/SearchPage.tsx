import { useState } from 'react';
import type { AnalysisResult } from '../types/analysis';

interface SearchPageProps {
  history: AnalysisResult[];
  onView: (item: AnalysisResult) => void;
}

interface Hit {
  item: AnalysisResult;
  snippet: string;
}

/** Searches the analyses already loaded in the session: file name, predicted
 *  label, summary and step text. The backend has no search endpoint yet, so
 *  this filters locally rather than pretending to query one. */
function search(history: AnalysisResult[], query: string): Hit[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const hits: Hit[] = [];
  for (const item of history) {
    if (item.name.toLowerCase().includes(q)) {
      const context = item.summary || (item.label ? `Classified as ${item.label}` : 'No summary yet');
      hits.push({ item, snippet: context });
      continue;
    }
    if (item.label?.toLowerCase().includes(q)) {
      hits.push({ item, snippet: `Classified as ${item.label}` });
      continue;
    }
    if (item.summary.toLowerCase().includes(q)) {
      hits.push({ item, snippet: item.summary });
      continue;
    }
    const step = item.steps.find(
      s => s.title.toLowerCase().includes(q) || s.description.toLowerCase().includes(q),
    );
    if (step) {
      hits.push({ item, snippet: `${step.time} — ${step.description}` });
    }
  }
  return hits;
}

export function SearchPage({ history, onView }: SearchPageProps) {
  const [query, setQuery] = useState('');
  const [submitted, setSubmitted] = useState('');

  const hits = search(history, submitted);

  return (
    <div className="page page-medium">
      <h6 style={{ color: 'var(--color-accent-700)' }}>Knowledge repository</h6>
      <h1>Search</h1>
      <p className="text-muted" style={{ maxWidth: 520 }}>
        Search across the analyses in this session by file name, recognised activity, or the
        text of a workflow step.
      </p>

      <form
        onSubmit={e => { e.preventDefault(); setSubmitted(query); }}
        style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-4)', maxWidth: 520 }}
      >
        <label htmlFor="search-query" className="sr-only">Search query</label>
        <input
          id="search-query"
          className="input"
          type="search"
          value={query}
          placeholder="e.g. docker, terminal, deploy"
          onChange={e => setQuery(e.target.value)}
          style={{ flex: 1 }}
        />
        <button className="btn btn-primary" type="submit">Search</button>
      </form>

      {submitted && (
        <p className="text-muted" style={{ marginTop: 'var(--space-4)' }}>
          {hits.length} {hits.length === 1 ? 'match' : 'matches'} for &ldquo;{submitted}&rdquo;
        </p>
      )}

      <ul className="search-results" style={{ marginTop: 'var(--space-3)' }}>
        {hits.map(({ item, snippet }) => (
          <li className="search-result" key={item.id}>
            <div className="search-result-head">
              <strong>{item.name}</strong>
              <button className="btn btn-ghost" onClick={() => onView(item)}>Open</button>
            </div>
            <p className="text-muted" style={{ margin: '4px 0 0' }}>{snippet}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
