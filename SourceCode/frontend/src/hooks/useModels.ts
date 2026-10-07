import { useEffect, useState } from 'react';
import { apiGet } from '../services/api/client';

interface RecommendedModel {
  model_name: string;
  reason: string;
  f1_macro: number;
  accuracy: number;
  latency_ms: number;
}

interface ModelsResponse {
  models: string[];
  tiers: Record<string, string[]>;
  recommended: RecommendedModel | null;
}

const FALLBACK_TIERS: Record<string, string[]> = {
  'Tier 1 — Classical ML': ['svm', 'naive_bayes', 'decision_tree', 'random_forest', 'knn', 'xgboost', 'lightgbm'],
  'Tier 2 — Deep Learning': ['mlp', 'cnn1d', 'lstm', 'transformer'],
  'Tier 3 — Ensemble': ['voting', 'stacking', 'late_fusion'],
};

const TIER_LABELS: Record<string, string> = {
  tier1: 'Tier 1 — Classical ML',
  tier2: 'Tier 2 — Deep Learning',
  tier3: 'Tier 3 — Ensemble',
};

export function useModels() {
  const [tiers, setTiers] = useState<Record<string, string[]>>(FALLBACK_TIERS);
  const [recommended, setRecommended] = useState<RecommendedModel | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiGet<ModelsResponse>('/evaluation/models')
      .then((data) => {
        if (cancelled) return;
        const labeled: Record<string, string[]> = {};
        for (const [key, models] of Object.entries(data.tiers)) {
          labeled[TIER_LABELS[key] ?? key] = models;
        }
        setTiers(labeled);
        setRecommended(data.recommended);
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return { tiers, recommended, loading };
}
