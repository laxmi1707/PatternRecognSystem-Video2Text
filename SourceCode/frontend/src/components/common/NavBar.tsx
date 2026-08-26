import type { Screen } from '../../types/analysis';

interface NavBarProps {
  screen: Screen;
  onUpload: () => void;
  onHistory: () => void;
}

export function NavBar({ screen, onUpload, onHistory }: NavBarProps) {
  return (
    <header className="nav">
      <span className="nav-brand">Runbook</span>
      <a href="#" onClick={e => { e.preventDefault(); onUpload(); }} aria-current={screen === 'upload' ? 'page' : undefined}>
        Upload
      </a>
      <a href="#" onClick={e => { e.preventDefault(); onHistory(); }} aria-current={screen === 'history' ? 'page' : undefined}>
        History
      </a>
    </header>
  );
}
