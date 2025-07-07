output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "The ID of the public subnet"
  value       = aws_subnet.public.id
}

# S3 bucket output
output "ssl_certificates_bucket" {
  description = "S3 bucket for SSL certificates backup"
  value       = aws_s3_bucket.ssl_certs.id
}

# EC2 outputs
output "ec2_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.app_server.public_ip
}

output "ec2_public_dns" {
  description = "The public DNS address of the EC2 instance"
  value       = aws_instance.app_server.public_dns
}

# Elastic IP outputs
output "elastic_ip" {
  description = "The stable Elastic IP address"
  value       = aws_eip.app_eip.public_ip
}

output "elastic_ip_dns" {
  description = "The stable public DNS associated with the Elastic IP"
  value       = aws_eip.app_eip.public_dns
}

# Application URLs
output "webhook_url" {
  description = "The webhook URL for the Notion integration"
  value       = "http://${aws_instance.app_server.public_dns}:8000/api/v1/webhooks/notion-personal/create-task"
}

output "webhook_url_stable" {
  description = "The stable webhook URL for the Notion integration (uses Elastic IP)"
  value       = "http://${aws_eip.app_eip.public_dns}:8000/api/v1/webhooks/notion-personal/create-task"
}

output "webhook_url_stable_http" {
  description = "The stable webhook URL for the Notion integration via HTTP port 80 (Nginx)"
  value       = "http://${aws_eip.app_eip.public_dns}/api/v1/webhooks/notion-personal/create-task"
}

# Domain and HTTPS outputs
output "domain_name" {
  description = "The configured domain name for the application"
  value       = var.domain_name
}

output "webhook_url_https" {
  description = "The HTTPS webhook URL for the Notion integration (if domain is configured)"
  value       = var.domain_name != null ? "https://${var.domain_name}/api/v1/webhooks/notion-personal/create-task" : null
} 