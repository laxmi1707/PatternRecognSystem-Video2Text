variable "aws_region" {
  description = "AWS region for the serving stack"
  type        = string
  default     = "ap-southeast-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to deploy with (null = default credential chain)"
  type        = string
  default     = null
}

variable "project_name" {
  description = "Name prefix for the ALB, target group and security groups"
  type        = string
  default     = "video2text"
}

variable "environment" {
  description = "Environment tag (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "cluster_name" {
  description = "ECS cluster name; must match the ECS_CLUSTER GitHub variable"
  type        = string
  default     = "video2text"
}

variable "service_name" {
  description = "ECS service and task family name; must match the ECS_SERVICE GitHub variable"
  type        = string
  default     = "video2text-backend"
}

variable "ecr_repository" {
  description = "ECR repository the deploy workflow pushes to"
  type        = string
  default     = "video2text-backend"
}

variable "image_tag" {
  description = "Image tag the task runs. The workflow pushes :latest and forces a new deployment"
  type        = string
  default     = "latest"
}

variable "execution_role_name" {
  description = "Task execution role (ECR pull, CloudWatch Logs)"
  type        = string
  default     = "video2text-ecs-task-execution"
}

variable "task_role_name" {
  description = "Task role the app runs as (S3 model read via the bucket policy)"
  type        = string
  default     = "video2text-ecs-task"
}

variable "container_port" {
  description = "Port uvicorn listens on"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "Fargate task CPU units (2048 = 2 vCPU)"
  type        = number
  default     = 2048
}

variable "task_memory" {
  description = "Fargate task memory in MiB; torch + YOLO + EasyOCR need several GB"
  type        = number
  default     = 8192
}

variable "desired_count" {
  description = "Running tasks. Exactly 1: SQLite lives inside each task, and a running task keeps the models, the OCR reader and the feature cache warm (no cold start)"
  type        = number
  default     = 1

  validation {
    condition     = var.desired_count == 1
    error_message = "desired_count must be 1: 0 means a cold start for the next user, and >1 splits the SQLite data between tasks."
  }
}

variable "allowed_origins" {
  description = "CORS origins allowed to call the API (the frontend's URL)"
  type        = list(string)
  default     = ["https://main.d2tjfo3h4t5uox.amplifyapp.com"]
}

variable "model_s3_prefix" {
  description = "S3 prefix of the model version to load (models/v1 = Tier 1 only, models/v2 = all tiers, models/v3 = 6 retrained models)"
  type        = string
  default     = "models/v3"
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for the container logs"
  type        = number
  default     = 14
}
