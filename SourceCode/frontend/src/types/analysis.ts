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
  /** One of the 10 classes in the project ReadMe.md's "Target Classes" list. */
  category: string;
}

export interface SearchResultItem {
  jobId: string;
  videoName: string;
  snippet: string;
  score: number;
}

export type Screen = 'upload' | 'analyzing' | 'results' | 'history' | 'dashboard' | 'search';
