variable "aws_region" {
  description = "AWS region for the model-artifacts bucket"
  type        = string
  default     = "ap-southeast-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to deploy with (null = default credential chain)"
  type        = string
  default     = null
}

variable "project_name" {
  description = "Project name used for naming and tagging"
  type        = string
  default     = "video2knowledge"
}

variable "environment" {
  description = "Environment tag (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "bucket_name" {
  description = "Bucket name override. Leave null to use <project>-<env>-model-artifacts-<account_id>"
  type        = string
  default     = null
}

variable "models_prefix" {
  description = "Key prefix that holds trained model artifacts (no leading or trailing slash)"
  type        = string
  default     = "models"
}

variable "noncurrent_version_retention_days" {
  description = "Days to keep overwritten (noncurrent) object versions before deletion"
  type        = number
  default     = 90
}

variable "force_destroy" {
  description = "Allow terraform destroy to delete a non-empty bucket. Keep false outside throwaway envs"
  type        = bool
  default     = false
}

variable "create_read_policy" {
  description = "Create the read-only IAM policy for the models prefix (needs iam:CreatePolicy)"
  type        = bool
  default     = false
}
