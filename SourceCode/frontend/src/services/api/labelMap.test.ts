import { describe, it, expect } from 'vitest';
import { mapResultsToSteps } from './labelMap';
import type { ClassificationResultDTO } from '../../types/api';

function makeResult(label: string, confidence = 0.9): ClassificationResultDTO {
  return { label, confidence, probabilities: {}, model_name: 'svm', latency_ms: 5 };
}

describe('mapResultsToSteps', () => {
  it('maps classification results to WorkflowSteps with correct time ranges', () => {
    const results = [makeResult('git_operations', 0.92), makeResult('coding_editing', 0.87)];
    const steps = mapResultsToSteps(results);

    expect(steps).toHaveLength(2);
    expect(steps[0].n).toBe(1);
    expect(steps[0].time).toBe('0:00-0:05');
    expect(steps[0].title).toBe('Performed Git operations');
    expect(steps[0].description).toContain('92%');
    expect(steps[0].description).toContain('svm');

    expect(steps[1].n).toBe(2);
    expect(steps[1].time).toBe('0:05-0:10');
    expect(steps[1].title).toBe('Edited code in the editor');
  });

  it('uses custom segment duration', () => {
    const steps = mapResultsToSteps([makeResult('debugging', 0.75)], 10);
    expect(steps[0].time).toBe('0:00-0:10');
  });

  it('falls back to "other" for unknown labels', () => {
    const steps = mapResultsToSteps([makeResult('unknown_label')]);
    expect(steps[0].title).toBe('Performed an unclassified action');
  });

  it('returns empty array for empty input', () => {
    expect(mapResultsToSteps([])).toEqual([]);
  });

  it('maps all known activity labels', () => {
    const labels = [
      'git_operations', 'docker_workflow', 'kubernetes_ops', 'terraform_iac',
      'aws_console', 'jenkins_ci_cd', 'coding_editing', 'debugging',
      'documentation', 'other',
    ];
    const results = labels.map((l) => makeResult(l));
    const steps = mapResultsToSteps(results);
    expect(steps).toHaveLength(10);
    steps.forEach((step, i) => {
      expect(step.n).toBe(i + 1);
      expect(step.title).toBeTruthy();
      expect(step.description).toBeTruthy();
    });
  });
});
