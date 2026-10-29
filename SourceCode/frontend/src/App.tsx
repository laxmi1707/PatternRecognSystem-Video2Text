import { useState } from 'react';
import { NavBar } from './components/common/NavBar';
import { CircuitBackground } from './components/common/CircuitBackground';
import { UploadPage } from './pages/UploadPage';
import { AnalyzingPage } from './pages/AnalyzingPage';
import { ResultsPage } from './pages/ResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import { useVideoAnalysis } from './hooks/useVideoAnalysis';
import engineerLeft from './assets/engineer-left.jpg';
import engineerRight from './assets/engineer-right.jpg';

export default function App() {
  const {
    screen, fileName, videoUrl, progress, stage, analysisReady, onAnimationDone,
    current, history, startAnalysis, goUpload, goHistory, viewHistory,
  } = useVideoAnalysis(3);

  const [isV2, setIsV2] = useState(() => localStorage.getItem('ui') === 'v2');

  const toggleUI = () => {
    const next = !isV2;
    localStorage.setItem('ui', next ? 'v2' : 'v1');
    setIsV2(next);
  };

  return (
    <div className={`app-shell${isV2 ? ' app-v2' : ''}`}>
      <CircuitBackground />
      <NavBar screen={screen} onUpload={goUpload} onHistory={goHistory} />

      {screen === 'upload' && (
        <>
          {isV2 && (
            <>
              <div className="side-photo side-photo-left">
                <img src={engineerLeft} alt="Engineer at workstation" />
              </div>
              <div className="side-photo side-photo-right">
                <img src={engineerRight} alt="Engineer reviewing results" />
              </div>
            </>
          )}
          <UploadPage onFileSelected={(file) => startAnalysis(file)} onHistory={goHistory} />
        </>
      )}
      {screen === 'analyzing' && <AnalyzingPage fileName={fileName} videoUrl={videoUrl} progress={progress} stage={stage} analysisReady={analysisReady} onAnimationDone={onAnimationDone} />}
      {screen === 'results' && current && <ResultsPage result={current} onAnalyzeAnother={goUpload} />}
      {screen === 'history' && <HistoryPage history={history} onView={viewHistory} />}

      <div className="app-footer">
        Project Group-21 &middot; NUS ISS Master of Technology in AI Systems
      </div>

      <button className="ui-toggle-btn" onClick={toggleUI}>
        {isV2 ? '← Classic' : '✦ New Look'}
      </button>
    </div>
  );
}
