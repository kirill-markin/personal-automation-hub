# Google Calendar Synchronization Documentation

## Overview

The Google Calendar synchronization feature automatically creates "Busy" blocks in target calendars when events with 2 or more participants are created or updated in source calendars. This prevents double-booking across multiple calendar views.

## System Architecture

### Components

1. **Google Calendar Client** (`backend/services/google_calendar/client.py`)
   - OAuth2 refresh token authentication
   - Calendar API operations (list, create, delete events)
   - Webhook subscription management
   - Rate limiting and error handling with retry mechanisms

2. **Account Manager** (`backend/services/google_calendar/account_manager.py`)
   - Manages multiple Google accounts
   - Handles OAuth2 credentials and client creation
   - Provides account validation and health checks

3. **Sync Engine** (`backend/services/google_calendar/sync_engine.py`)
   - Core synchronization logic
   - Event filtering and processing
   - Busy block creation and deletion
   - Support for multiple sync flows

4. **Webhook Handler** (`backend/services/google_calendar/webhook_handler.py`)
   - Receives Google Calendar push notifications
   - Validates webhook signatures
   - Triggers real-time event processing

5. **Polling Scheduler** (`backend/services/google_calendar/polling_scheduler.py`)
   - Daily backup synchronization
   - Configurable schedule and time ranges
   - Catches any missed webhook events

6. **Configuration Loader** (`backend/services/google_calendar/config_loader.py`)
   - Loads multi-account configuration from environment variables
   - Validates sync flow configurations
   - Provides configuration management

## Configuration

### Environment Variables

The system uses environment variables for configuration, supporting multiple accounts and sync flows:

#### Shared OAuth2 Configuration
```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

#### Account Configuration
```bash
# Account N configuration
GOOGLE_ACCOUNT_N_EMAIL=account@gmail.com
GOOGLE_ACCOUNT_N_CLIENT_ID=client_id_for_account_n
GOOGLE_ACCOUNT_N_CLIENT_SECRET=client_secret_for_account_n
GOOGLE_ACCOUNT_N_REFRESH_TOKEN=refresh_token_for_account_n
```

#### Sync Flow Configuration
```bash
# Sync Flow N configuration
SYNC_FLOW_N_NAME=Flow Display Name
SYNC_FLOW_N_SOURCE_ACCOUNT_ID=source_account_id
SYNC_FLOW_N_SOURCE_CALENDAR_ID=source_calendar_id
SYNC_FLOW_N_TARGET_ACCOUNT_ID=target_account_id
SYNC_FLOW_N_TARGET_CALENDAR_ID=target_calendar_id
SYNC_FLOW_N_START_OFFSET=minutes_before_event_start
SYNC_FLOW_N_END_OFFSET=minutes_after_event_end
```

#### Polling Schedule
```bash
SYNC_INTERVAL_MINUTES=60  # Sync interval in minutes (default: hourly)
```

#### Webhook Configuration
```bash
WEBHOOK_BASE_URL=http://your-server.com:8000  # Base URL for webhook endpoints
WEBHOOK_API_KEY=your_secure_api_key  # API key for webhook authentication
```

### Data Models

#### Core Models

```python
class GoogleAccount(BaseModel):
    """Configuration for a single Google account"""
    account_id: int
    name: str
    client_id: str
    client_secret: str
    refresh_token: str

class SyncFlow(BaseModel):
    """Configuration for a single sync flow"""
    name: str
    source_account_id: int
    source_calendar_id: str
    target_account_id: int
    target_calendar_id: str
    start_offset: int  # minutes
    end_offset: int    # minutes

class CalendarEvent(BaseModel):
    """Calendar event data structure"""
    id: str
    calendar_id: str
    account_id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    participants: List[str]
    participant_count: int
    status: str
    creator: str
    organizer: str
    transparency: str  # "opaque" (busy) or "transparent" (free)
```

#### Processing Models

```python
class BusyBlock(BaseModel):
    """Busy block configuration"""
    title: str = "Busy"
    start_time: datetime
    end_time: datetime
    target_account_id: int
    target_calendar_id: str
    source_event_id: str

class EventProcessingResult(BaseModel):
    """Result of processing a single event"""
    flow_name: str
    event_id: str
    event_title: str
    sync_type: str  # "webhook" or "polling"
    success: bool
    action: str  # "created", "deleted", "existed", "skipped", "error"
    error: Optional[str]
    reason: Optional[str]
```

## Synchronization Logic

### Event Filtering

Events are processed only if they meet these criteria:

1. **Participant Count**: Must have 2 or more participants
2. **Event Status**: Must be "confirmed" (not cancelled or tentative)
3. **Event Transparency**: Must be "opaque" (busy) - "transparent" (free) events are ignored
4. **Account Match**: Must belong to a configured source calendar

### Busy Block Management

The system uses **time-based matching** for busy block management:

1. **Creation**: 
   - Calculate busy block time using source event time + configured offsets
   - Search for existing busy block with exact time match
   - If no exact match, check if existing busy blocks fully cover the required period
   - Skip all-day events when checking coverage (they don't prevent creation)
   - Create new busy block only if no match or coverage exists

2. **Deletion**:
   - When source event is cancelled, calculate expected busy block times
   - Search for busy blocks with exact time match
   - Delete found busy blocks

3. **Idempotent Operations**:
   - Multiple processing of same event won't create duplicates
   - System is resistant to manual editing of busy blocks
   - No fragile ID-based connections between source and busy events

### Sync Flow Processing

For each incoming event:

1. **Find Applicable Flows**: Identify sync flows that monitor the event's calendar
2. **Process Event**: For each applicable flow:
   - Check if event meets criteria
   - Handle cancelled events (delete busy blocks)
   - Handle active events (create busy blocks)
3. **Track Results**: Log processing results and update statistics

### Transparency (Busy/Free) Logic

The system respects Google Calendar's transparency setting for fine-grained control:

1. **Busy Events (opaque)**:
   - Create busy blocks in target calendars
   - Standard synchronization behavior
   - Default setting for new events

2. **Free Events (transparent)**:
   - Skip busy block creation
   - Existing busy blocks are deleted if event changes to free
   - Allows for "tentative" or "available" events that shouldn't block time

3. **Dynamic Updates**:
   - Real-time webhook updates handle transparency changes
   - Changing from busy to free deletes existing busy blocks
   - Changing from free to busy creates new busy blocks
   - Maintains consistency across all synchronized calendars

## Real-Time Synchronization

### Webhook System

The system uses Google Calendar push notifications for real-time sync:

1. **Subscription Management**:
   - Subscribe to calendar change notifications
   - Automatic renewal of subscriptions (24-hour expiry)
   - Graceful handling of subscription failures

2. **Webhook Processing**:
   - Validate webhook signatures from Google
   - Extract calendar and event information
   - Trigger sync engine processing
   - Handle various notification types ("sync", "exists", etc.)

3. **Security**:
   - Signature validation using Google's public certificates
   - API key authentication for webhook endpoints
   - Rate limiting and abuse protection

### Webhook Endpoints

```
POST /api/v1/webhooks/google-calendar
```

Receives Google Calendar push notifications and triggers event processing.

## Backup Synchronization

### Daily Polling

The system runs daily polling as a backup to webhooks:

1. **Schedule**: Configurable time (default: 6:00 AM UTC)
2. **Time Range**: Configurable range (default: current-2 days to current+14 days)
3. **Processing**: Uses same sync engine logic as webhooks
4. **Idempotent**: Safe to process same events multiple times

### Manual Sync

Manual synchronization can be triggered programmatically:

```python
from backend.services.google_calendar.polling_scheduler import PollingScheduler

scheduler = PollingScheduler(config, account_manager)
result = scheduler.run_manual_sync(days_back=1, days_forward=7)
```

## Error Handling and Reliability

### Retry Mechanisms

All Google Calendar API calls include retry logic:

- **Retry Strategy**: Exponential backoff (1s, 2s, 4s, 8s, 10s max)
- **Retry Attempts**: Up to 3 attempts per operation
- **Retry Conditions**: HttpError, ConnectionError, TimeoutError
- **Rate Limiting**: Automatic handling of Google API rate limits

### Error Types

```python
class GoogleCalendarError(Exception):
    """Base exception for Google Calendar API errors"""
    pass

class SyncEngineError(Exception):
    """Exception raised when sync engine operations fail"""
    pass

class WebhookValidationError(Exception):
    """Exception raised when webhook validation fails"""
    pass
```

### Logging

Comprehensive logging throughout the system:

- **INFO**: Successful operations, sync results, statistics
- **WARNING**: Non-critical issues, missing events, expired subscriptions
- **ERROR**: API errors, validation failures, sync failures
- **DEBUG**: Detailed processing information, webhook validation

## API Integration

### Google Calendar API Usage

The system uses the following Google Calendar API endpoints:

1. **Calendar List**: `GET /calendar/v3/users/me/calendarList`
2. **Events List**: `GET /calendar/v3/calendars/{calendarId}/events`
3. **Events Insert**: `POST /calendar/v3/calendars/{calendarId}/events`
4. **Events Delete**: `DELETE /calendar/v3/calendars/{calendarId}/events/{eventId}`
5. **Watch**: `POST /calendar/v3/calendars/{calendarId}/events/watch`
6. **Channels Stop**: `POST /calendar/v3/channels/stop`

### OAuth2 Flow

1. **Initial Setup**: Use `scripts/setup_google_oauth.py` to obtain refresh tokens
2. **Token Refresh**: Automatic refresh using stored refresh tokens
3. **Scope**: `https://www.googleapis.com/auth/calendar` (full calendar access)

## Performance and Scalability

### Efficiency Features

1. **Idempotent Operations**: No duplicate processing or creation
2. **Time-Based Matching**: Efficient busy block detection
3. **Batch Processing**: Daily polling processes multiple events efficiently
4. **Caching**: Account clients are cached for reuse
5. **Lazy Loading**: Clients created only when needed

### Monitoring

The system provides statistics and monitoring:

```python
class SyncEngineStats(BaseModel):
    events_processed: int
    busy_blocks_created: int
    busy_blocks_deleted: int
    errors: int
    accounts: int
    sync_flows: int
    last_updated: str
```

Access via: `sync_engine.get_stats()`

## Security Considerations

### OAuth2 Security

1. **Refresh Token Storage**: Secure storage in environment variables
2. **Token Rotation**: Automatic token refresh, manual token rotation
3. **Scope Limitation**: Only calendar access, no other Google services
4. **Account Isolation**: Each account has separate credentials

### Webhook Security

1. **Signature Validation**: Cryptographic validation of webhook signatures
2. **API Key Authentication**: Webhook endpoints protected by API keys
3. **Rate Limiting**: Protection against webhook abuse
4. **Input Validation**: Strict validation of webhook payloads

### Data Protection

1. **No Persistent Storage**: No calendar data stored locally
2. **Minimal Data Access**: Only necessary event information retrieved
3. **Secure Transmission**: All API calls use HTTPS
4. **Environment Variables**: Sensitive data in environment variables only

## Deployment

### Development Setup

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Configure Environment**: Set up `.env` file with credentials
3. **Run Setup**: `python scripts/setup_google_oauth.py`
4. **Test Configuration**: `python -m pytest tests/integration/test_calendar_access.py -m integration`
5. **Start Server**: `python run.py`

### Production Deployment

1. **Terraform Configuration**: Add variables to `terraform/terraform.tfvars`
2. **Deploy Infrastructure**: `cd terraform && terraform apply`
3. **Environment Variables**: Set production credentials in EC2 instance
4. **Monitor Logs**: Check application logs for sync operations
5. **Health Checks**: Use monitoring endpoints to verify system health

## Troubleshooting

### Common Issues

1. **OAuth2 Errors**:
   - Check client ID and secret
   - Verify refresh token validity
   - Ensure Calendar API is enabled
   - Check test user configuration

2. **Sync Issues**:
   - Verify calendar access permissions
   - Check sync flow configuration
   - Review event filtering criteria
   - Monitor webhook subscriptions

3. **Performance Issues**:
   - Check API rate limits
   - Review retry mechanisms
   - Monitor system resources
   - Optimize sync frequency

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG
```

### Health Checks

The system provides health check endpoints:

```
GET /api/v1/calendar/health
GET /api/v1/calendar/stats
```

## Future Enhancements

### Planned Features

1. **Web UI**: Configuration management interface
2. **Database Storage**: Persistent configuration and history
3. **Advanced Filtering**: Time-based, calendar-specific filters
4. **Notification System**: Email/SMS alerts for sync issues
5. **Metrics Dashboard**: Real-time sync monitoring

### Extension Points

1. **Custom Event Processing**: Pluggable event processors
2. **Multiple Sync Engines**: Support for different sync strategies
3. **Integration APIs**: RESTful APIs for external integrations
4. **Webhook Extensions**: Custom webhook handlers

## API Reference

### Configuration Loading

```python
from backend.services.google_calendar.config_loader import load_multi_account_config

config = load_multi_account_config()
```

### Account Management

```python
from backend.services.google_calendar.account_manager import AccountManager

account_manager = AccountManager(config)
client = account_manager.get_client(account_id)
```

### Sync Engine

```python
from backend.services.google_calendar.sync_engine import CalendarSyncEngine

sync_engine = CalendarSyncEngine(config, account_manager)
results = sync_engine.process_event(event, sync_type="webhook")
```

### Webhook Handler

```python
from backend.services.google_calendar.webhook_handler import WebhookHandler

webhook_handler = WebhookHandler(config, account_manager)
result = webhook_handler.handle_webhook(headers, body)
```

This documentation provides a comprehensive overview of the Google Calendar synchronization system. For setup instructions, see [Google Calendar Setup Guide](google_calendar_setup.md). 