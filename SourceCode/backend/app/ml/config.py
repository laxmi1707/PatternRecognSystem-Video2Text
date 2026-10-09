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
    "terminal_ops",      # shell commands, file system, process management
    "system_config",     # settings, preferences, themes, permissions, packages
    "web_browsing",      # browser navigation, search, bookmarks
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
    n_features: int = 151  # 50 OCR + 30 UI + 40 visual + 30 interaction + 1 has_action_log
    dataset_root: str = "./dataset"
    upload_dir: str = "./uploads"
    labels: tuple[str, ...] = field(
        default_factory=lambda: tuple(ACTIVITY_LABELS),
    )
