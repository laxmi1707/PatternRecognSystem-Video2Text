output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.training.id
}

output "public_ip" {
  description = "Public IP of the training instance"
  value       = aws_instance.training.public_ip
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh -i ${var.key_pair_name}.pem ubuntu@${aws_instance.training.public_ip}"
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "http://${aws_instance.training.public_ip}:5173"
}

output "backend_url" {
  description = "Backend API docs URL"
  value       = "http://${aws_instance.training.public_ip}:8000/docs"
}
