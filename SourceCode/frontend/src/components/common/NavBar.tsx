import type { Screen } from '../../types/analysis';

interface NavBarProps {
  screen: Screen;
  onUpload: () => void;
  onHistory: () => void;
  onDashboard: () => void;
  onSearch: () => void;
}

export function NavBar({ screen, onUpload, onHistory, onDashboard, onSearch }: NavBarProps) {
  return (
    <header className="nav">
      <span className="nav-brand">Runbook</span>
      <nav className="nav-links">
        <button type="button" className="nav-link" onClick={onUpload} aria-current={screen === 'upload' ? 'page' : undefined}>
          Upload
        </button>
        <button type="button" className="nav-link" onClick={onHistory} aria-current={screen === 'history' ? 'page' : undefined}>
          History
        </button>
        <button type="button" className="nav-link" onClick={onDashboard} aria-current={screen === 'dashboard' ? 'page' : undefined}>
          Dashboard
        </button>
        <button type="button" className="nav-link" onClick={onSearch} aria-current={screen === 'search' ? 'page' : undefined}>
          Search
        </button>
      </nav>
    </header>
  );
}
