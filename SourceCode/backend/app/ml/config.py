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
    "diagram_design",    # draw.io, Inkscape, Miro, Visio, Excalidraw
    "media_editing",     # OpenShot, Kdenlive, Audacity, Blender, video/audio tools
    "file_management",   # Nautilus, Dolphin, file manager operations
    "image_editing",     # GIMP, Krita, Darktable, photo/raster editing
    "other",
]

NUM_CLASSES = len(ACTIVITY_LABELS)


# Model version served by default: the S3 prefix the backend downloads (MODEL_S3_PREFIX)
MODEL_VERSION_PREFIX = "models/v3"


def _default_model_dir() -> str:
    """MODEL_DIR, else ./<MODEL_S3_PREFIX>, so the local folder is named after the version in it."""
    return os.environ.get("MODEL_DIR") or f"./{os.environ.get('MODEL_S3_PREFIX', MODEL_VERSION_PREFIX)}"


@dataclass(frozen=True)
class MLConfig:
    seed: int = 42
    test_size: float = 0.2
    cv_folds: int = 5
    model_dir: str = _default_model_dir()
    num_classes: int = NUM_CLASSES
    # n_features is dynamic: 151 for hog backend, 1391 for cnn backend
    # Actual value resolved at runtime from TOTAL_FEATURES in feature_assembler
    n_features: int = 1391 if os.environ.get("FEATURE_BACKEND") == "cnn" else 151
    dataset_root: str = "./dataset"
    upload_dir: str = "./uploads"
    labels: tuple[str, ...] = field(
        default_factory=lambda: tuple(ACTIVITY_LABELS),
    )
