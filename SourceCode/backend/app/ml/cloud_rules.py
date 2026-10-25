"""Rule-based recognition of AWS console activity from text (OCR or task instructions).

The trained classifiers have (almost) no AWS console recordings to learn from, but the
console is easy to recognise from text: its URL, the service name in the header, page
titles, and banners/dialogs. These rules turn such text into

- a service area (``CLOUD_SERVICE_LABELS``): which part of AWS was used, and
- operations (``OPERATION_LABELS``): what was done there (create, delete, ...),

each with the evidence that matched, so a reviewer can see why a label was chosen.

Screen text needs care: the console always shows buttons such as "Create bucket" or
"Delete", so button words alone would report every operation on every page. For screen
text only phrases that appear *because* something happened count as operations: success
banners ("Successfully uploaded"), confirmation dialogs ("To confirm deletion, enter ..."),
dialog titles ("Delete objects", "Terminate instance?"). Instructions may use plain verbs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

CLOUD_SERVICE_LABELS: tuple[str, ...] = (
    "cloud_storage",            # S3, EBS, EFS, Glacier
    "cloud_compute",            # EC2, Lambda, ECS / Fargate
    "cloud_networking",         # VPC, subnets, security groups, load balancers, Route 53, CloudFront
    "cloud_identity_security",  # IAM, Secrets Manager, KMS, Certificate Manager
    "cloud_database",           # RDS, DynamoDB, Aurora
    "cloud_monitoring",         # CloudWatch, CloudTrail, billing
)
OPERATION_LABELS: tuple[str, ...] = ("create", "view", "modify", "upload", "delete")

# Confidence of a decision, by the strongest evidence behind the service area.
CONF_URL = 0.95
CONF_SERVICE_NAME = 0.85
CONF_GENERIC = 0.6

# Evidence that the text comes from the AWS console at all.
_CONSOLE = re.compile(
    r"console\.aws\.amazon\.com|\.amazonaws\.com|aws\.amazon\.com|aws management console"
    r"|\baws console\b|\bcloudshell\b"
)

# Console URLs, checked in order; only the first match counts. Specific pages come before
# the service they live in (security groups are part of the EC2 console URL).
_URL_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"securitygroup|#loadbalancer|#targetgroup|/vpc/|/vpcconsole|/cloudfront|/route53"),
     "cloud_networking"),
    (re.compile(r"/secretsmanager|/iam/|/iamv2|/kms|/acm/"), "cloud_identity_security"),
    (re.compile(r"/rds/|/dynamodb"), "cloud_database"),
    (re.compile(r"/cloudwatch|/cloudtrail|/billing|/cost-management"), "cloud_monitoring"),
    (re.compile(r"s3\.console|/s3/|/efs/|/glacier"), "cloud_storage"),
    (re.compile(r"/ec2/|/lambda/|/ecs/|/elasticbeanstalk"), "cloud_compute"),
]

# (service area, service names: strong evidence, generic words: only count with other
# AWS evidence). Order breaks ties: more specific areas first.
_SERVICE_WORDS: list[tuple[str, list[str], list[str]]] = [
    ("cloud_networking",
     ["security group", "security groups", "vpc", "route 53", "route53", "cloudfront", "elastic load balancing"],
     ["inbound rule", "inbound rules", "outbound rules", "subnet", "subnets", "load balancer",
      "target group", "internet gateway", "nat gateway"]),
    ("cloud_identity_security",
     ["secrets manager", "iam", "kms", "key management service", "certificate manager"],
     ["secret", "secrets", "access key", "role", "roles", "policy", "policies", "user group"]),
    ("cloud_database",
     ["rds", "dynamodb", "aurora"],
     ["database", "databases", "db instance", "db snapshot"]),
    ("cloud_monitoring",
     ["cloudwatch", "cloudtrail", "cost explorer"],
     ["log group", "log groups", "alarm", "alarms", "billing", "metrics"]),
    ("cloud_storage",
     ["s3", "amazon s3", "ebs", "efs", "glacier"],
     ["bucket", "buckets", "object", "objects", "volume", "volumes"]),
    ("cloud_compute",
     ["ec2", "lambda", "ecs", "fargate", "elastic beanstalk"],
     ["instance", "instances", "ami", "amis", "auto scaling", "function", "functions"]),
]

# Operations from phrases that only appear when something happened (safe for screen text).
_SCREEN_OPERATIONS: list[tuple[str, re.Pattern]] = [
    ("delete", re.compile(
        r"successfully (deleted|terminated|removed)|(deleted|terminated|removed) successfully"
        r"|to confirm (deletion|termination)|permanently delete|delete objects?\b|empty bucket"
        r"|terminate instances?\??|delete (bucket|secret|security group|role|user|policy|key)s?\?")),
    ("upload", re.compile(r"upload succeeded|successfully uploaded|uploaded successfully|upload: status"
                          r"|files and folders \(\d+")),
    ("create", re.compile(r"successfully created|created successfully|was created|has been created"
                          r"|successfully launched|launched successfully")),
    ("modify", re.compile(r"successfully (updated|modified|attached|edited|saved|rotated)"
                          r"|(updated|modified|attached|saved) successfully|changes (were )?saved")),
]

# Operations from verbs (instructions only: screen text always contains these words).
_INSTRUCTION_OPERATIONS: list[tuple[str, list[str]]] = [
    ("delete", ["delete", "terminate", "remove", "detach", "deregister", "destroy", "empty the bucket"]),
    ("upload", ["upload"]),
    ("create", ["create", "launch", "add", "new", "store", "provision", "set up"]),
    ("modify", ["edit", "update", "modify", "attach", "configure", "rotate", "change", "enable", "disable",
                "rename", "stop", "start", "reboot"]),
    ("view", ["view", "open", "describe", "search", "download", "list", "browse", "show", "check", "find"]),
]


def _word(w: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])")


_SERVICE_PATTERNS = [
    (area, [(w, _word(w)) for w in strong], [(w, _word(w)) for w in generic])
    for area, strong, generic in _SERVICE_WORDS
]
_INSTRUCTION_OP_PATTERNS = [(op, [_word(v) for v in verbs]) for op, verbs in _INSTRUCTION_OPERATIONS]


@dataclass
class CloudDecision:
    service: str  # one of CLOUD_SERVICE_LABELS
    confidence: float
    operations: list[str] = field(default_factory=list)  # in OPERATION_LABELS order of first appearance
    evidence: list[str] = field(default_factory=list)  # what matched, for review


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def is_aws_console(text: str) -> bool:
    return bool(_CONSOLE.search(_normalise(text)))


def detect_service(text: str, require_console: bool = True) -> tuple[str, float, list[str]] | None:
    """Most likely service area, its confidence, and the evidence; None if not AWS.

    With ``require_console`` (screen text) the text must show it is the AWS console: a
    console URL, "AWS Management Console", or at least one AWS service name. Generic words
    ("bucket", "instance") never decide on their own.
    """
    t = _normalise(text)
    for pattern, area in _URL_RULES:
        m = pattern.search(t)
        if m and (_CONSOLE.search(t) or not require_console):
            return area, CONF_URL, [f"url:{m.group(0)}"]

    scores: dict[str, float] = {}
    evidence: dict[str, list[str]] = {}
    strong_hit = False
    for area, strong, generic in _SERVICE_PATTERNS:
        for word, p in strong:
            n = len(p.findall(t))
            if n:
                scores[area] = scores.get(area, 0) + 2 * n
                evidence.setdefault(area, []).append(word)
                strong_hit = True
        for word, p in generic:
            n = len(p.findall(t))
            if n:
                scores[area] = scores.get(area, 0) + n
                evidence.setdefault(area, []).append(word)
    if not scores:
        return None
    if require_console and not (strong_hit or _CONSOLE.search(t)):
        return None
    if not strong_hit and not _CONSOLE.search(t) and not re.search(r"(?<![a-z])aws(?![a-z])", t):
        return None  # "create a new database" is not necessarily AWS
    order = [a for a, _, _ in _SERVICE_WORDS]
    best = max(scores, key=lambda a: (scores[a], -order.index(a)))
    conf = CONF_SERVICE_NAME if strong_hit else CONF_GENERIC
    return best, conf, evidence[best]


def detect_operations(text: str, source: str = "screen") -> list[str]:
    """Operations found in the text, in order of first appearance.

    ``source="screen"`` (OCR) uses only phrases caused by an action; ``"instruction"``
    also accepts plain verbs.
    """
    t = _normalise(text)
    found: list[tuple[int, str]] = []
    for op, pattern in _SCREEN_OPERATIONS:
        m = pattern.search(t)
        if m:
            found.append((m.start(), op))
    if source == "instruction":
        for op, patterns in _INSTRUCTION_OP_PATTERNS:
            starts = [m.start() for p in patterns for m in [p.search(t)] if m]
            if starts:
                found.append((min(starts), op))
    ops: list[str] = []
    for _, op in sorted(found):
        if op not in ops:
            ops.append(op)
    return ops


def decide_cloud_label(text: str, source: str = "screen") -> CloudDecision | None:
    """Service area + operations for AWS console text, or None if it is not AWS.

    ``source="screen"`` for OCR of a recording (must look like the console),
    ``"instruction"`` for a task description.
    """
    if not text or not text.strip():
        return None
    found = detect_service(text, require_console=(source == "screen"))
    if found is None:
        return None
    service, conf, evidence = found
    return CloudDecision(service=service, confidence=conf,
                         operations=detect_operations(text, source), evidence=evidence)
