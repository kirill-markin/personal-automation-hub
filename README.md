# Personal Automation Hub

A personal automation hub for integrating various services.

## Features

- Notion webhook integration for creating tasks via HTTP requests
  - Support for task title (required)
  - Support for task body content (optional)

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Unix/MacOS: `source .venv/bin/activate`
4. Install uv: `pip install uv`
5. Install dependencies: `uv pip install -e ".[dev]"`
6. Copy `.env.example` to `.env` and fill in your API keys

## Configuration

### Environment Variables Management

**IMPORTANT**: This project uses two configuration files that must be kept in sync:

1. **`.env`** - For local development
2. **`terraform/terraform.tfvars`** - For production deployment

Both files contain the same environment variables, but with different values:
- `.env` contains local/development values
- `terraform.tfvars` contains production values for AWS deployment

**You must manually ensure both files are updated when adding new variables or changing existing ones.**

### Local Configuration (.env)

In your `.env` file, configure the following variables:

```
NOTION_API_KEY=secret_your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
WEBHOOK_API_KEY=your_secure_api_key
```

### Production Configuration (terraform.tfvars)

The same variables must be configured in `terraform/terraform.tfvars` with production values:

```
webhook_api_key = "your_production_webhook_api_key"
notion_api_key = "secret_your_production_notion_api_key"
notion_database_id = "your_production_notion_database_id"
```

**Note**: Variable names in terraform.tfvars use snake_case format as required by Terraform.

## Running the Application

```bash
python run.py
```

The API will be available at http://localhost:8000

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example Usage (Local Development)

### Create a Notion task with title only

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/notion-personal/create-task \
    -H "X-API-Key: your_webhook_api_key" \
    -H "Content-Type: application/json" \
    -d '{"title": "My first task"}'
```

### Create a Notion task with title and body content

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/notion-personal/create-task \
    -H "X-API-Key: your_webhook_api_key" \
    -H "Content-Type: application/json" \
    -d '{"title": "Task with content", "body": "This is the detailed content that will appear as a paragraph in the Notion page."}'
```

**Request body parameters:**
- `title` (required): The task title that will appear as the page name
- `body` (optional): Text content that will be added as a paragraph block inside the page

Response:
```json
{"success":true,"task_id":"1bf02949-83d9-81fe-9ff8-e6ede9dc950c"}
```

## Production Usage (AWS Deployment)

### Finding the Production URL

To get the current production webhook URL:

1. **Navigate to terraform directory:**
   ```bash
   cd terraform
   ```

2. **Get the stable production URL:**
   ```bash
   terraform output webhook_url_stable
   ```
   This will show you the current stable URL using Elastic IP, e.g.:
   ```
   http://ec2-YOUR-ELASTIC-IP.compute-1.amazonaws.com:8000/api/v1/webhooks/notion-personal/create-task
   ```

### Finding the API Key

The webhook API key is stored in `terraform/terraform.tfvars`:

```bash
# From terraform directory
grep "webhook_api_key" terraform.tfvars
```

### Complete Production Example

#### Task with title only:
```bash
# Get the URL first
WEBHOOK_URL=$(cd terraform && terraform output -raw webhook_url_stable)

# Get the API key (replace with your actual key from terraform.tfvars)
API_KEY="your_webhook_api_key_from_terraform_tfvars"

# Create a task
curl -X POST "$WEBHOOK_URL" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"title": "Task created via production API"}'
```

#### Task with title and body content:
```bash
curl -X POST "$WEBHOOK_URL" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"title": "Detailed task", "body": "This task includes detailed instructions and context that will be visible when opening the page in Notion."}'
```

### Production URL Options

- **Stable URL (port 8000):** `terraform output webhook_url_stable`
- **Nginx URL (port 80):** `terraform output webhook_url_stable_http`
- **Current IP URL:** `terraform output webhook_url`

**Recommended:** Use the stable URL with Elastic IP for consistent access.

### Quick Production Test

```bash
# From project root
cd terraform
WEBHOOK_URL=$(terraform output -raw webhook_url_stable)
API_KEY=$(grep "webhook_api_key" terraform.tfvars | cut -d'"' -f2)

# Test with title only
curl -X POST "$WEBHOOK_URL" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"title": "Production test task"}'

# Test with title and body
curl -X POST "$WEBHOOK_URL" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"title": "Production test with content", "body": "This is a test task with body content to verify the API is working correctly."}'
```