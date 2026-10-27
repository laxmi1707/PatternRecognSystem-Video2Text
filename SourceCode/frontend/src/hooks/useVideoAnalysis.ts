import { useCallback, useEffect, useRef, useState } from 'react';
import type { AnalysisResult, Screen } from '../types/analysis';
import { analyzeVideo, fetchHistory, AnalyzeHandle } from '../services/api/analysisService';

export function useVideoAnalysis(analysisSeconds = 3) {
  const [screen, setScreen] = useState<Screen>('upload');
  const [fileName, setFileName] = useState('');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [current, setCurrent] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>([]);
  const handleRef = useRef<AnalyzeHandle | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHistory().then((backendHistory: AnalysisResult[]) => {
      if (!cancelled && backendHistory.length > 0) {
        setHistory((prev: AnalysisResult[]) => {
          const backendIds = new Set(backendHistory.map((h: AnalysisResult) => h.id));
          const localOnly = prev.filter((p: AnalysisResult) => !backendIds.has(p.id));
          return [...localOnly, ...backendHistory];
        });
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const pendingResultRef = useRef<AnalysisResult | null>(null);
  const [analysisReady, setAnalysisReady] = useState(false);

  // Called by AnalyzingProgress after its task animation finishes
  const onAnimationDone = useCallback(() => {
    if (pendingResultRef.current) {
      setCurrent(pendingResultRef.current);
      setHistory((h: AnalysisResult[]) => [pendingResultRef.current!, ...h]);
      setScreen('results');
      pendingResultRef.current = null;
      setAnalysisReady(false);
    }
  }, []);

  const startAnalysis = useCallback((file: File) => {
    handleRef.current?.cancel();
    setFileName(file.name);
    setProgress(0);
    setAnalysisReady(false);
    setScreen('analyzing');
    const url = URL.createObjectURL(file);
    setVideoUrl(url);
    handleRef.current = analyzeVideo(file, analysisSeconds, (pct, stg) => { setProgress(pct); setStage(stg); }, (result) => {
      // Store result but let the animation finish before switching screen
      pendingResultRef.current = result;
      setAnalysisReady(true);
    });
  }, [analysisSeconds]);

  const goUpload = useCallback(() => {
    handleRef.current?.cancel();
    setScreen('upload');
    setProgress(0);
  }, []);

  const goHistory = useCallback(() => setScreen('history'), []);

  const viewHistory = useCallback((item: AnalysisResult) => {
    setCurrent(item);
    setScreen('results');
  }, []);

  return { screen, fileName, videoUrl, progress, stage, analysisReady, onAnimationDone, current, history, startAnalysis, goUpload, goHistory, viewHistory };
}
