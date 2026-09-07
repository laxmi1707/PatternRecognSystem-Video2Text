export interface WorkflowStep {
  n: number;
  time: string;
  title: string;
  description: string;
}

/** Matches the real backend's /jobs/{id}/results shape (agreed with Eshwaran
 * 2026-09-05) -- the classifier's raw output, not a narrative. */
export interface ClassificationResult {
  id: string;
  name: string;
  date: string;
  duration: string;
  status: 'Complete';
  videoUrl: string | null;
  /** One of the 10 classes in the project ReadMe.md's "Target Classes" list. */
  label: string;
  confidence: number;
  probabilities: Record<string, number>;
}

/** The narrative SOP writeup, fetched separately from the classification.
 * Prototype data until the real LLM/RAG generation stage exists. */
export interface SopReport {
  summary: string;
  steps: WorkflowStep[];
}

export interface SearchResultItem {
  jobId: string;
  videoName: string;
  snippet: string;
  score: number;
}

export type Screen = 'upload' | 'analyzing' | 'results' | 'history' | 'dashboard' | 'search' | 'report';
