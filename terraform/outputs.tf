output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "The ID of the public subnet"
  value       = aws_subnet.public.id
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

# Application URLs
output "webhook_url" {
  description = "The webhook URL for the Notion integration"
  value       = "http://${aws_instance.app_server.public_dns}:8000/api/v1/webhooks/notion-personal/create-task"
} 