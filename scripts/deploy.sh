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
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Personal Automation Hub - Deployment Script${NC}"

# Get EC2 instance IP
cd "$PROJECT_DIR/terraform"
INSTANCE_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")
ELASTIC_IP=$(terraform output -raw elastic_ip 2>/dev/null || echo "")

if [ -z "$INSTANCE_IP" ]; then
    echo -e "${RED}❌ Error: Cannot get EC2 instance IP. Run 'terraform apply' first.${NC}"
    exit 1
fi

echo -e "${YELLOW}📍 Instance IP: $INSTANCE_IP${NC}"
echo -e "${YELLOW}📍 Elastic IP: $ELASTIC_IP${NC}"

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
            
            # Note: This assumes you have SSH key configured
            # You might need to adjust the SSH command based on your setup
            ssh -o StrictHostKeyChecking=no ec2-user@$ELASTIC_IP << 'EOF'
                cd /opt/app
                echo "📥 Pulling latest changes..."
                sudo git pull origin main
                echo "🔄 Rebuilding and restarting Docker containers..."
                sudo /usr/local/bin/docker-compose down
                sudo /usr/local/bin/docker-compose up -d --build
                echo "✅ Container status:"
                sudo docker ps | grep app-backend
EOF
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
            echo -e "${YELLOW}🔧 Tainting EC2 instance...${NC}"
            terraform taint aws_instance.app_server
            echo -e "${YELLOW}🔧 Applying changes...${NC}"
            terraform apply
            echo -e "${GREEN}✅ Full recreation completed!${NC}"
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

echo -e "${GREEN}🎯 Current webhook URLs:${NC}"
echo "  Stable: http://$ELASTIC_IP:8000/api/v1/webhooks/notion-personal/create-task"
echo "  HTTP:   http://$ELASTIC_IP/api/v1/webhooks/notion-personal/create-task" 