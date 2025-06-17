variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "personal-automation-hub"
}

variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "The CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "The availability zone for the subnet"
  type        = string
  default     = "us-east-1a"
}

variable "instance_type" {
  description = "The instance type for the EC2 instance"
  type        = string
  default     = "t2.micro"
}

variable "ami_id" {
  description = "The AMI ID for the EC2 instance (optional, will use latest Amazon Linux 2 if not specified)"
  type        = string
  default     = null
}

variable "key_name" {
  description = "The name of the key pair to use for SSH access"
  type        = string
  default     = null
}

variable "notion_api_key" {
  description = "The Notion API key"
  type        = string
  sensitive   = true
}

variable "notion_database_id" {
  description = "The Notion database ID"
  type        = string
  sensitive   = true
}

variable "webhook_api_key" {
  description = "The webhook API key"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "The domain name for the application (used for SSL certificate)"
  type        = string
  default     = null
} 