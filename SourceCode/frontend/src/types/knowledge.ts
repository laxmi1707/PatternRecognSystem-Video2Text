export interface SOPStep {
  number: number;
  title: string;
  description: string;
  time_range: string;
}

export interface SOPResponse {
  title: string;
  purpose: string;
  prerequisites: string[];
  steps: SOPStep[];
  expected_outcome: string;
  troubleshooting: string[];
}

export interface ModelComparisonRow {
  model_name: string;
  tier: string;
  accuracy: number;
  precision_macro: number;
  recall_macro: number;
  f1_macro: number;
  auc_macro: number;
  latency_ms: number;
}

export interface EvalReportResponse {
  comparison_table: ModelComparisonRow[];
  generated_at: string;
}

export interface AvailableModelsResponse {
  models: string[];
  tiers: Record<string, string[]>;
}
