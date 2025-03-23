# Terraform Infrastructure for Personal Automation Hub

This directory contains Terraform configurations to deploy the Personal Automation Hub infrastructure to AWS.

## Infrastructure Components

- VPC with public subnet
- EC2 instance running Docker container
- Security groups for the EC2 instance
- Optional S3 bucket for Terraform state

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0.0
- AWS CLI configured with appropriate credentials

## AWS Credentials Configuration

Configure AWS CLI with your credentials before running any Terraform commands:

```bash
aws configure
```

You will be prompted to enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (use `us-east-1`)
- Default output format (optional)

## Deployment Steps

### 1. Prepare Environment Variables

Create a `terraform.tfvars` file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` to add your sensitive values:

```
# Only add application secrets, NOT AWS credentials
notion_api_key = "your-notion-api-key"
notion_database_id = "your-notion-database-id"
webhook_api_key = "your-secure-webhook-key"
key_name = "your-ssh-key-name"  # The SSH key for EC2 access
```

Note: Do NOT add AWS credentials to terraform.tfvars. Use AWS CLI configuration instead.

### 2. Deploy the Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

### 3. Access the Service

After deployment, the output will include the EC2 public IP and DNS name. You can access the webhook at:

```
http://<ec2_public_dns>:8000/api/v1/webhooks/notion/create_task
```

Example using curl:

```bash
curl -X POST http://<ec2_public_dns>:8000/api/v1/webhooks/notion/create_task \
    -H "X-API-Key: your_webhook_api_key" \
    -H "Content-Type: application/json" \
    -d '{"title": "My first task"}'
```

## Updating the Infrastructure

### Updating Application Code

The EC2 instance pulls the code directly from GitHub. To update:

1. Push changes to the GitHub repository
2. SSH into the EC2 instance: `ssh -i your-key.pem ec2-user@<ec2_public_dns>`
3. Navigate to the app directory: `cd /opt/app`
4. Pull the latest code: `git pull`
5. Restart the container: `docker-compose restart`

Alternatively, you can rebuild the infrastructure with `terraform apply` to get a fresh instance.

### Modifying Infrastructure

1. Make changes to the Terraform files
2. Run `terraform plan` to see the proposed changes
3. Run `terraform apply` to apply the changes

## Cleanup

To destroy all resources:

```bash
terraform destroy
``` 