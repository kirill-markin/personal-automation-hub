# Personal Automation Hub

A personal automation hub for integrating various services.

## Features

### Notion Integration
- Notion webhook integration for creating tasks via HTTP requests
  - Support for task title (required)
  - Support for task body content (optional)

### Google Calendar Synchronization
- Automatic "Busy" block creation across multiple calendars
- Real-time sync via Google Calendar webhooks
- Daily backup sync via polling
- Multi-account support (personal + work calendars)
- Configurable time offsets for busy blocks
- Event filtering (2+ participants required, busy/free transparency)
- Idempotent operations (duplicate-safe)

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

#### Notion Integration
```
NOTION_API_KEY=secret_your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
WEBHOOK_API_KEY=your_secure_api_key
WEBHOOK_BASE_URL=http://localhost:8000
```

#### Google Calendar Synchronization
```
# OAuth2 Credentials
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# Account Configuration (repeat for each account)
GOOGLE_ACCOUNT_1_EMAIL=personal@gmail.com
GOOGLE_ACCOUNT_1_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=1//04_your_refresh_token_here

GOOGLE_ACCOUNT_2_EMAIL=work@company.com
GOOGLE_ACCOUNT_2_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_2_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_2_REFRESH_TOKEN=1//04_your_work_refresh_token

# Sync Flow Configuration
DAILY_SYNC_HOUR=6
DAILY_SYNC_TIMEZONE=UTC

SYNC_FLOW_1_NAME=Work to Personal
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=2
SYNC_FLOW_1_SOURCE_CALENDAR_ID=work.email@company.com
SYNC_FLOW_1_TARGET_ACCOUNT_ID=1
SYNC_FLOW_1_TARGET_CALENDAR_ID=personal.email@gmail.com
SYNC_FLOW_1_START_OFFSET=-15
SYNC_FLOW_1_END_OFFSET=15

SYNC_FLOW_2_NAME=Personal to Work
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_2_SOURCE_CALENDAR_ID=personal.email@gmail.com
SYNC_FLOW_2_TARGET_ACCOUNT_ID=2
SYNC_FLOW_2_TARGET_CALENDAR_ID=work.email@company.com
SYNC_FLOW_2_START_OFFSET=-15
SYNC_FLOW_2_END_OFFSET=15
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

## Code Deployment

### Deployment Script

Use the deployment script for convenient code updates:

```bash
# Quick deployment (recommended for most changes)
./scripts/deploy.sh quick

# Full recreation (for major changes or when something is broken)
./scripts/deploy.sh recreate
```

### Deployment Methods

1. **Quick Deployment** (`./scripts/deploy.sh quick`)
   - ⚡ Fast: 5-10 seconds
   - 🔄 Minimal downtime: ~2-3 seconds
   - ✅ Good for: code changes, configuration updates
   - ❌ Not for: dependency changes, system-level changes

2. **Full Recreation** (`./scripts/deploy.sh recreate`)
   - 🐌 Slow: 2-3 minutes
   - 🔄 Downtime: ~1-2 minutes
   - ✅ Good for: dependency changes, system fixes, "nuclear option"
   - ✅ Guarantees: clean state, latest code

### Manual Deployment

For manual deployment without the script:

```bash
# Quick method (SSH + Git Pull)
INSTANCE_IP=$(cd terraform && terraform output -raw elastic_ip)
ssh ec2-user@$INSTANCE_IP "cd /opt/app && sudo git pull origin main && sudo /usr/local/bin/docker-compose down && sudo /usr/local/bin/docker-compose up -d --build"

# Full recreation method
cd terraform
terraform taint aws_instance.app_server
terraform apply
```

**Note:** Changes must be pushed to GitHub before deployment - EC2 instance pulls code from the repository.

## Google Calendar & Gmail Setup

For detailed Google Calendar synchronization and Gmail automation setup:

1. **[Google Calendar Setup Guide](docs/google_calendar_setup.md)** - Complete setup instructions (includes Gmail OAuth)
2. **[Configuration Examples](docs/configuration_examples.md)** - Common sync scenarios
3. **[API Documentation](docs/calendar_sync.md)** - Technical details
4. **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions

### Quick Start for Google Calendar & Gmail

1. **Setup OAuth2 credentials** in Google Cloud Console (enable both Calendar and Gmail APIs)
2. **Obtain refresh tokens** for each account:
   ```bash
   python scripts/setup_google_oauth.py --account-id 1
   python scripts/setup_google_oauth.py --account-id 2
   ```
   **Note**: The script will now request both Calendar and Gmail permissions.
3. **Configure sync flows** in `.env` file
4. **Test the setup**:
   ```bash
   python -m pytest tests/integration/test_calendar_access.py -m integration -v
   ```
5. **Start the server**: `python run.py`

### Google Calendar Features

- **Event Filtering**: Only events with 2+ participants are synced
- **Busy/Free Transparency**: Only events marked as 'busy' (opaque) are synced; 'free' (transparent) events are ignored
- **All-Day Events Support**: All-day events are synchronized without time offsets and preserve their all-day format
- **Time Offsets**: Configurable minutes before/after event for busy blocks (applied only to regular timed events)
- **Real-time Sync**: Webhooks provide immediate synchronization
- **Backup Sync**: Daily polling catches any missed events
- **Multi-Account**: Support for unlimited Google accounts
- **Idempotent**: Safe to run multiple times without duplicates

### Example Sync Scenarios

- **Work-Life Balance**: Sync work calendar to personal (and vice versa)
- **Team Coordination**: Share availability across team members
- **Client Management**: Different buffer times for different client types
- **Multiple Views**: One calendar syncing to multiple target calendars

### Transparency (Busy/Free) Logic

The system now respects the Google Calendar transparency setting:

- **Busy Events (opaque)**: Events marked as "busy" will create busy blocks in target calendars
- **Free Events (transparent)**: Events marked as "free" will be ignored and no busy blocks will be created
- **Automatic Cleanup**: If you change an event from busy to free, existing busy blocks will be automatically deleted
- **Dynamic Updates**: Real-time webhook updates handle transparency changes immediately

This allows for more granular control over which events should block time in synchronized calendars.

### All-Day Events Support

The system intelligently handles all-day events differently from regular timed events:

- **All-Day Events**: No time offsets applied, busy blocks preserve all-day format
- **Regular Events**: Time offsets applied (e.g., -15 minutes start, +15 minutes end)
- **Multi-Day Events**: Events with specific times across multiple days still get offsets

**Example**: A vacation day (all-day) creates an all-day busy block, while a 2pm meeting creates a busy block from 1:45pm to 2:15pm.

For complete details, see [All-Day Events Documentation](docs/all_day_events.md).