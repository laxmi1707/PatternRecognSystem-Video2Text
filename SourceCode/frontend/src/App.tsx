import { NavBar } from './components/common/NavBar';
import { UploadPage } from './pages/UploadPage';
import { AnalyzingPage } from './pages/AnalyzingPage';
import { ResultsPage } from './pages/ResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import { useVideoAnalysis } from './hooks/useVideoAnalysis';

export default function App() {
  const {
    screen, fileName, videoUrl, progress, stage, fastMode, toggleFastMode, current, history,
    startAnalysis, goUpload, goHistory, viewHistory,
  } = useVideoAnalysis(3);

  return (
    <div className="app-shell">
      <NavBar screen={screen} onUpload={goUpload} onHistory={goHistory} />
      {screen === 'upload' && <UploadPage onFileSelected={(file) => startAnalysis(file)} fastMode={fastMode} onToggleFastMode={toggleFastMode} />}
      {screen === 'analyzing' && <AnalyzingPage fileName={fileName} videoUrl={videoUrl} progress={progress} stage={stage} />}
      {screen === 'results' && current && <ResultsPage result={current} onAnalyzeAnother={goUpload} />}
      {screen === 'history' && <HistoryPage history={history} onView={viewHistory} />}
    </div>
  );
}
