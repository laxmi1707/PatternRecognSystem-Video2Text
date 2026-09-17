from enum import Enum

from pydantic import BaseModel


class ActivityLabel(str, Enum):
    GIT_OPERATIONS = "git_operations"
    DOCKER_WORKFLOW = "docker_workflow"
    KUBERNETES_OPS = "kubernetes_ops"
    TERRAFORM_IAC = "terraform_iac"
    AWS_CONSOLE = "aws_console"
    JENKINS_CI_CD = "jenkins_ci_cd"
    CODING_EDITING = "coding_editing"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class ClassifyRequest(BaseModel):
    features: list[float]
    model_name: str | None = None


class ClassifyBatchRequest(BaseModel):
    features: list[list[float]]
    model_name: str | None = None


class ClassificationResult(BaseModel):
    label: ActivityLabel
    confidence: float
    probabilities: dict[str, float]
    model_name: str
    latency_ms: float


class ClassifyBatchResponse(BaseModel):
    results: list[ClassificationResult]
    model_name: str
    latency_ms: float
