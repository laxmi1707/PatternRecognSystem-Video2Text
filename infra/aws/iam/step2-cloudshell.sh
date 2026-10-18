#!/usr/bin/env bash
# Step 2 (IAM for ECS Fargate). Paste into AWS CloudShell as an admin of 984263476980.
# Self-contained: writes its own policy files, so nothing has to be uploaded.
set -euo pipefail
mkdir -p ~/v2t-iam && cd ~/v2t-iam
cat > ecs-tasks-trust.json <<'EOF_V2T'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ecs-tasks.amazonaws.com" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": { "aws:SourceAccount": "984263476980" },
        "ArnLike": { "aws:SourceArn": "arn:aws:ecs:ap-southeast-1:984263476980:*" }
      }
    }
  ]
}
EOF_V2T
cat > claude-user-fargate.json <<'EOF_V2T'
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "FargateEcs", "Effect": "Allow", "Action": "ecs:*", "Resource": "*" },
    { "Sid": "FargateLoadBalancer", "Effect": "Allow", "Action": "elasticloadbalancing:*", "Resource": "*" },
    { "Sid": "FargateCloudFront", "Effect": "Allow", "Action": "cloudfront:*", "Resource": "*" },
    { "Sid": "FargateEc2Describe", "Effect": "Allow", "Action": "ec2:Describe*", "Resource": "*" },
    {
      "Sid": "FargateSecurityGroups",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "FargateReadTaskRoles",
      "Effect": "Allow",
      "Action": "iam:GetRole",
      "Resource": [
        "arn:aws:iam::984263476980:role/video2text-ecs-task-execution",
        "arn:aws:iam::984263476980:role/video2text-ecs-task"
      ]
    },
    {
      "Sid": "FargatePassTaskRoles",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::984263476980:role/video2text-ecs-task-execution",
        "arn:aws:iam::984263476980:role/video2text-ecs-task"
      ],
      "Condition": { "StringEquals": { "iam:PassedToService": "ecs-tasks.amazonaws.com" } }
    },
    {
      "Sid": "FargateServiceLinkedRoles",
      "Effect": "Allow",
      "Action": "iam:CreateServiceLinkedRole",
      "Resource": "arn:aws:iam::984263476980:role/aws-service-role/*",
      "Condition": {
        "StringEquals": {
          "iam:AWSServiceName": ["ecs.amazonaws.com", "elasticloadbalancing.amazonaws.com"]
        }
      }
    }
  ]
}
EOF_V2T
cat > github-deploy-ecs.json <<'EOF_V2T'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EcsDeployService",
      "Effect": "Allow",
      "Action": ["ecs:UpdateService", "ecs:DescribeServices"],
      "Resource": "arn:aws:ecs:ap-southeast-1:984263476980:service/video2text/video2text-backend"
    },
    { "Sid": "EcrAuth", "Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*" },
    {
      "Sid": "EcrPushBackend",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "arn:aws:ecr:ap-southeast-1:984263476980:repository/video2text-backend"
    }
  ]
}
EOF_V2T
cat > merge_boundary.py <<'EOF_V2T'
"""Merge the Fargate statements into the current ClaudeIAMRootUserBoundary document.

A new boundary version replaces the whole document, so the existing statements
must be carried over. Statements whose Sid already exists are replaced, so
running this twice does not duplicate anything.

Usage:
    python merge_boundary.py current-boundary.json merged-boundary.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Already granted by the user's managed policies (ECR, CloudWatch Logs); the
# boundary must allow them too or they are denied.
EXTRA_BOUNDARY_STATEMENTS = [
    {"Sid": "FargateLogs", "Effect": "Allow", "Action": "logs:*", "Resource": "*"},
    {"Sid": "FargateEcr", "Effect": "Allow", "Action": "ecr:*", "Resource": "*"},
]


def main() -> None:
    current_path, merged_path = Path(sys.argv[1]), Path(sys.argv[2])
    current = json.loads(current_path.read_text(encoding="utf-8-sig"))
    # get-policy-version --query PolicyVersion.Document returns the document itself
    statements = current["Statement"]
    if isinstance(statements, dict):
        statements = [statements]

    new = json.loads((HERE / "claude-user-fargate.json").read_text())["Statement"]
    new += EXTRA_BOUNDARY_STATEMENTS
    new_sids = {s["Sid"] for s in new}

    kept = [s for s in statements if s.get("Sid") not in new_sids]
    merged = {"Version": "2012-10-17", "Statement": kept + new}
    merged_path.write_text(json.dumps(merged, indent=2))

    size = len(json.dumps(merged, separators=(",", ":")))
    print(f"kept {len(kept)} existing statements, added {len(new)}; {size} chars (limit 6144)")


if __name__ == "__main__":
    main()
EOF_V2T
ACCT=984263476980
BOUNDARY=arn:aws:iam::$ACCT:policy/ClaudeIAMRootUserBoundary

create_role() {
  if aws iam get-role --role-name "$1" > /dev/null 2>&1; then
    echo "role $1 already exists, skipping create"
  else
    aws iam create-role --role-name "$1" --assume-role-policy-document file://ecs-tasks-trust.json > /dev/null
    echo "created role $1"
  fi
}

echo "== 2a ECS roles"
create_role video2text-ecs-task-execution
aws iam attach-role-policy --role-name video2text-ecs-task-execution \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
create_role video2text-ecs-task

echo "== 2b ClaudeIAMRootUser permissions"
aws iam put-user-policy --user-name ClaudeIAMRootUser --policy-name Video2TextFargate \
  --policy-document file://claude-user-fargate.json

echo "== 2c ClaudeIAMRootUserBoundary"
V=$(aws iam get-policy --policy-arn "$BOUNDARY" --query Policy.DefaultVersionId --output text)
aws iam get-policy-version --policy-arn "$BOUNDARY" --version-id "$V" \
  --query PolicyVersion.Document > current-boundary.json
python3 merge_boundary.py current-boundary.json merged-boundary.json
N=$(aws iam list-policy-versions --policy-arn "$BOUNDARY" --query 'length(Versions)' --output text)
if [ "$N" -ge 5 ]; then
  OLDEST=$(aws iam list-policy-versions --policy-arn "$BOUNDARY" \
    --query 'sort_by(Versions[?IsDefaultVersion==`false`], &CreateDate)[0].VersionId' --output text)
  echo "boundary has 5 versions, deleting oldest non-default $OLDEST"
  aws iam delete-policy-version --policy-arn "$BOUNDARY" --version-id "$OLDEST"
fi
aws iam create-policy-version --policy-arn "$BOUNDARY" \
  --policy-document file://merged-boundary.json --set-as-default --query PolicyVersion.VersionId --output text

echo "== 2d video2text-github-deploy"
aws iam put-role-policy --role-name video2text-github-deploy --policy-name ECSDeploy \
  --policy-document file://github-deploy-ecs.json
echo "deploy role boundary (null = none):"
aws iam get-role --role-name video2text-github-deploy --query Role.PermissionsBoundary

echo "STEP 2 DONE (previous boundary version was $V; roll back with:"
echo "  aws iam set-default-policy-version --policy-arn $BOUNDARY --version-id $V )"
