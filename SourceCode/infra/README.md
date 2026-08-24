# CI/CD: Docker → ECR → EKS

GitHub Actions builds the `backend` and `frontend` Docker images, pushes them
to Amazon ECR, and deploys them to EKS. Workflows:
`.github/workflows/backend-deploy.yml`, `.github/workflows/frontend-deploy.yml`.
Each triggers on push to `main` (path-filtered to its own directory) or manual
dispatch, authenticates to AWS via OIDC (no stored AWS keys), and applies the
manifests in `infra/k8s/`.

None of the steps below run automatically — they require your AWS
credentials, so run them yourself (AWS CLI or Console) before the workflows
can succeed.

## Prerequisites

1. **An EKS cluster** already running, with `kubectl` access. This repo does
   not provision the cluster itself (VPC, node groups, etc.) — only deploys
   into an existing one.
2. **AWS Load Balancer Controller** installed in the cluster (needed for
   `infra/k8s/ingress.yaml`):
   https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html
3. A domain (or you can skip the Ingress and `kubectl port-forward` /
   use a `LoadBalancer` Service instead for a quick test).

## 1. Create the GitHub OIDC identity provider (once per AWS account)

Skip this if your account already has `token.actions.githubusercontent.com`
registered as an identity provider.

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

## 2. Create the IAM role GitHub Actions will assume

Trust policy — scope `sub` to this exact repo and branch so no other repo
can assume the role. Replace `<AWS_ACCOUNT_ID>`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:laxmi1707/PatternRecognSystem-Video2Text:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Permissions policy — ECR push/pull plus EKS auth token retrieval:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:CreateRepository"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["eks:DescribeCluster"],
      "Resource": "*"
    }
  ]
}
```

```bash
aws iam create-role \
  --role-name video2text-github-actions \
  --assume-role-policy-document file://trust-policy.json

aws iam put-role-policy \
  --role-name video2text-github-actions \
  --policy-name video2text-ecr-eks \
  --policy-document file://permissions-policy.json
```

## 3. Grant the role access inside the cluster (EKS RBAC)

The IAM role also needs a Kubernetes-side identity mapping so `kubectl`
commands run by the workflow are authorized:

```bash
aws eks create-access-entry \
  --cluster-name <EKS_CLUSTER_NAME> \
  --principal-arn arn:aws:iam::<AWS_ACCOUNT_ID>:role/video2text-github-actions

aws eks associate-access-policy \
  --cluster-name <EKS_CLUSTER_NAME> \
  --principal-arn arn:aws:iam::<AWS_ACCOUNT_ID>:role/video2text-github-actions \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy \
  --access-scope type=namespace,namespaces=video2text
```

## 4. Set GitHub repo variables and secrets

Settings → Secrets and variables → Actions.

**Variables**
| Name | Example |
|---|---|
| `AWS_REGION` | `us-east-1` |
| `EKS_CLUSTER_NAME` | `video2text-cluster` |
| `APP_DOMAIN` | `video2text.com` |

**Secrets**
| Name | Value |
|---|---|
| `AWS_OIDC_ROLE_ARN` | `arn:aws:iam::<AWS_ACCOUNT_ID>:role/video2text-github-actions` |

## 5. Fill in the remaining placeholder

`infra/k8s/backend-configmap.yaml` has `__FRONTEND_ORIGIN__` — set it to the
deployed frontend URL (e.g. `https://video2text.com`) so CORS allows
the frontend to call the backend.

## Layout

```
backend/Dockerfile           # multi-stage: pip install → slim runtime, uvicorn on :8000
frontend/Dockerfile          # multi-stage: npm build → nginx serving the static bundle on :80
frontend/nginx.conf          # SPA fallback routing (try_files → index.html)
infra/k8s/                   # plain Kubernetes manifests, applied directly by the workflows
.github/workflows/
  backend-deploy.yml         # build → push to ECR → deploy Deployment+Service to EKS
  frontend-deploy.yml        # build → push to ECR → deploy Deployment+Service+Ingress to EKS
```

Image tags are the triggering commit SHA (plus a rolling `latest`), so each
deploy is traceable to a commit and `kubectl rollout undo` works normally.

## Local smoke test

```bash
docker build -t video2text-backend ./backend && docker run -p 8000:8000 video2text-backend
docker build -t video2text-frontend ./frontend && docker run -p 8080:80 video2text-frontend
```
