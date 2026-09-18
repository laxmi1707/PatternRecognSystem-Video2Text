import type { AvailableModelsResponse, EvalReportResponse, SOPResponse } from '../../types/knowledge';
import { apiGet, apiPost } from './client';

/** GET /api/v1/evaluation/models — which classifiers the backend has registered. */
export async function fetchAvailableModels(): Promise<AvailableModelsResponse> {
  return apiGet<AvailableModelsResponse>('/evaluation/models');
}

/** POST /api/v1/evaluation/run — trains and scores every registered model. Slow. */
export async function runEvaluation(): Promise<EvalReportResponse> {
  return apiPost<EvalReportResponse>('/evaluation/run');
}

/** POST /api/v1/knowledge/sop/{jobId} — the generated SOP for one analysis job. */
export async function fetchSopReport(jobId: number): Promise<SOPResponse> {
  return apiPost<SOPResponse>(`/knowledge/sop/${jobId}`);
}
