output "api_url" {
  description = "HTTPS base URL for the frontend's VITE_API_BASE_URL"
  value       = "https://${aws_cloudfront_distribution.api.domain_name}/api/v1"
}

output "health_url" {
  description = "Backend health check through CloudFront"
  value       = "https://${aws_cloudfront_distribution.api.domain_name}/health"
}

output "alb_dns_name" {
  description = "ALB DNS name (accepts traffic from CloudFront only)"
  value       = aws_lb.backend.dns_name
}

output "ecs_cluster" {
  description = "Value for the ECS_CLUSTER GitHub variable"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service" {
  description = "Value for the ECS_SERVICE GitHub variable"
  value       = aws_ecs_service.backend.name
}

output "log_group" {
  description = "CloudWatch log group for the container"
  value       = aws_cloudwatch_log_group.backend.name
}
