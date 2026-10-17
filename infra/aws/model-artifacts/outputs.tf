output "bucket_name" {
  description = "Model-artifacts bucket name"
  value       = aws_s3_bucket.models.id
}

output "bucket_arn" {
  description = "Model-artifacts bucket ARN"
  value       = aws_s3_bucket.models.arn
}

output "models_uri" {
  description = "S3 URI prefix for model artifacts"
  value       = "s3://${aws_s3_bucket.models.id}/${var.models_prefix}/"
}

output "models_read_policy_arn" {
  description = "IAM policy granting read-only access to the models prefix (attach to the backend runtime role)"
  value       = one(aws_iam_policy.models_read[*].arn)
}

output "models_read_policy_json" {
  description = "Read-only policy document, for creating the policy manually when create_read_policy = false"
  value       = data.aws_iam_policy_document.models_read.json
}
