# Personal Automation Hub

A personal automation hub for integrating various services.

## Features

- Notion webhook integration for creating tasks via HTTP requests

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

In your `.env` file, configure the following variables:

```
NOTION_API_KEY=secret_your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
WEBHOOK_API_KEY=your_secure_api_key
```

## Running the Application

```bash
python run.py
```

The API will be available at http://localhost:8000

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example Usage

Create a Notion task using cURL:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/notion/create_task \
    -H "X-API-Key: your_webhook_api_key" \
    -H "Content-Type: application/json" \
    -d '{"title": "My first task"}'
```

Response:
```json
{"success":true,"task_id":"1bf02949-83d9-81fe-9ff8-e6ede9dc950c"}
```