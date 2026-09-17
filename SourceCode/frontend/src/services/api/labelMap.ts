import type { WorkflowStep } from '../../types/analysis';
import type { ClassificationResultDTO } from '../../types/api';
import { formatSeconds } from '../../utils/formatTime';

const LABEL_META: Record<string, { title: string; descriptionTemplate: string }> = {
  git_operations: {
    title: 'Performed Git operations',
    descriptionTemplate:
      'Git commands were executed (clone, pull, commit, push, etc.). Classified as git_operations with {confidence}% confidence by {model}.',
  },
  docker_workflow: {
    title: 'Worked with Docker',
    descriptionTemplate:
      'Docker containers or images were managed (build, run, compose, etc.). Classified as docker_workflow with {confidence}% confidence by {model}.',
  },
  kubernetes_ops: {
    title: 'Managed Kubernetes resources',
    descriptionTemplate:
      'Kubernetes cluster operations were performed (kubectl, helm, etc.). Classified as kubernetes_ops with {confidence}% confidence by {model}.',
  },
  terraform_iac: {
    title: 'Ran Terraform infrastructure',
    descriptionTemplate:
      'Infrastructure-as-code changes were applied using Terraform. Classified as terraform_iac with {confidence}% confidence by {model}.',
  },
  aws_console: {
    title: 'Used the AWS console',
    descriptionTemplate:
      'AWS services were accessed or configured via the console. Classified as aws_console with {confidence}% confidence by {model}.',
  },
  jenkins_ci_cd: {
    title: 'Interacted with Jenkins CI/CD',
    descriptionTemplate:
      'A Jenkins pipeline or job was triggered or monitored. Classified as jenkins_ci_cd with {confidence}% confidence by {model}.',
  },
  coding_editing: {
    title: 'Edited code in the editor',
    descriptionTemplate:
      'Source code was written or modified in an editor/IDE. Classified as coding_editing with {confidence}% confidence by {model}.',
  },
  debugging: {
    title: 'Debugged an issue',
    descriptionTemplate:
      'Debugging tools or techniques were used to investigate an issue. Classified as debugging with {confidence}% confidence by {model}.',
  },
  documentation: {
    title: 'Worked on documentation',
    descriptionTemplate:
      'Documentation files were created or edited. Classified as documentation with {confidence}% confidence by {model}.',
  },
  other: {
    title: 'Performed an unclassified action',
    descriptionTemplate:
      'An activity was detected that does not match a known category. Classified as other with {confidence}% confidence by {model}.',
  },
};

export function mapResultsToSteps(
  results: ClassificationResultDTO[],
  segmentDurationSec = 5,
): WorkflowStep[] {
  return results.map((r, i) => {
    const meta = LABEL_META[r.label] ?? LABEL_META['other'];
    const startSec = i * segmentDurationSec;
    const endSec = (i + 1) * segmentDurationSec;
    const confidencePct = Math.round(r.confidence * 100);

    return {
      n: i + 1,
      time: `${formatSeconds(startSec)}-${formatSeconds(endSec)}`,
      title: meta.title,
      description: meta.descriptionTemplate
        .replace('{confidence}', String(confidencePct))
        .replace('{model}', r.model_name),
    };
  });
}
