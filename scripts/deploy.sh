#!/bin/bash

# Personal Automation Hub - Deployment Script
# Usage: ./scripts/deploy.sh [method]
# Methods: quick, recreate, docker

set -e

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Personal Automation Hub - Deployment Script${NC}"

# Function to handle SSH known_hosts for recreated instances
handle_ssh_known_hosts() {
    local ip=$1
    local method=$2
    
    if [ "$method" = "recreate" ]; then
        echo -e "${BLUE}🔐 SSH Security Notice:${NC}"
        echo "When recreating EC2 instances, SSH host keys change."
        echo "You have several options:"
        echo "  1. Remove old key manually: ssh-keygen -R $ip"
        echo "  2. Let this script handle it (less secure for production)"
        echo "  3. Cancel and handle manually for maximum security"
        echo ""
        read -p "Should this script automatically update known_hosts? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}🔧 Removing old SSH key for $ip...${NC}"
            ssh-keygen -R $ip 2>/dev/null || true
            echo -e "${GREEN}✅ SSH key removed${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  You'll need to manually remove the old SSH key before connecting${NC}"
            echo -e "${YELLOW}   Run: ssh-keygen -R $ip${NC}"
            return 1
        fi
    fi
    return 0
}

# Function to execute SSH commands with better security
ssh_exec() {
    local ip=$1
    local commands=$2
    
    # Use accept-new instead of no checking - more secure
    ssh -o StrictHostKeyChecking=accept-new \
        -o UserKnownHostsFile=~/.ssh/known_hosts \
        -o ConnectTimeout=10 \
        ec2-user@$ip "$commands"
}

# Get EC2 instance IP and domain configuration
cd "$PROJECT_DIR/terraform"
INSTANCE_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")
ELASTIC_IP=$(terraform output -raw elastic_ip 2>/dev/null || echo "")
DOMAIN_NAME=$(terraform output -raw domain_name 2>/dev/null || echo "")

if [ -z "$INSTANCE_IP" ]; then
    echo -e "${RED}❌ Error: Cannot get EC2 instance IP. Run 'terraform apply' first.${NC}"
    exit 1
fi

echo -e "${YELLOW}📍 Instance IP: $INSTANCE_IP${NC}"
echo -e "${YELLOW}📍 Elastic IP: $ELASTIC_IP${NC}"
if [ -n "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "null" ]; then
    echo -e "${YELLOW}📍 Domain: $DOMAIN_NAME${NC}"
fi

METHOD=${1:-quick}

case $METHOD in
    "quick")
        echo -e "${GREEN}🔄 Quick deployment (SSH + Git Pull)${NC}"
        echo "This will:"
        echo "1. SSH to EC2 instance"
        echo "2. Pull latest code from GitHub"
        echo "3. Restart the service"
        echo "4. Check service status"
        echo ""
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}🔧 Updating code on remote server...${NC}"
            
            ssh_exec $ELASTIC_IP '
                cd /opt/app
                echo "📥 Pulling latest changes..."
                sudo git pull origin main
                echo "🔄 Rebuilding and restarting Docker containers..."
                sudo /usr/local/bin/docker-compose down
                sudo /usr/local/bin/docker-compose up -d --build
                echo "✅ Container status:"
                sudo docker ps | grep app-backend
            '
            echo -e "${GREEN}✅ Quick deployment completed!${NC}"
        else
            echo -e "${YELLOW}❌ Deployment cancelled${NC}"
        fi
        ;;
        
    "recreate")
        echo -e "${GREEN}🔄 Full recreation (Terraform taint + apply)${NC}"
        echo "This will:"
        echo "1. Mark EC2 instance for recreation"
        echo "2. Destroy old instance"
        echo "3. Create new instance with latest code"
        echo "4. Takes ~2-3 minutes with downtime"
        echo ""
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Handle SSH known_hosts before recreation
            handle_ssh_known_hosts $ELASTIC_IP "recreate"
            
            echo -e "${YELLOW}🔧 Tainting EC2 instance...${NC}"
            terraform taint aws_instance.app_server
            echo -e "${YELLOW}🔧 Applying changes...${NC}"
            terraform apply -auto-approve
            echo -e "${GREEN}✅ Full recreation completed!${NC}"
            
            # Update variables after terraform apply
            DOMAIN_NAME=$(terraform output -raw domain_name 2>/dev/null || echo "")
            
            # Wait a bit for the instance to be ready
            echo -e "${YELLOW}⏳ Waiting for instance to be ready...${NC}"
            sleep 30
            
            # Test HTTPS only if domain is configured
            if [ -n "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "null" ]; then
                echo -e "${YELLOW}🔍 Testing SSL certificate deployment...${NC}"
                echo "Checking if HTTPS is working for domain: $DOMAIN_NAME"
                HTTPS_ROOT_URL="https://$DOMAIN_NAME/"
                for i in {1..12}; do
                    if curl -I -s -k "$HTTPS_ROOT_URL" >/dev/null 2>&1; then
                        echo -e "${GREEN}✅ HTTPS is working!${NC}"
                        break
                    elif [ $i -eq 12 ]; then
                        echo -e "${YELLOW}⚠️  HTTPS not ready yet, check logs manually${NC}"
                    else
                        echo -e "${YELLOW}   Attempt $i/12 - waiting 20 seconds...${NC}"
                        sleep 20
                    fi
                done
            else
                echo -e "${YELLOW}ℹ️  No domain configured, skipping HTTPS check${NC}"
            fi
        else
            echo -e "${YELLOW}❌ Deployment cancelled${NC}"
        fi
        ;;
        
    "docker")
        echo -e "${GREEN}🔄 Docker deployment${NC}"
        echo "This requires Docker setup on EC2 instance"
        echo "Not implemented yet - use 'quick' or 'recreate' methods"
        ;;
        
    *)
        echo -e "${RED}❌ Unknown method: $METHOD${NC}"
        echo "Available methods:"
        echo "  quick    - SSH + Git Pull (fast, minimal downtime)"
        echo "  recreate - Terraform taint + apply (slow, guaranteed clean state)"
        echo "  docker   - Docker-based deployment (not implemented)"
        echo ""
        echo "Usage: $0 [method]"
        exit 1
        ;;
esac

# Update final variables to show current state
cd "$PROJECT_DIR/terraform"
ELASTIC_IP=$(terraform output -raw elastic_ip 2>/dev/null || echo "")
DOMAIN_NAME=$(terraform output -raw domain_name 2>/dev/null || echo "")

echo -e "${GREEN}🎯 Current service URLs:${NC}"
echo "  Stable: http://$ELASTIC_IP:8000/"
echo "  HTTP:   http://$ELASTIC_IP/"

# Check if HTTPS is available (only if domain is configured)
if [ -n "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "null" ]; then
    HTTPS_ROOT_URL="https://$DOMAIN_NAME/"
    if curl -I -s -k "$HTTPS_ROOT_URL" >/dev/null 2>&1; then
        echo -e "${GREEN}  HTTPS:  $HTTPS_ROOT_URL${NC}"
    else
        echo -e "${YELLOW}  HTTPS:  $HTTPS_ROOT_URL (not ready)${NC}"
    fi
else
    echo -e "${YELLOW}  HTTPS:  Not configured (set domain_name in terraform.tfvars)${NC}"
fi 