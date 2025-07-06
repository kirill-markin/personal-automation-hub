terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.97.0"
    }
  }
  required_version = ">= 1.0.0"

  # Uncomment to use S3 backend instead of local
  /*
  backend "s3" {
    bucket         = "personal-automation-hub-terraform-state"
    key            = "personal-automation-hub/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
  */
}

# Basic VPC and networking
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnet (just one)
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Group for EC2 Instance
resource "aws_security_group" "app_server" {
  name        = "${var.project_name}-app-sg"
  description = "Security group for app server"
  vpc_id      = aws_vpc.main.id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Application port 8000
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-app-sg"
  }
}

# EC2 instance to run the application directly
resource "aws_instance" "app_server" {
  ami                    = var.ami_id != null ? var.ami_id : data.aws_ami.amazon_linux_2.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.app_server.id]
  subnet_id              = aws_subnet.public.id
  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    # Install dependencies
    yum update -y
    amazon-linux-extras install docker -y
    amazon-linux-extras install nginx1 -y
    service docker start
    service nginx start
    usermod -a -G docker ec2-user
    chkconfig docker on
    chkconfig nginx on
    yum install -y git

    # Install docker-compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    # Clone the repository
    mkdir -p /opt/app
    cd /opt/app
    git clone https://github.com/kirill-markin/personal-automation-hub.git .

    # Create environment file with proper values and ONLY environment variables
    cat > /opt/app/.env << EOF_ENV
# =============================================================================
# OTHER CONFIGURATION
# =============================================================================
WEBHOOK_API_KEY=${var.webhook_api_key}

# =============================================================================
# NOTION CONFIGURATION
# =============================================================================
NOTION_API_KEY=${var.notion_api_key}
NOTION_DATABASE_ID=${var.notion_database_id}

# =============================================================================
# GOOGLE CALENDAR CONFIGURATION
# =============================================================================
# Shared OAuth2 Configuration
GOOGLE_CLIENT_ID=${var.google_client_id != null ? var.google_client_id : ""}
GOOGLE_CLIENT_SECRET=${var.google_client_secret != null ? var.google_client_secret : ""}

# Calendar Sync Settings
DAILY_SYNC_HOUR=${var.daily_sync_hour}
DAILY_SYNC_TIMEZONE=${var.daily_sync_timezone}
MAX_GOOGLE_ACCOUNTS=${var.max_google_accounts}
MAX_SYNC_FLOWS=${var.max_sync_flows}

# Google Account 1 Configuration
GOOGLE_ACCOUNT_1_NAME=${var.google_account_1_name != null ? var.google_account_1_name : ""}
GOOGLE_ACCOUNT_1_CLIENT_ID=${var.google_account_1_client_id != null ? var.google_account_1_client_id : ""}
GOOGLE_ACCOUNT_1_CLIENT_SECRET=${var.google_account_1_client_secret != null ? var.google_account_1_client_secret : ""}
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=${var.google_account_1_refresh_token != null ? var.google_account_1_refresh_token : ""}

# Google Account 2 Configuration
GOOGLE_ACCOUNT_2_NAME=${var.google_account_2_name != null ? var.google_account_2_name : ""}
GOOGLE_ACCOUNT_2_CLIENT_ID=${var.google_account_2_client_id != null ? var.google_account_2_client_id : ""}
GOOGLE_ACCOUNT_2_CLIENT_SECRET=${var.google_account_2_client_secret != null ? var.google_account_2_client_secret : ""}
GOOGLE_ACCOUNT_2_REFRESH_TOKEN=${var.google_account_2_refresh_token != null ? var.google_account_2_refresh_token : ""}

# Sync Flow 1 Configuration
SYNC_FLOW_1_NAME=${var.sync_flow_1_name != null ? var.sync_flow_1_name : ""}
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=${var.sync_flow_1_source_account_id != null ? var.sync_flow_1_source_account_id : ""}
SYNC_FLOW_1_SOURCE_CALENDAR_ID=${var.sync_flow_1_source_calendar_id != null ? var.sync_flow_1_source_calendar_id : ""}
SYNC_FLOW_1_TARGET_ACCOUNT_ID=${var.sync_flow_1_target_account_id != null ? var.sync_flow_1_target_account_id : ""}
SYNC_FLOW_1_TARGET_CALENDAR_ID=${var.sync_flow_1_target_calendar_id != null ? var.sync_flow_1_target_calendar_id : ""}
SYNC_FLOW_1_START_OFFSET=${var.sync_flow_1_start_offset}
SYNC_FLOW_1_END_OFFSET=${var.sync_flow_1_end_offset}

# Sync Flow 2 Configuration
SYNC_FLOW_2_NAME=${var.sync_flow_2_name != null ? var.sync_flow_2_name : ""}
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=${var.sync_flow_2_source_account_id != null ? var.sync_flow_2_source_account_id : ""}
SYNC_FLOW_2_SOURCE_CALENDAR_ID=${var.sync_flow_2_source_calendar_id != null ? var.sync_flow_2_source_calendar_id : ""}
SYNC_FLOW_2_TARGET_ACCOUNT_ID=${var.sync_flow_2_target_account_id != null ? var.sync_flow_2_target_account_id : ""}
SYNC_FLOW_2_TARGET_CALENDAR_ID=${var.sync_flow_2_target_calendar_id != null ? var.sync_flow_2_target_calendar_id : ""}
SYNC_FLOW_2_START_OFFSET=${var.sync_flow_2_start_offset}
SYNC_FLOW_2_END_OFFSET=${var.sync_flow_2_end_offset}


EOF_ENV

    # Create Nginx config based on whether domain is set
    if [ "${var.domain_name != null ? var.domain_name : ""}" != "" ]; then
      # Create HTTPS config
      cat > /etc/nginx/conf.d/app.conf << EOF_NGINX
server {
    listen 80;
    server_name ${var.domain_name};

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name ${var.domain_name};

    # SSL Configuration (will be updated by Certbot)
    ssl_certificate /etc/letsencrypt/live/${var.domain_name}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${var.domain_name}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers EECDH+AESGCM:EDH+AESGCM;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF_NGINX
    else
      # Create HTTP only config
      cat > /etc/nginx/conf.d/app.conf << EOF_NGINX
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF_NGINX
    fi

    # Create initial self-signed certificate directory structure to prevent Nginx errors
    mkdir -p /etc/nginx/ssl/
    
    # Restart Nginx to apply the new configuration
    service nginx restart

    # Install Certbot for SSL if domain is specified
    if [ "${var.domain_name != null ? var.domain_name : ""}" != "" ]; then
      echo "Setting up SSL for domain ${var.domain_name}"
      # Install Certbot
      amazon-linux-extras install epel -y
      yum install -y certbot python2-certbot-nginx
      
      # Stop Nginx temporarily to allow Certbot to bind to port 80
      service nginx stop
      
      # Get certificate
      certbot certonly --standalone --non-interactive --agree-tos \
        --email admin@${var.domain_name} \
        -d ${var.domain_name} \
        --preferred-challenges http
      
      # Restart Nginx to pick up the new certificate
      service nginx start
      
      # Set up certificate renewal cron job
      echo "0 3 * * * /usr/bin/certbot renew --quiet --post-hook 'service nginx reload'" > /etc/cron.d/certbot-renew
    fi

    # Build and start the container
    cd /opt/app
    /usr/local/bin/docker-compose up -d
  EOF

  tags = {
    Name = "${var.project_name}-server"
  }
}

# Elastic IP for stable addressing
resource "aws_eip" "app_eip" {
  instance = aws_instance.app_server.id
  
  tags = {
    Name = "${var.project_name}-eip"
  }
}

# Use latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
} 