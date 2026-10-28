# The SOP detector beside the backend: CloudFront -> the backend's ALB -> /sop-detector/*
# -> its own Fargate task.
#
# A separate root from infra/aws/ecs, with its own state, so nothing in the backend
# stack changes. It only READS the backend stack (its ALB, listener and security group,
# found by name) and adds one listener rule to that listener. CloudFront already sends
# every path to the ALB, so /sop-detector/* needs no CloudFront change.
#
# Order: apply infra/aws/ecs first, then this. Destroy this first, then infra/aws/ecs.
# Its own ECS cluster, so the backend's cluster can always be destroyed.

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
      Component   = "sop-detector"
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  name      = "${var.project_name}-sop-detector"
  image_uri = "${aws_ecr_repository.sop_detector.repository_url}:${var.image_tag}"
  role_arn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role"
}

# --- The backend stack, read only --------------------------------------------------------

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

data "aws_lb" "backend" {
  name = "${var.project_name}-alb"
}

data "aws_lb_listener" "http" {
  load_balancer_arn = data.aws_lb.backend.arn
  port              = 80
}

data "aws_security_group" "alb" {
  name   = "${var.project_name}-alb"
  vpc_id = data.aws_vpc.default.id
}

# --- Image repository --------------------------------------------------------------------

resource "aws_ecr_repository" "sop_detector" {
  name                 = local.name
  image_tag_mutability = "MUTABLE"
  force_delete         = true # destroy between demos removes the image too
}

# --- Network: the detector's tasks accept the ALB only ----------------------------------

resource "aws_security_group" "tasks" {
  name        = "${local.name}-tasks"
  description = "SOP detector Fargate tasks; service port from the ALB only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Service from ALB"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [data.aws_security_group.alb.id]
  }

  egress {
    description = "All outbound (ECR, CloudWatch Logs; there is no NAT)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- Routing: /sop-detector/* on the backend's listener ----------------------------------

resource "aws_lb_target_group" "sop_detector" {
  name                 = "${var.project_name}-sop-tg"
  port                 = var.container_port
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = data.aws_vpc.default.id
  deregistration_delay = 30

  health_check {
    path                = "/sop-detector/health"
    matcher             = "200"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 5
  }
}

resource "aws_lb_listener_rule" "sop_detector" {
  listener_arn = data.aws_lb_listener.http.arn
  priority     = var.listener_rule_priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.sop_detector.arn
  }

  condition {
    path_pattern {
      values = ["/sop-detector/*"]
    }
  }
}

# --- ECS ---------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "sop_detector" {
  name              = "/ecs/${local.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_cluster" "sop_detector" {
  name = local.name
}

resource "aws_ecs_task_definition" "sop_detector" {
  family                   = local.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  # The backend's execution role: pulls from ECR and writes logs. No task role is
  # needed - the models are inside the image.
  execution_role_arn = "${local.role_arn}/${var.execution_role_name}"

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "sop-detector"
      image     = local.image_uri
      essential = true
      portMappings = [
        { containerPort = var.container_port, protocol = "tcp" }
      ]
      environment = [
        { name = "SOP_DETECTOR_PORT", value = tostring(var.container_port) },
        { name = "SOP_DETECTOR_THREADS", value = tostring(floor(var.task_cpu / 1024)) },
        { name = "ALLOWED_ORIGINS", value = jsonencode(var.allowed_origins) },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.sop_detector.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "sop-detector"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "sop_detector" {
  name            = local.name
  cluster         = aws_ecs_cluster.sop_detector.id
  task_definition = aws_ecs_task_definition.sop_detector.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  # Pulling a ~3 GB image and importing torch take a few minutes.
  health_check_grace_period_seconds = 600

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = true # reach ECR without a NAT gateway
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.sop_detector.arn
    container_name   = "sop-detector"
    container_port   = var.container_port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener_rule.sop_detector]
}
