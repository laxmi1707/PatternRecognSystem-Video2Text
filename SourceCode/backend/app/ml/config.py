from dataclasses import dataclass, field


ACTIVITY_LABELS = [
    "git_operations",
    "docker_workflow",
    "kubernetes_ops",
    "terraform_iac",
    "aws_console",
    "jenkins_ci_cd",
    "coding_editing",
    "debugging",
    "documentation",
    "other",
]

NUM_CLASSES = len(ACTIVITY_LABELS)


@dataclass(frozen=True)
class MLConfig:
    seed: int = 42
    test_size: float = 0.2
    cv_folds: int = 5
    model_dir: str = "./models"
    num_classes: int = NUM_CLASSES
    labels: tuple[str, ...] = field(
        default_factory=lambda: tuple(ACTIVITY_LABELS),
    )
