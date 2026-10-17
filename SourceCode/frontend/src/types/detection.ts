/** A step the SOP detector read from the video itself: a click or typed text. */
export interface DetectedStep {
  /** seconds from the start of the recording */
  t: number;
  action: 'Click' | 'Type';
  text: string;
}

export interface DetectionResult {
  app: string;
  app_confidence: number | null;
  duration: number | null;
  steps: DetectedStep[];
}

export interface DetectionJob {
  job_id: string;
  status: 'running' | 'completed' | 'failed';
  progress_pct: number;
  stage: string;
  result: DetectionResult | null;
  error: string | null;
}
