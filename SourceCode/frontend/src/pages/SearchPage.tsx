import { useState, type FormEvent } from 'react';
import type { SearchResultItem } from '../types/analysis';
import { searchVideos } from '../services/api/analysisService';

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [searchedFor, setSearchedFor] = useState<string | null>(null);

  const runSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setStatus('loading');
    setError(null);
    try {
      const items = await searchVideos(query.trim());
      setResults(items);
      setSearchedFor(query.trim());
      setStatus('idle');
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Search failed');
    }
  };

  return (
    <div className="page page-medium">
      <h6 style={{ color: 'var(--color-accent-700)' }}>Knowledge base</h6>
      <h1>Search</h1>
      <p className="text-muted" style={{ maxWidth: 480 }}>
        Search across every analyzed recording's workflow for a matching step.
      </p>

      <form onSubmit={runSearch} style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-4)' }}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder='e.g. "create a new directory"'
          aria-label="Search query"
          className="input"
        />
        <button type="submit" className="btn btn-primary" disabled={status === 'loading'}>
          {status === 'loading' ? 'Searching…' : 'Search'}
        </button>
      </form>

      {status === 'error' && <p className="dropzone-error" role="alert" style={{ marginTop: 'var(--space-4)' }}>{error}</p>}

      {searchedFor && status !== 'error' && (
        <div style={{ marginTop: 'var(--space-6)' }}>
          {results.length === 0 ? (
            <p className="text-muted">No matches for "{searchedFor}".</p>
          ) : (
            <ul className="search-results">
              {results.map((r, i) => (
                <li key={`${r.jobId}-${i}`} className="search-result">
                  <div className="search-result-head">
                    <span className="tag tag-accent">{r.videoName}</span>
                    <span className="text-muted" style={{ fontSize: 12 }}>match {(r.score * 100).toFixed(0)}%</span>
                  </div>
                  <p style={{ margin: 'var(--space-2) 0 0' }}>{r.snippet}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
