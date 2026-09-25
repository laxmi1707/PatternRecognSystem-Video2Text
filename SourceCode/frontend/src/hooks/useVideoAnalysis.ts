import { useCallback, useEffect, useRef, useState } from 'react';
import type { AnalysisResult, Screen } from '../types/analysis';
import { analyzeVideo, getMockHistory, fetchHistory, AnalyzeHandle } from '../services/api/analysisService';

export function useVideoAnalysis(analysisSeconds = 3) {
  const [screen, setScreen] = useState<Screen>('upload');
  const [fileName, setFileName] = useState('');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [current, setCurrent] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>(() => getMockHistory());
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

  const startAnalysis = useCallback((file: File) => {
    handleRef.current?.cancel();
    setFileName(file.name);
    setProgress(0);
    setScreen('analyzing');
    const url = URL.createObjectURL(file);
    setVideoUrl(url);
    handleRef.current = analyzeVideo(file, analysisSeconds, setProgress, (result) => {
      setCurrent(result);
      setHistory((h: AnalysisResult[]) => [result, ...h]);
      setScreen('results');
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

  return { screen, fileName, videoUrl, progress, current, history, startAnalysis, goUpload, goHistory, viewHistory };
}
