output "ecr_repository_url" {
  description = "Push the detector image here (see ../README.md)"
  value       = aws_ecr_repository.sop_detector.repository_url
}

output "detector_path" {
  description = "Append to the backend's CloudFront domain (its api_url without /api/v1)"
  value       = "/sop-detector"
}

output "ecs_cluster" {
  value = aws_ecs_cluster.sop_detector.name
}

output "ecs_service" {
  value = aws_ecs_service.sop_detector.name
}

output "log_group" {
  description = "CloudWatch log group for the detector container"
  value       = aws_cloudwatch_log_group.sop_detector.name
}
