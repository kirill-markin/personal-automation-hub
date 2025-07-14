# Terraform Infrastructure for Personal Automation Hub

This directory contains Terraform configuration to deploy the Personal Automation Hub application to AWS.

## Infrastructure Components

- VPC with public subnet
- EC2 instance running Docker container
- Security groups for the EC2 instance
- Optional S3 bucket for Terraform state

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform installed locally
- SSH key pair set up in your AWS account for EC2 access

## Configuration

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` and add your variables:
   - Required: `notion_api_key`, `notion_database_id`, `webhook_api_key`, `webhook_base_url`, `key_name`
   - Optional: Override any default settings as needed

## HTTPS Configuration (Optional)

To enable HTTPS with a valid SSL certificate:

1. Ensure you have a domain name with DNS pointing to your AWS instance
2. Add your domain name to `terraform.tfvars`:
   ```
   domain_name = "your-domain.example.com"
   ```
3. When deploying, Terraform will automatically:
   - Configure Nginx for HTTPS
   - Install Certbot and obtain a Let's Encrypt certificate
   - Configure automatic certificate renewal

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

## Deployment

Run the following commands from this directory:

```bash
terraform init    # Initialize terraform
terraform plan    # Preview changes
terraform apply   # Apply changes and deploy
```

After successful deployment, the outputs will show the public IP and domain name of your instance.

## Managing the Infrastructure

- To update the infrastructure: Make changes and run `terraform apply`
- To tear down: `terraform destroy`

## Access the Service

After deployment, the output will include the EC2 public IP and DNS name. You can access the webhook at:

```
http://<ec2_public_dns>:8000/api/v1/webhooks/notion-personal/create-task
```

Example using curl:

```bash
curl -X POST http://<ec2_public_dns>:8000/api/v1/webhooks/notion-personal/create-task \
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