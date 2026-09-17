export interface VideoUploadResponse {
  id: number;
  filename: string;
  original_filename: string;
  status: string;
  job_id: number;
}

export interface VideoResponse {
  id: number;
  filename: string;
  original_filename: string;
  file_size_bytes: number;
  duration_seconds: number | null;
  status: string;
}

export interface ClassificationResultDTO {
  label: string;
  confidence: number;
  probabilities: Record<string, number>;
  model_name: string;
  latency_ms: number;
}

export interface JobResponse {
  id: number;
  video_id: number;
  status: string;
  job_type: string;
  model_name: string | null;
  progress_pct: number;
  error_message: string | null;
}

export interface JobResultsResponse {
  job_id: number;
  status: string;
  results: ClassificationResultDTO[];
}
