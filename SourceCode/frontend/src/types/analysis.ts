export interface WorkflowStep {
  n: number;
  time: string;
  title: string;
  description: string;
}

export interface AnalysisResult {
  id: string;
  /** Backend job behind this analysis. Needed to generate an SOP report. */
  jobId?: number;
  name: string;
  date: string;
  duration: string;
  stepCount: number;
  status: 'Complete';
  videoUrl: string | null;
  summary: string;
  steps: WorkflowStep[];
  /** Dominant activity across the classified segments, when the backend returned one. */
  label?: string;
  confidence?: number;
  probabilities?: Record<string, number>;
}

export type Screen =
  | 'upload'
  | 'analyzing'
  | 'results'
  | 'history'
  | 'dashboard'
  | 'search'
  | 'report';
