# Integration Tests

**⚠️ WARNING: These tests require real API credentials and should NOT be run automatically in CI/CD pipelines.**

## Overview

This directory contains integration tests that:
- Test real Google Calendar API connections
- Require valid OAuth2 credentials and refresh tokens
- Make actual API calls to Google services
- Should be run manually by developers only

## Required Environment Variables

These tests require a complete `.env` file with real credentials:

```bash
# Google Calendar Account 1 (Personal)
GOOGLE_ACCOUNT_1_EMAIL=your-personal-account@gmail.com
GOOGLE_ACCOUNT_1_CLIENT_ID=your-personal-client-id
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your-personal-client-secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=your-personal-refresh-token

# Google Calendar Account 2 (Work)
GOOGLE_ACCOUNT_2_EMAIL=your-work-account@company.com
GOOGLE_ACCOUNT_2_CLIENT_ID=your-work-client-id
GOOGLE_ACCOUNT_2_CLIENT_SECRET=your-work-client-secret
GOOGLE_ACCOUNT_2_REFRESH_TOKEN=your-work-refresh-token

# Sync Flow Configuration
SYNC_FLOW_1_NAME=Work to Personal Busy
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=2
SYNC_FLOW_1_SOURCE_CALENDAR_ID=your-work-calendar-id
SYNC_FLOW_1_TARGET_ACCOUNT_ID=1
SYNC_FLOW_1_TARGET_CALENDAR_ID=your-personal-busy-calendar-id
SYNC_FLOW_1_START_OFFSET=-15
SYNC_FLOW_1_END_OFFSET=15

# Polling Settings
DAILY_SYNC_HOUR=6
DAILY_SYNC_TIMEZONE=UTC
```

## Running Tests

### Manual Execution

```bash
# Test all accounts and sync flows
python -m pytest tests/integration/test_calendar_access.py -v

# Test specific account only
python tests/integration/test_calendar_access.py --account-id 1

# List all calendars
python tests/integration/test_list_calendars.py

# List calendars for specific account
python tests/integration/test_list_calendars.py --account-id 2

# Get copy-paste format for .env
python tests/integration/test_list_calendars.py --copy-paste

# Test sync engine functionality
python -m pytest tests/integration/test_sync_engine.py -v

# Test webhook handler functionality
python -m pytest tests/integration/test_webhook_handler.py -v

# Test daily polling system functionality
python -m pytest tests/integration/test_daily_polling.py -v

# Test specific sync engine features
python tests/integration/test_sync_engine.py --test-busy-blocks

# Test specific webhook handler features
python tests/integration/test_webhook_handler.py --test-subscriptions

# Test specific daily polling features
python tests/integration/test_daily_polling.py --test-manual-sync
python tests/integration/test_daily_polling.py --test-scheduler
```

### Excluding from Automated Tests

These tests are marked with `@pytest.mark.integration` and should be excluded from regular test runs:

```bash
# Run only unit tests (excludes integration)
pytest -m "not integration"

# Run only integration tests
pytest -m "integration"

# Run all Phase 2 integration tests
pytest -m "integration" tests/integration/test_sync_engine.py tests/integration/test_webhook_handler.py tests/integration/test_daily_polling.py
```

## Security Notes

- **Never commit real credentials to version control**
- **Always use `.env` file for local development**
- **Keep your refresh tokens secure and rotate them regularly**
- **Use separate test accounts when possible**
- **Test data is automatically cleaned up after each test**

## Test Files

### Phase 1 Tests (Account Management & Configuration)
- `test_calendar_access.py` - Comprehensive testing of calendar connections and sync flows
- `test_list_calendars.py` - Utility for listing and exploring available calendars

### Phase 2 Tests (Core Sync Functionality)
- `test_sync_engine.py` - End-to-end sync engine testing with real calendar data
- `test_webhook_handler.py` - Webhook processing and subscription management testing
- `test_daily_polling.py` - Daily polling system and API endpoint testing

## Phase 2 Integration Test Coverage

### Sync Engine Tests (`test_sync_engine.py`)

**Event Processing Tests:**
- `test_process_event_with_multiple_participants()` - Test busy block creation for multi-participant events
- `test_process_event_with_single_participant()` - Test event skipping for single-participant events
- `test_event_deletion_removes_busy_block()` - Test busy block deletion for cancelled events
- `test_idempotent_busy_block_creation()` - Test that duplicate processing doesn't create duplicates

**Calendar Sync Tests:**
- `test_sync_calendar_events()` - Test syncing events from a calendar within date range
- `test_sync_all_source_calendars()` - Test syncing all configured source calendars
- `test_multi_flow_processing()` - Test processing events through multiple sync flows

**Initialization Tests:**
- `test_sync_engine_initialization()` - Test sync engine setup and configuration

**Helper Functions:**
- `SyncEngineTestHelper` - Test utilities for creating/deleting test events and busy blocks
- Automatic cleanup of test data after each test

### Webhook Handler Tests (`test_webhook_handler.py`)

**Validation Tests:**
- `test_webhook_data_validation()` - Test webhook payload validation
- `test_webhook_header_validation()` - Test Google Calendar webhook header validation

**Processing Tests:**
- `test_webhook_processing_sync_state()` - Test webhook processing for sync notifications
- `test_webhook_processing_exists_state()` - Test webhook processing for exists notifications
- `test_webhook_processing_invalid_data()` - Test error handling for invalid webhook data
- `test_webhook_processing_non_monitored_calendar()` - Test handling of non-monitored calendars

**Subscription Management Tests:**
- `test_webhook_subscription_creation()` - Test creating webhook subscriptions
- `test_webhook_subscription_deletion()` - Test deleting webhook subscriptions

**Monitoring Tests:**
- `test_get_monitored_calendars()` - Test retrieving list of monitored calendars
- `test_find_account_for_calendar()` - Test calendar-to-account mapping

**Initialization Tests:**
- `test_webhook_handler_initialization()` - Test webhook handler setup and configuration

**Helper Functions:**
- `WebhookTestHelper` - Test utilities for creating mock webhook data and headers
- Automatic cleanup of test webhook subscriptions

### Daily Polling Tests (`test_daily_polling.py`)

**API Endpoint Tests:**
- `test_health_check_endpoint()` - Test health check endpoint functionality
- `test_sync_status_endpoint()` - Test sync status monitoring endpoint
- `test_accounts_endpoint()` - Test accounts listing endpoint
- `test_sync_flows_endpoint()` - Test sync flows configuration endpoint
- `test_calendar_listing_endpoint()` - Test calendar listing for each account

**Manual Sync Tests:**
- `test_manual_sync_operations()` - Test manual sync with different parameters (days_back/days_forward)

**Scheduler Tests:**
- `test_force_scheduler_run()` - Test force run scheduler functionality

**Workflow Tests:**
- `test_complete_polling_workflow()` - Test complete end-to-end polling workflow

**Helper Functions:**
- `DailyPollingTestHelper` - Test utilities for making API requests and waiting for server
- Server availability checking and API request management

## Running Complete Integration Test Suite

```bash
# Run all Phase 1 and Phase 2 integration tests
pytest -m "integration" tests/integration/ -v

# Run specific phase tests
pytest -m "integration" tests/integration/test_sync_engine.py -v
pytest -m "integration" tests/integration/test_webhook_handler.py -v
pytest -m "integration" tests/integration/test_daily_polling.py -v

# Run tests with detailed output
pytest -m "integration" tests/integration/ -v -s

# Run specific test function
pytest -m "integration" tests/integration/test_sync_engine.py::test_process_event_with_multiple_participants -v
pytest -m "integration" tests/integration/test_daily_polling.py::test_manual_sync_operations -v
```

## Test Data Management

**Automatic Cleanup:**
- All tests automatically clean up test data after completion
- Test events are tracked and deleted
- Test busy blocks are removed
- Webhook subscriptions are cleaned up

**Test Event Naming:**
- Test events use random prefixes to avoid conflicts
- Example: `SyncTest_A8bCdEfG` for sync engine tests
- All test events include descriptive titles and metadata

**Safety Measures:**
- Tests only modify calendars specified in sync flows
- Real user events are never modified or deleted
- Test data is clearly marked with test prefixes

## Troubleshooting

**Common Issues:**

1. **Missing Environment Variables:**
   - Ensure `.env` file contains all required variables
   - Check that refresh tokens are valid and not expired

2. **Calendar Access Errors:**
   - Verify calendar IDs are correct
   - Check that accounts have proper permissions

3. **Webhook Subscription Errors:**
   - Webhook subscriptions may fail in test environments
   - This is expected behavior and doesn't indicate test failure

4. **Rate Limiting:**
   - Google Calendar API has rate limits
   - Tests include appropriate delays and retry logic

**Getting Help:**
- Check test output for specific error messages
- Verify configuration using `test_calendar_access.py`
- Use `test_list_calendars.py` to verify calendar access 