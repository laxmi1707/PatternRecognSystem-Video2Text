# Backend on ECS Fargate: CloudFront (HTTPS) -> ALB (HTTP, CloudFront-only) -> Fargate task.
# Separate root from ../main.tf (EC2 training) and ../model-artifacts (S3 models), so
# `terraform destroy` here removes only the serving stack.
#
# Prerequisites (created by an IAM admin, see ../iam/): the task execution role, the task
# role (granted model read via the model-artifacts bucket policy), and an image pushed to
# ECR by .github/workflows/deploy-backend.yml.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  name      = var.project_name
  image_uri = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repository}:${var.image_tag}"
  role_arn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role"
}

# --- Network: default VPC, public subnets, no NAT gateway --------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

# CloudFront's origin-facing IP ranges, so the ALB only accepts traffic via CloudFront.
# The plural data source only needs ec2:DescribeManagedPrefixLists; the singular one
# also reads the entries (ec2:GetManagedPrefixListEntries), which isn't granted.
data "aws_ec2_managed_prefix_lists" "cloudfront" {
  filter {
    name   = "prefix-list-name"
    values = ["com.amazonaws.global.cloudfront.origin-facing"]
  }
}

resource "aws_security_group" "alb" {
  name        = "${local.name}-alb"
  description = "ALB for the backend; HTTP from CloudFront only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "HTTP from CloudFront"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    prefix_list_ids = data.aws_ec2_managed_prefix_lists.cloudfront.ids
  }

  egress {
    description = "To tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }
}

resource "aws_security_group" "tasks" {
  name        = "${local.name}-tasks"
  description = "Backend Fargate tasks; API port from the ALB only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "API from ALB"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # ECR, S3 (models) and CloudWatch Logs over the public internet; there is no NAT.
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- Load balancer -----------------------------------------------------------------------

resource "aws_lb" "backend" {
  name               = "${local.name}-alb"
  load_balancer_type = "application"
  internal           = false
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.public.ids
  idle_timeout       = 120 # video uploads
}

resource "aws_lb_target_group" "backend" {
  name                 = "${local.name}-tg"
  port                 = var.container_port
  protocol             = "HTTP"
  target_type          = "ip" # Fargate tasks register by IP
  vpc_id               = data.aws_vpc.default.id
  deregistration_delay = 30

  health_check {
    path                = "/health"
    matcher             = "200"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 5
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# --- ECS ---------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.ecr_repository}"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_cluster" "main" {
  name = var.cluster_name
}

resource "aws_ecs_task_definition" "backend" {
  family                   = var.service_name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = "${local.role_arn}/${var.execution_role_name}"
  task_role_arn            = "${local.role_arn}/${var.task_role_name}"

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = local.image_uri
      essential = true
      portMappings = [
        { containerPort = var.container_port, protocol = "tcp" }
      ]
      environment = [
        # SQLite inside the container: no database server, but data resets on redeploy.
        { name = "DATABASE_URL", value = "sqlite+aiosqlite:////app/video2text.db" },
        { name = "ALLOWED_ORIGINS", value = jsonencode(var.allowed_origins) },
        # Model version downloaded from S3 at startup (app/ml/model_sync.py).
        { name = "MODEL_S3_PREFIX", value = var.model_s3_prefix },
        # Visual features the models were trained on (app/pipeline/feature_assembler.py).
        { name = "FEATURE_BACKEND", value = var.feature_backend },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "backend" {
  name            = var.service_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  # Startup downloads models from S3 and imports torch before /health answers.
  health_check_grace_period_seconds = 300

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = true # reach ECR/S3 without a NAT gateway
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = var.container_port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.http]
}

# --- CloudFront: HTTPS endpoint for the Amplify (HTTPS) frontend ------------------------

data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer" {
  name = "Managed-AllViewerExceptHostHeader"
}

resource "aws_cloudfront_distribution" "api" {
  enabled         = true
  comment         = "${local.name} backend API"
  price_class     = "PriceClass_200" # includes Asia
  is_ipv6_enabled = true

  origin {
    origin_id   = "alb"
    domain_name = aws_lb.backend.dns_name

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      origin_read_timeout    = 60
    }
  }

  default_cache_behavior {
    target_origin_id         = "alb"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer.id
    compress                 = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
