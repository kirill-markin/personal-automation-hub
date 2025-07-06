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
GOOGLE_ACCOUNT_1_NAME=your-personal-account-name
GOOGLE_ACCOUNT_1_CLIENT_ID=your-personal-client-id
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your-personal-client-secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=your-personal-refresh-token

# Google Calendar Account 2 (Work)
GOOGLE_ACCOUNT_2_NAME=your-work-account-name
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
```

### Excluding from Automated Tests

These tests are marked with `@pytest.mark.integration` and should be excluded from regular test runs:

```bash
# Run only unit tests (excludes integration)
pytest -m "not integration"

# Run only integration tests
pytest -m "integration"
```

## Security Notes

- **Never commit real credentials to version control**
- **Always use `.env` file for local development**
- **Keep your refresh tokens secure and rotate them regularly**
- **Use separate test accounts when possible**

## Test Files

- `test_calendar_access.py` - Comprehensive testing of calendar connections and sync flows
- `test_list_calendars.py` - Utility for listing and exploring available calendars 