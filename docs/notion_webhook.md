# Notion Webhook

## Overview
A simple API endpoint that allows creating tasks in Notion databases via HTTP requests. The webhook provides a secure way for external systems to create tasks without direct access to Notion.

## How It Works

### Architecture
- **API Endpoint**: FastAPI handles incoming requests at `/api/v1/webhooks/notion-personal/create-task`
- **Authentication**: API key validation using a header-based approach
- **Notion Client**: Communicates with Notion API to create database entries

### Implementation

The webhook consists of several key components:

1. **Configuration** (`backend/core/config.py`)
   - Loads environment variables for Notion API credentials and webhook security
   - Uses Pydantic for validation and type safety

2. **Security** (`backend/core/security.py`)
   - Validates the API key in request headers
   - Rejects unauthorized requests with 401 error

3. **API Models** (`backend/models/notion.py`)
   - Defines data structures for requests and responses
   - Ensures data validation with Pydantic

4. **Service Layer** (`backend/services/notion/client.py`)
   - Handles communication with Notion API
   - Creates tasks in the specified database

5. **API Endpoint** (`backend/api/v1/webhooks/notion.py`)
   - Receives and validates requests
   - Returns standardized responses with task IDs

### Request Flow
1. External system sends POST request with task title
2. API key validated through middleware
3. Request data validated with Pydantic model
4. Notion service creates task with title
5. Success response returned with task ID

## Usage

### Prerequisites
- Notion API key (integration token)
- Notion database ID
- Valid webhook API key

### Configuration
Set up environment variables in `.env` file:
```
NOTION_API_KEY=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
WEBHOOK_API_KEY=your_secure_webhook_key
```

### Making Requests
To create a task, send a POST request:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/notion-personal/create-task \
    -H "X-API-Key: your_webhook_api_key" \
    -H "Content-Type: application/json" \
    -d '{"title": "Task title"}'
```

### Response Format
Successful response:
```json
{
  "success": true,
  "task_id": "notion_page_id"
}
```

Error response:
```json
{
  "detail": "Error message"
}
```

## Security Considerations
- API key must be kept secure
- Notion API key has access to all integrated resources
- All sensitive values should be stored in environment variables
- `.env` file should be in `.gitignore` 