import type { Screen } from '../../types/analysis';

interface NavBarProps {
  screen: Screen;
  onUpload: () => void;
  onHistory: () => void;
}

export function NavBar({ screen, onUpload, onHistory }: NavBarProps) {
  return (
    <header className="nav">
      <span className="nav-brand">
        <span className="nav-brand-trace">TRACE</span>
        <span className="nav-subtitle">Task Recognition &amp; Activity Capture Engine</span>
      </span>
      <a href="#" onClick={e => { e.preventDefault(); onUpload(); }} aria-current={screen === 'upload' ? 'page' : undefined}>
        Upload
      </a>
      <a href="#" onClick={e => { e.preventDefault(); onHistory(); }} aria-current={screen === 'history' ? 'page' : undefined}>
        History
      </a>
    </header>
  );
}
