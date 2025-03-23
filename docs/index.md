## Personal Automation Hub Overview

Server for personal automations using Python and FastAPI. Integration layer for services.

## User Stories

- Create Notion tasks via webhook
- Sync calendars both ways:
  - Google Calendar ↔ Personal calendar
- MCP for Perplexity API
- Scheduled tasks via cron
- Future MCP servers host

## Technical Stack

- Backend: Python 3.11+ with FastAPI
- Database: Supabase (PostgreSQL + realtime subscriptions)
- Authentication: Supabase Auth (built on OAuth2/JWT)
- Task scheduling: Celery with Redis + Flower (monitoring UI integrated with Streamlit)
- Deployment: Docker + Docker Compose + GitHub Actions for CI/CD
- API standards: OpenAPI 3.0, AsyncAPI for webhooks
- Interface: Streamlit dashboard for configuration and monitoring
- Hosting: AWS with Terraform infrastructure-as-code
  - ECS Fargate for containerized deployment
  - RDS for managed PostgreSQL
  - ElastiCache for Redis
  - CloudWatch for monitoring
  - Route53 for DNS
- MCP servers: Model Calling Protocol implementation for AI service orchestration

## Repository Structure

```
personal-automation-hub/
├── backend/              # Main FastAPI backend
│   ├── api/              # API routes and endpoints
│   │   ├── v1/           # API version 1
│   │   └── webhooks/     # Webhook handlers
│   ├── models/           # Data models and schemas
│   ├── services/         # Business logic and services
│   │   ├── notion/       # Notion integration services
│   │   ├── calendar/     # Calendar sync services
│   │   └── tasks/        # Task scheduling services
│   ├── core/             # Core application components
│   │   ├── config.py     # Configuration management
│   │   ├── security.py   # Authentication and security
│   │   └── celery_app.py # Celery configuration
│   ├── utils/            # Utility functions
│   └── tests/            # Unit and integration tests
├── terraform/            # Terraform IaC and Docker configurations
└── docker-compose.yml    # Run everything locally
```

### Future Extensions

MCP servers will be added to the repository structure later:
```
mcp_servers/              # Folder for all MCP servers
├── perplexity/           # MCP server for Perplexity
├── claude/               # MCP server for Claude
└── shared/               # Shared code for MCP servers
```

Frontend will be added after initial backend implementation:
```
frontend/                 # Streamlit interface
├── pages/                # Multi-page app structure
│   ├── home.py           # Home dashboard
│   ├── notion.py         # Notion integration settings
│   ├── calendar.py       # Calendar sync settings
│   └── tasks.py          # Task scheduling management
├── components/           # Reusable UI components
├── utils/                # UI utility functions
└── assets/               # Static assets and styles
```

## Integration Questions

- How to integrate MCP for Perplexity with other services?
- Best storage for API keys and credentials?
- Optimal hosting solution?
- Monitoring and logging strategy?

## Next Steps

- Create repo
- Set up FastAPI
- Implement Notion webhook
- Design Supabase schema 
