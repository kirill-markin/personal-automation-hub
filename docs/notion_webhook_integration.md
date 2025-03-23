# Notion Webhook Integration

## Technical Specification

### Overview
Simple webhook integration for creating tasks in Notion. Allows external systems to create tasks in a Notion database via HTTP requests with just a title.

### API Endpoint
- **Path**: `/api/v1/webhooks/notion/create_task`
- **Method**: POST
- **Authentication**: API Key (required in header)

### Request Payload
```json
{
  "title": "Task title"
}
```

### Response
```json
{
  "success": true,
  "task_id": "notion_page_id"
}
```

### Error Handling
- 400: Invalid request payload
- 401: Unauthorized (invalid API key)
- 500: Error creating Notion task

### Implementation Details

#### Components
1. **Webhook Controller**: FastAPI endpoint handler for incoming requests
2. **Notion Service**: Business logic for Notion API integration
3. **Authentication Middleware**: API key validation

#### Data Flow
1. External system sends POST request with task title
2. API key validated through middleware
3. Notion service creates task with title
4. Response returned with task ID or error

#### Dependencies
- Notion API Client (v1)
- FastAPI for endpoint handling
- Pydantic for data validation

#### Configuration
Environment variables stored in a `.env` file:
- `NOTION_API_KEY`: Secret key for Notion API access
- `NOTION_DATABASE_ID`: Notion database ID for tasks
- `WEBHOOK_API_KEY`: API key for webhook access

Example `.env` file:
```
NOTION_API_KEY=secret_abcdef123456
NOTION_DATABASE_ID=1234567890abcdef
WEBHOOK_API_KEY=my-secure-api-key
```

Also provide a `.env.example` file in the repository as a template.

### Security Considerations
- API key validation for all requests
- Proper error handling
- Ensure .env file is in .gitignore to prevent secrets from being committed

## Implementation Architecture

### Directory Structure
The implementation follows a modular structure:
- `main.py`: FastAPI application entry point
- `api/v1/webhooks/notion.py`: Notion webhook endpoint
- `core/config.py`: Environment configuration
- `core/security.py`: API key validation
- `services/notion.py`: Notion API interaction
- `models/notion.py`: Pydantic models for requests/responses

### Implementation Flow

1. **Environment Configuration**: Create a Settings class with Pydantic to load environment variables from .env file, including Notion API key, database ID, and webhook API key.

2. **API Key Authentication**: Implement middleware that validates the API key in the request header against the configured webhook API key.

3. **Request/Response Models**: Define Pydantic models for the request (with title field) and response (with success and task_id fields).

4. **Notion Service**: Create a service class that uses the Notion API client to create tasks in the specified database. The service takes a title and returns the created task's ID.

5. **Webhook Endpoint**: Implement a FastAPI endpoint that validates the request, uses the Notion service to create the task, and returns a response with the task ID.

6. **FastAPI Application**: Set up the main application with router for the Notion webhook endpoint.

### Making a Request
To create a task, send a POST request to the endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/notion/create_task \
    -H "X-API-Key: your_webhook_api_key" \
    -H "Content-Type: application/json" \
    -d '{"title": "My first task"}'
```

### Running the Application
1. Create and populate the `.env` file with required variables
2. Install dependencies: fastapi, uvicorn, notion-client, python-dotenv
3. Start the application with uvicorn

### API Documentation
FastAPI automatically generates interactive API documentation at:
- /docs (Swagger UI)
- /redoc (ReDoc) 