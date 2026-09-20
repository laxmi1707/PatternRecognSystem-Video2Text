from __future__ import annotations

# Keyword evidence for weak-labeling OCR'd frame text against app.ml.config.ACTIVITY_LABELS.
# Deliberately simple substring matching -- good enough to bootstrap a labeled
# dataset from real screen recordings, not a claim of semantic understanding.
ACTIVITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "git_operations": (
        "git ", "git commit", "git push", "git pull", "git merge", "git branch",
        "git checkout", "git rebase", "git clone", "git stash", "git log", "git diff", "git status",
    ),
    "docker_workflow": (
        "docker ", "dockerfile", "docker-compose", "docker compose",
        "docker build", "docker run", "docker ps", "docker exec",
    ),
    "kubernetes_ops": (
        "kubectl", "k8s", " pod ", "namespace", "helm ", "kubernetes", "minikube", "kubeconfig",
    ),
    "terraform_iac": (
        "terraform", "tfstate", "terraform apply", "terraform plan",
        "terraform init", 'resource "', 'provider "',
    ),
    "aws_console": (
        "aws ", "aws-cli", "s3://", "ec2", "lambda", "cloudformation",
        " iam ", "console.aws.amazon.com",
    ),
    "jenkins_ci_cd": (
        "jenkins", "jenkinsfile", "pipeline {", "stage(", "build #",
    ),
    "coding_editing": (
        "def ", "function ", "class ", "import ", "const ",
        "public class", "#include", "print(", "return ",
    ),
    "debugging": (
        "traceback", "exception", "stack trace", "breakpoint",
        "segfault", "panic:", "error:", "warning:",
    ),
    "documentation": (
        "readme", "## ", "# ", "markdown", ".md",
    ),
}

DEFAULT_ACTIVITY = "other"


def score_text(text: str) -> tuple[str, float, dict[str, int]]:
    """Score OCR'd text against keyword sets. Returns (best_activity, confidence, hit_counts).

    Confidence is a coarse function of keyword-hit count, not a calibrated
    probability -- it exists to feed the human-review threshold, not to be
    read as "percent chance correct".
    """
    lowered = text.lower()
    hit_counts = {
        activity: sum(lowered.count(kw) for kw in keywords)
        for activity, keywords in ACTIVITY_KEYWORDS.items()
    }
    best_activity = max(hit_counts, key=hit_counts.get)
    best_hits = hit_counts[best_activity]

    if best_hits == 0:
        return DEFAULT_ACTIVITY, 0.3, hit_counts

    confidence = min(0.95, 0.55 + 0.12 * best_hits)
    return best_activity, confidence, hit_counts
