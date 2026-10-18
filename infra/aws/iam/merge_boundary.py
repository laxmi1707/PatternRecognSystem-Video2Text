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
