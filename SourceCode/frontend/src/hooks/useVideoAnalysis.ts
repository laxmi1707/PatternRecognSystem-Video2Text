import { useCallback, useRef, useState } from 'react';
import type { AnalysisResult, Screen } from '../types/analysis';
import { analyzeVideo, getMockHistory, AnalyzeHandle } from '../services/api/analysisService';

export function useVideoAnalysis(analysisSeconds = 3) {
  const [screen, setScreen] = useState<Screen>('upload');
  const [fileName, setFileName] = useState('');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [current, setCurrent] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>(() => getMockHistory());
  const [error, setError] = useState<string | null>(null);
  const handleRef = useRef<AnalyzeHandle | null>(null);

  const startAnalysis = useCallback((file: File) => {
    handleRef.current?.cancel();
    setFileName(file.name);
    setProgress(0);
    setError(null);
    setScreen('analyzing');
    const url = URL.createObjectURL(file);
    setVideoUrl(url);
    handleRef.current = analyzeVideo(
      file,
      analysisSeconds,
      setProgress,
      (result) => {
        setCurrent(result);
        setHistory(h => [result, ...h]);
        setScreen('results');
      },
      (message) => {
        setError(message);
        setScreen('upload');
      }
    );
  }, [analysisSeconds]);

  const goUpload = useCallback(() => {
    handleRef.current?.cancel();
    setScreen('upload');
    setProgress(0);
    setError(null);
  }, []);

  const goHistory = useCallback(() => setScreen('history'), []);

  const viewHistory = useCallback((item: AnalysisResult) => {
    setCurrent(item);
    setScreen('results');
  }, []);

  return { screen, fileName, videoUrl, progress, current, history, error, startAnalysis, goUpload, goHistory, viewHistory };
}
