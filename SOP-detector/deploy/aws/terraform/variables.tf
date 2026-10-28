variable "aws_region" {
  description = "AWS region (the backend stack's)"
  type        = string
  default     = "ap-southeast-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to deploy with (null = default credential chain)"
  type        = string
  default     = null
}

variable "project_name" {
  description = "The backend stack's project_name; its ALB and ALB security group are found by it"
  type        = string
  default     = "video2text"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "dev"
}

variable "image_tag" {
  description = "Tag of the detector image in its ECR repository"
  type        = string
  default     = "latest"
}

variable "execution_role_name" {
  description = "The backend's ECS task execution role (ECR pull, CloudWatch Logs)"
  type        = string
  default     = "video2text-ecs-task-execution"
}

variable "container_port" {
  description = "Port the detector service listens on inside the task"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "Task CPU units. Measured on a 44 s video: 4 vCPU about 8.5 min, 2 vCPU about 13.5 min"
  type        = number
  default     = 4096
}

variable "task_memory" {
  description = "Task memory (MiB)"
  type        = number
  default     = 8192
}

variable "desired_count" {
  description = "Number of detector tasks (0 = stop paying for it but keep the setup)"
  type        = number
  default     = 1
}

variable "listener_rule_priority" {
  description = "Priority of the /sop-detector/* rule on the backend's listener (any unused number)"
  type        = number
  default     = 10
}

variable "allowed_origins" {
  description = "Browser origins allowed to call the detector directly (CORS)"
  type        = list(string)
  default     = ["http://localhost:5173", "http://127.0.0.1:5173"]
}

variable "log_retention_days" {
  description = "CloudWatch log retention"
  type        = number
  default     = 14
}
