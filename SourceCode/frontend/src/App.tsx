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
    screen, fileName, videoUrl, progress, phase, current, history, error,
    reportTarget, report, reportLoading, reportError,
    startAnalysis, goUpload, goHistory, goDashboard, goSearch, viewHistory, viewReport,
  } = useVideoAnalysis(3);

  return (
    <div className="app-shell">
      <NavBar screen={screen} onUpload={goUpload} onHistory={goHistory} onDashboard={goDashboard} onSearch={goSearch} />
      {screen === 'upload' && <UploadPage onFileSelected={startAnalysis} error={error} />}
      {screen === 'analyzing' && (
        <AnalyzingPage fileName={fileName} videoUrl={videoUrl} progress={progress} phase={phase} onCancel={goUpload} />
      )}
      {screen === 'results' && current && (
        <ResultsPage result={current} onAnalyzeAnother={goUpload} onViewReport={() => viewReport(current)} />
      )}
      {screen === 'history' && <HistoryPage history={history} onView={viewHistory} onViewReport={viewReport} />}
      {screen === 'dashboard' && <DashboardPage history={history} />}
      {screen === 'search' && <SearchPage />}
      {screen === 'report' && reportTarget && (
        <ReportPage
          target={reportTarget}
          report={report}
          loading={reportLoading}
          error={reportError}
          onBack={() => viewHistory(reportTarget)}
        />
      )}
    </div>
  );
}
