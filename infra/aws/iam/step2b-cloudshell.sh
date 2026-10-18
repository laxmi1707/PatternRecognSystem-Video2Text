#!/usr/bin/env bash
# Step 2b: add ec2:GetSecurityGroupsForVpc (needed to create the ALB), ec2:DeleteSecurityGroup
# (needed for terraform destroy) and ec2:GetManagedPrefixListEntries to ClaudeIAMRootUser.
# Paste into AWS CloudShell as an admin of 984263476980. Safe to re-run.
set -euo pipefail
mkdir -p ~/v2t-iam && cd ~/v2t-iam
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
        "ec2:DeleteSecurityGroup",
        "ec2:GetSecurityGroupsForVpc",
        "ec2:GetManagedPrefixListEntries",
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
BOUNDARY=arn:aws:iam::984263476980:policy/ClaudeIAMRootUserBoundary

aws iam put-user-policy --user-name ClaudeIAMRootUser --policy-name Video2TextFargate \
  --policy-document file://claude-user-fargate.json

V=$(aws iam get-policy --policy-arn "$BOUNDARY" --query Policy.DefaultVersionId --output text)
aws iam get-policy-version --policy-arn "$BOUNDARY" --version-id "$V" \
  --query PolicyVersion.Document > current-boundary.json
python3 merge_boundary.py current-boundary.json merged-boundary.json
N=$(aws iam list-policy-versions --policy-arn "$BOUNDARY" --query 'length(Versions)' --output text)
if [ "$N" -ge 5 ]; then
  OLDEST=$(aws iam list-policy-versions --policy-arn "$BOUNDARY" \
    --query 'sort_by(Versions[?IsDefaultVersion==`false`], &CreateDate)[0].VersionId' --output text)
  aws iam delete-policy-version --policy-arn "$BOUNDARY" --version-id "$OLDEST"
fi
aws iam create-policy-version --policy-arn "$BOUNDARY" \
  --policy-document file://merged-boundary.json --set-as-default --query PolicyVersion.VersionId --output text
echo "STEP 2b DONE (roll back: aws iam set-default-policy-version --policy-arn $BOUNDARY --version-id $V)"
