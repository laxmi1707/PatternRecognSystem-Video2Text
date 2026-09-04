import { NavBar } from './components/common/NavBar';
import { UploadPage } from './pages/UploadPage';
import { AnalyzingPage } from './pages/AnalyzingPage';
import { ResultsPage } from './pages/ResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import { DashboardPage } from './pages/DashboardPage';
import { SearchPage } from './pages/SearchPage';
import { useVideoAnalysis } from './hooks/useVideoAnalysis';

export default function App() {
  const {
    screen, fileName, videoUrl, progress, phase, current, history, error,
    startAnalysis, goUpload, goHistory, goDashboard, goSearch, viewHistory,
  } = useVideoAnalysis(3);

  return (
    <div className="app-shell">
      <NavBar screen={screen} onUpload={goUpload} onHistory={goHistory} onDashboard={goDashboard} onSearch={goSearch} />
      {screen === 'upload' && <UploadPage onFileSelected={startAnalysis} error={error} />}
      {screen === 'analyzing' && (
        <AnalyzingPage fileName={fileName} videoUrl={videoUrl} progress={progress} phase={phase} onCancel={goUpload} />
      )}
      {screen === 'results' && current && <ResultsPage result={current} onAnalyzeAnother={goUpload} />}
      {screen === 'history' && <HistoryPage history={history} onView={viewHistory} />}
      {screen === 'dashboard' && <DashboardPage history={history} />}
      {screen === 'search' && <SearchPage />}
    </div>
  );
}
