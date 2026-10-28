# Deploying the SOP detector to AWS

The detector runs as its own Fargate task behind the TRACE backend's load balancer, at
`/sop-detector/*` on the backend's CloudFront URL.

```
browser -> CloudFront (HTTPS) -> backend ALB --/api/*, /health------> backend task   (unchanged)
                                             \--/sop-detector/*----> detector task  (this folder)
```

**Nothing in the backend stack changes.** `terraform/` is a separate Terraform root with its
own state. It reads the backend's load balancer, listener and ALB security group by name,
then adds:

- one listener rule;
- its own ECR repository, ECS cluster and service, security group, target group and log
  group.

CloudFront already forwards every path to the load balancer, so it needs no change.

## Before you start

- The backend stack is applied. **Apply it first, destroy it last**: destroy this stack
  before the backend's.
- You need Docker, the AWS CLI and Terraform, with credentials that can:
  - create an ECR repository and push to it;
  - manage ECS, the load balancer's target groups and listener rules, EC2 security groups
    and CloudWatch log groups;
  - pass the role `video2text-ecs-task-execution` to ECS.

## Steps

Run from the repository root, in Bash.

```bash
# 1. Create the image repository only (the service needs an image before it can start)
cd deploy/aws/terraform
terraform init
terraform apply -target=aws_ecr_repository.sop_detector
REPO=$(terraform output -raw ecr_repository_url)
cd -

# 2. Build the image (about 4.5 GB) and push it
docker build -t sop-detector:latest .
aws ecr get-login-password --region ap-southeast-1 | \
    docker login --username AWS --password-stdin "${REPO%%/*}"
docker tag sop-detector:latest "$REPO:latest"
docker push "$REPO:latest"

# 3. Create the rest: the listener rule, target group, cluster, service and logs.
#    allowed_origins: the frontend origins that may call the detector, e.g. the Amplify URL.
cd deploy/aws/terraform
terraform apply -var 'allowed_origins=["https://<amplify domain>","http://localhost:5173"]'

# 4. Check, after a few minutes (the task pulls the image and loads the models)
curl https://<backend CloudFront domain>/sop-detector/health
```

The CloudFront domain is the backend's API URL without `/api/v1`. The TRACE frontend finds
the detector through `VITE_SOP_DETECTOR_URL` (for example
`https://<backend CloudFront domain>/sop-detector`), set when the frontend is built.

## Speed and cost

- **Speed**, measured on a 44 s video: about 8.5 minutes on 4 vCPU (the default), about 13.5
  minutes on 2 vCPU. 95% of the time is reading the screen once per second for typing;
  clicks take under 40 s. The four sample recordings are answered at once.
- **Cost:** a 4 vCPU / 8 GB Fargate task is about US$0.20-0.25 per hour in Singapore, plus
  ECR storage for one image.

To stop paying, use either:

- `terraform apply -var desired_count=0` - keeps the setup;
- `terraform destroy` - **run it before** destroying the backend stack.

## Updating the models

After retraining, write a new model file with
`python -m detector.model_file build models/<new name>.pkl`, point `SOP_DETECTOR_PKL` (or the
Dockerfile) at it, rebuild and push with the same tag, and restart the service:

```bash
aws ecs update-service --cluster video2text-sop-detector \
    --service video2text-sop-detector --force-new-deployment
```
