import os
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
    model_dir: str = os.environ.get("MODEL_DIR", "./models/v2" if os.environ.get("FEATURE_BACKEND") == "cnn" else "./models")
    num_classes: int = NUM_CLASSES
    # n_features is dynamic: 151 for hog backend, 1391 for cnn backend
    # Actual value resolved at runtime from TOTAL_FEATURES in feature_assembler
    n_features: int = 1391 if os.environ.get("FEATURE_BACKEND") == "cnn" else 151
    dataset_root: str = "./dataset"
    upload_dir: str = "./uploads"
    labels: tuple[str, ...] = field(
        default_factory=lambda: tuple(ACTIVITY_LABELS),
    )
