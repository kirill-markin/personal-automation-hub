# =============================================================================
# OTHER CONFIGURATION
# =============================================================================

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

# =============================================================================
# NOTION CONFIGURATION
# =============================================================================

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

# =============================================================================
# GOOGLE CALENDAR CONFIGURATION
# =============================================================================

# Shared OAuth2 Configuration
variable "google_client_id" {
  description = "Google OAuth2 client ID for Calendar API"
  type        = string
  sensitive   = true
  default     = null
}

variable "google_client_secret" {
  description = "Google OAuth2 client secret for Calendar API"
  type        = string
  sensitive   = true
  default     = null
}

# Calendar Sync Settings
variable "daily_sync_hour" {
  description = "Hour of day (0-23) for daily calendar sync polling"
  type        = number
  default     = 6
}

variable "daily_sync_timezone" {
  description = "Timezone for daily calendar sync schedule"
  type        = string
  default     = "UTC"
}

variable "max_google_accounts" {
  description = "Maximum number of Google accounts to scan for in environment variables"
  type        = number
  default     = 10
}

variable "max_sync_flows" {
  description = "Maximum number of sync flows to scan for in environment variables"
  type        = number
  default     = 50
}

# Google Account 1 Configuration
variable "google_account_1_email" {
  description = "Email for Google account 1"
  type        = string
  default     = null
}

variable "google_account_1_client_id" {
  description = "Google OAuth2 client ID for account 1"
  type        = string
  sensitive   = true
  default     = null
}

variable "google_account_1_client_secret" {
  description = "Google OAuth2 client secret for account 1"
  type        = string
  sensitive   = true
  default     = null
}

variable "google_account_1_refresh_token" {
  description = "Google OAuth2 refresh token for account 1"
  type        = string
  sensitive   = true
  default     = null
}

# Google Account 2 Configuration
variable "google_account_2_email" {
  description = "Email for Google account 2"
  type        = string
  default     = null
}

variable "google_account_2_client_id" {
  description = "Google OAuth2 client ID for account 2"
  type        = string
  sensitive   = true
  default     = null
}

variable "google_account_2_client_secret" {
  description = "Google OAuth2 client secret for account 2"
  type        = string
  sensitive   = true
  default     = null
}

variable "google_account_2_refresh_token" {
  description = "Google OAuth2 refresh token for account 2"
  type        = string
  sensitive   = true
  default     = null
}

# Sync Flow 1 Configuration
variable "sync_flow_1_name" {
  description = "Name for sync flow 1"
  type        = string
  default     = null
}

variable "sync_flow_1_source_account_id" {
  description = "Source account ID for sync flow 1"
  type        = number
  default     = null
}

variable "sync_flow_1_source_calendar_id" {
  description = "Source calendar ID for sync flow 1"
  type        = string
  default     = null
}

variable "sync_flow_1_target_account_id" {
  description = "Target account ID for sync flow 1"
  type        = number
  default     = null
}

variable "sync_flow_1_target_calendar_id" {
  description = "Target calendar ID for sync flow 1"
  type        = string
  default     = null
}

variable "sync_flow_1_start_offset" {
  description = "Start offset in minutes for sync flow 1 (negative for before)"
  type        = number
  default     = -15
}

variable "sync_flow_1_end_offset" {
  description = "End offset in minutes for sync flow 1 (positive for after)"
  type        = number
  default     = 15
}

# Sync Flow 2 Configuration
variable "sync_flow_2_name" {
  description = "Name for sync flow 2"
  type        = string
  default     = null
}

variable "sync_flow_2_source_account_id" {
  description = "Source account ID for sync flow 2"
  type        = number
  default     = null
}

variable "sync_flow_2_source_calendar_id" {
  description = "Source calendar ID for sync flow 2"
  type        = string
  default     = null
}

variable "sync_flow_2_target_account_id" {
  description = "Target account ID for sync flow 2"
  type        = number
  default     = null
}

variable "sync_flow_2_target_calendar_id" {
  description = "Target calendar ID for sync flow 2"
  type        = string
  default     = null
}

variable "sync_flow_2_start_offset" {
  description = "Start offset in minutes for sync flow 2 (negative for before)"
  type        = number
  default     = -15
}

variable "sync_flow_2_end_offset" {
  description = "End offset in minutes for sync flow 2 (positive for after)"
  type        = number
  default     = 15
}

 