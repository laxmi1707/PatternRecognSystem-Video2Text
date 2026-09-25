export interface WorkflowStep {
  n: number;
  time: string;
  title: string;
  description: string;
}

export interface ModelSummary {
  model_name: string;
  tier: string;
  avg_confidence: number;
  latency_ms: number;
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
  modelComparison: ModelSummary[];
  bestModel: string | null;
  allResults: Record<string, WorkflowStep[]>;
}

export type Screen = 'upload' | 'analyzing' | 'results' | 'history';
