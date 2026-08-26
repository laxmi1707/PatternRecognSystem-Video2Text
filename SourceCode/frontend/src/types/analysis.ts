export interface WorkflowStep {
  n: number;
  time: string;
  title: string;
  description: string;
}

export interface AnalysisResult {
  id: string;
  name: string;
  date: string;
  duration: string;
  stepCount: number;
  status: 'Complete';
  videoUrl: string | null;
  summary: string;
  steps: WorkflowStep[];
}

export type Screen = 'upload' | 'analyzing' | 'results' | 'history';
