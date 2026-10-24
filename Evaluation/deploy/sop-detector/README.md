# Deploying the SOP detector to AWS

The detector (`Evaluation/sop_detector_service.py`) runs as its own Fargate task behind
the backend's load balancer, at `/sop-detector/*` on the backend's CloudFront URL.

```
browser -> CloudFront (HTTPS) -> backend ALB --/api/*, /health------> backend task   (unchanged)
                                             \--/sop-detector/*----> detector task  (this folder)
```

**Nothing in the backend stack (`infra/aws/ecs`) changes.** This is a separate Terraform
root with its own state. It reads the backend's load balancer, listener and ALB security
group by name. Then it adds:

- one listener rule;
- its own ECR repository, ECS cluster and service, security group, target group and log
  group.

CloudFront already forwards every path to the load balancer, so it needs no change.

## Before you start

- The backend stack is applied (`infra/aws/ecs`). **Apply it first, destroy it last.**
  Destroy this stack before `infra/aws/ecs`.
- You need Docker, the AWS CLI and Terraform, with credentials that can:
  - create an ECR repository and push to it;
  - manage ECS, the load balancer's target groups and listener rules, EC2 security
    groups and CloudWatch log groups;
  - pass the role `video2text-ecs-task-execution` to ECS.

  This is the same set as the backend stack, plus ECR repository creation.

## Steps

All commands run from the repository root, in Bash.

```bash
# 1. Create the image repository only (the service needs an image before it can start)
cd Evaluation/deploy/sop-detector/terraform
terraform init
terraform apply -target=aws_ecr_repository.sop_detector
REPO=$(terraform output -raw ecr_repository_url)
cd -

# 2. Build the image (about 3 GB) and push it
bash Evaluation/deploy/sop-detector/build.sh
aws ecr get-login-password --region ap-southeast-1 | \
    docker login --username AWS --password-stdin "${REPO%%/*}"
docker tag video2text-sop-detector:latest "$REPO:latest"
docker push "$REPO:latest"

# 3. Create the rest: the listener rule, target group, cluster, service and logs
cd Evaluation/deploy/sop-detector/terraform
terraform apply

# 4. Check, after a few minutes (the task pulls the image and loads the models)
curl https://<backend CloudFront domain>/sop-detector/health
```

The CloudFront domain is the backend stack's `api_url` without `/api/v1`.

## Using it

The detector panel is on the frontend of the `feat/frontend` branch. Run that frontend
locally against the AWS deployment. Its dev server forwards `/api`, `/health` and
`/sop-detector` to AWS, so no CORS change is needed anywhere:

```bash
cd SourceCode/frontend
BACKEND_URL=https://<backend CloudFront domain> npm run dev -- --mode aws
# PowerShell: $env:BACKEND_URL="https://..."; npm run dev -- --mode aws
```

The four demo recordings (Bash 111479, Eclipse 52907 and 52918, VSCode 46738) are
answered at once from stored runs. Any other video is processed live, one at a time.

## Speed and cost

- **Speed**, measured on a 44 s video:
  - 4 vCPU (the default): about 8.5 minutes;
  - 2 vCPU: about 13.5 minutes.

  In this image, limited to 4 CPUs and 8 GB with `docker run --cpus 4 --memory 8g`, a
  23 s Gedit recording took 3.8 minutes and used about 1 GB of memory.
- **Where the time goes:** 95% of it is reading the screen once per second for the typing
  branch. Clicks take under 40 s.
- **Cost:** a 4 vCPU / 8 GB Fargate task is about US$0.20 per hour in Singapore, plus ECR
  storage for one image.

To stop paying, use either:

- `terraform apply -var desired_count=0` — keeps the setup;
- `terraform destroy` — **run it before** destroying `infra/aws/ecs`.

## Updating

The image takes every fitted model from one file, `Evaluation/models/sop_detector.pkl`
(`SOP_DETECTOR_PKL`). After retraining, write a new one with
`python -m detector.model_file build Evaluation/models/<new name>.pkl`, point `build.sh`
at it, then rebuild and push with the same tag and restart the service:

```bash
aws ecs update-service --cluster video2text-sop-detector \
    --service video2text-sop-detector --force-new-deployment
```

## Testing the image on your own machine

```bash
bash Evaluation/deploy/sop-detector/build.sh
docker run --rm -p 8100:8000 video2text-sop-detector:latest
# then, in SourceCode/frontend:  npm run dev   (proxies /sop-detector to localhost:8100)
```
