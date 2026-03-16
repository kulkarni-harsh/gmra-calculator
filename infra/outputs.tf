output "alb_dns_name" {
  description = "Raw ALB DNS (for debugging — use your domain in production)"
  value       = aws_lb.main.dns_name
}

output "app_url" {
  description = "Your app's public URL"
  value       = "https://${var.domain_name}"
}

output "name_servers" {
  description = "Paste these 4 values into Namecheap → Domain → Nameservers → Custom DNS"
  value       = aws_route53_zone.main.name_servers
}

output "ecr_backend_url" {
  description = "ECR repository URL for the backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  description = "ECR repository URL for the frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}
