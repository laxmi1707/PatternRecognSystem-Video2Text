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
  terminal_ops: {
    title: 'Ran terminal commands',
    descriptionTemplate:
      'Commands were executed in a terminal or shell session. Classified as terminal_ops with {confidence}% confidence by {model}.',
  },
  system_config: {
    title: 'Configured system settings',
    descriptionTemplate:
      'System or application settings were modified. Classified as system_config with {confidence}% confidence by {model}.',
  },
  web_browsing: {
    title: 'Browsed the web',
    descriptionTemplate:
      'A web browser was used to navigate pages or search. Classified as web_browsing with {confidence}% confidence by {model}.',
  },
  other: {
    title: 'Performed an unclassified action',
    descriptionTemplate:
      'An activity was detected that does not match a known category. Classified as other with {confidence}% confidence by {model}.',
  },
};

const TERMINAL_LABELS = new Set(['terminal_ops', 'debugging', 'git_operations', 'docker_workflow']);

const UI_NOISE = /\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Activities|Terminal|Applications|Places|System|Files|Settings)\b/;

function extractCommand(ocrText: string): string {
  if (!ocrText) return '';
  const parts = ocrText.split(/[$#]\s+/);
  for (let i = parts.length - 1; i >= 1; i--) {
    const cmd = parts[i].split(/\n|\s{3,}/)[0]
      .replace(/[\s;]\S+\s*@\s*\S+.*/, '')
      .trim();
    if (cmd.length > 3 && cmd.split(' ').length <= 10 && !UI_NOISE.test(cmd))
      return cmd.slice(0, 80);
  }
  return '';
}

type RiskRule = { labels: string[]; keywords: string[]; level: 'high' | 'medium'; reason: string };

const RISK_RULES: RiskRule[] = [
  { labels: ['aws_console'], keywords: ['delete', 'terminate', 'destroy', 'purge', 'deregister'], level: 'high', reason: 'Destructive AWS operation detected' },
  { labels: [], keywords: ['rm -rf', 'rm -r /', 'drop table', 'drop database', 'truncate table', 'chmod 777', 'sudo rm'], level: 'high', reason: 'Destructive command visible on screen' },
  { labels: [], keywords: ['--force', '--hard', 'force-push', 'force push', 'password', 'secret', 'private_key', 'access_key'], level: 'high', reason: 'Sensitive operation or credential visible on screen' },
  { labels: ['terraform_iac', 'kubernetes_ops'], keywords: ['destroy', 'drain', 'force-delete'], level: 'high', reason: 'Irreversible infrastructure change detected' },
  { labels: ['docker_workflow', 'kubernetes_ops'], keywords: ['prune', 'force', 'kill', 'remove', 'delete'], level: 'medium', reason: 'Potentially destructive container operation' },
  { labels: ['debugging'], keywords: ['exception', 'crash', 'fatal', 'killed', 'traceback', 'segfault'], level: 'medium', reason: 'Error or crash detected during debugging' },
];

function assessRisk(label: string, ocrText: string): { risk_level: 'high' | 'medium' | 'none'; risk_reason: string } {
  if (!ocrText) return { risk_level: 'none', risk_reason: '' };
  const text = ocrText.toLowerCase();
  for (const rule of RISK_RULES) {
    const labelMatch = rule.labels.length === 0 || rule.labels.includes(label);
    if (labelMatch && rule.keywords.some(kw => text.includes(kw))) {
      return { risk_level: rule.level, risk_reason: rule.reason };
    }
  }
  return { risk_level: 'none', risk_reason: '' };
}

export function mapResultsToSteps(results: ClassificationResultDTO[]): WorkflowStep[] {
  return results.map((r, i) => {
    const meta = LABEL_META[r.label] ?? LABEL_META['other'];
    const confidencePct = Math.round(r.confidence * 100);
    const startSec = r.start_time ?? i * 5;
    const endSec = r.end_time ?? (i + 1) * 5;

    const cmd = TERMINAL_LABELS.has(r.label) ? extractCommand(r.ocr_text ?? '') : '';
    const title = cmd ? `Run: \`${cmd}\`` : meta.title;
    const description = cmd
      ? `Execute: \`${cmd}\`. Classified as ${r.label.replace('_', ' ')} with ${confidencePct}% confidence by ${r.model_name}.`
      : meta.descriptionTemplate
          .replace('{confidence}', String(confidencePct))
          .replace('{model}', r.model_name);

    const { risk_level, risk_reason } = assessRisk(r.label, r.ocr_text ?? '');

    return {
      n: i + 1,
      time: `${formatSeconds(startSec)}-${formatSeconds(endSec)}`,
      title,
      description,
      risk_level,
      risk_reason,
    };
  });
}
