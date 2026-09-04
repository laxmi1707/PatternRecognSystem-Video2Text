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
      <a href="#" onClick={e => { e.preventDefault(); onUpload(); }} aria-current={screen === 'upload' ? 'page' : undefined}>
        Upload
      </a>
      <a href="#" onClick={e => { e.preventDefault(); onHistory(); }} aria-current={screen === 'history' ? 'page' : undefined}>
        History
      </a>
      <a href="#" onClick={e => { e.preventDefault(); onDashboard(); }} aria-current={screen === 'dashboard' ? 'page' : undefined}>
        Dashboard
      </a>
      <a href="#" onClick={e => { e.preventDefault(); onSearch(); }} aria-current={screen === 'search' ? 'page' : undefined}>
        Search
      </a>
    </header>
  );
}
