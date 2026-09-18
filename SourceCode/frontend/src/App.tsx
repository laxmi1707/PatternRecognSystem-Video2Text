import { NavBar } from './components/common/NavBar';
import { UploadPage } from './pages/UploadPage';
import { AnalyzingPage } from './pages/AnalyzingPage';
import { ResultsPage } from './pages/ResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import { DashboardPage } from './pages/DashboardPage';
import { SearchPage } from './pages/SearchPage';
import { ReportPage } from './pages/ReportPage';
import { useVideoAnalysis } from './hooks/useVideoAnalysis';

export default function App() {
  const {
    screen, fileName, videoUrl, progress, phase, current, history, reportTarget,
    startAnalysis, goUpload, goHistory, goDashboard, goSearch,
    viewHistory, viewReport, backToResults,
  } = useVideoAnalysis(3);

  return (
    <div className="app-shell">
      <NavBar
        screen={screen}
        onUpload={goUpload}
        onHistory={goHistory}
        onDashboard={goDashboard}
        onSearch={goSearch}
      />
      {screen === 'upload' && <UploadPage onFileSelected={(file, model) => startAnalysis(file, model)} />}
      {screen === 'analyzing' && (
        <AnalyzingPage
          fileName={fileName}
          videoUrl={videoUrl}
          progress={progress}
          phase={phase}
          onCancel={goUpload}
        />
      )}
      {screen === 'results' && current && (
        <ResultsPage
          result={current}
          onAnalyzeAnother={goUpload}
          onViewReport={() => viewReport(current)}
        />
      )}
      {screen === 'history' && <HistoryPage history={history} onView={viewHistory} />}
      {screen === 'dashboard' && <DashboardPage history={history} />}
      {screen === 'search' && <SearchPage history={history} onView={viewHistory} />}
      {screen === 'report' && reportTarget && (
        <ReportPage target={reportTarget} onBack={backToResults} />
      )}
    </div>
  );
}
