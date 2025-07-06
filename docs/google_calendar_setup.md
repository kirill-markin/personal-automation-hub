# Google Calendar Setup Guide

## Overview

This guide walks you through setting up Google Calendar synchronization in the Personal Automation Hub. The system automatically creates "Busy" blocks in target calendars when events with 2+ participants are created in source calendars.

## Prerequisites

- Python 3.11+ installed
- Personal Automation Hub repository cloned
- Google account(s) with calendar access

## Step 1: Google Cloud Project Setup

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" or select an existing project
3. Give your project a name (e.g., "Personal Calendar Sync")
4. Click "Create"

### 1.2 Enable Google Calendar API

1. In the Google Cloud Console, navigate to "APIs & Services" → "Library"
2. Search for "Google Calendar API"
3. Click on "Google Calendar API" and click "Enable"

### 1.3 Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Google Workspace)
   - Fill in required fields (App name, User support email, Developer contact)
   - Add your email to "Test users" if using External type
4. For OAuth 2.0 Client ID:
   - Application type: "Desktop application"
   - Name: "Personal Calendar Sync"
   - Click "Create"
5. Download the credentials JSON file or copy the Client ID and Client Secret

## Step 2: Environment Configuration

### 2.1 Copy Environment Template

```bash
cp .env.example .env
```

### 2.2 Add Google OAuth2 Credentials

Edit the `.env` file and add your Google OAuth2 credentials:

```bash
# Shared Google OAuth2 Application (one app for all accounts)
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

## Step 3: Obtain Refresh Tokens

You need to obtain a refresh token for each Google account you want to sync.

### 3.1 Run OAuth2 Setup Script

For each Google account, run the setup script:

```bash
# For first account
python scripts/setup_google_oauth.py --account-id 1

# For second account  
python scripts/setup_google_oauth.py --account-id 2

# For additional accounts
python scripts/setup_google_oauth.py --account-id 3
```

### 3.2 OAuth2 Flow

1. The script will open your browser to Google's OAuth2 consent screen
2. Select the Google account you want to authorize
3. Grant permission for calendar access
4. The script will display your refresh token
5. Copy the refresh token to your `.env` file

### 3.3 Add Account Configuration

Add each account's configuration to your `.env` file:

```bash
# Google Account 1: Personal Gmail
GOOGLE_ACCOUNT_1_EMAIL=personal@gmail.com
GOOGLE_ACCOUNT_1_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your_client_secret_here
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=1//04_refresh_token_for_account_1

# Google Account 2: Work Account
GOOGLE_ACCOUNT_2_EMAIL=work@company.com
GOOGLE_ACCOUNT_2_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_ACCOUNT_2_CLIENT_SECRET=your_client_secret_here
GOOGLE_ACCOUNT_2_REFRESH_TOKEN=1//04_refresh_token_for_account_2
```

## Step 4: Calendar Configuration

### 4.1 List Available Calendars

Use the script to list calendars for each account:

```bash
# List calendars for account 1
python scripts/list_google_calendars.py --account-id 1

# List calendars for account 2
python scripts/list_google_calendars.py --account-id 2
```

### 4.2 Configure Sync Flows

Add sync flow configuration to your `.env` file. Each sync flow represents one source calendar syncing to one target calendar:

```bash
# Polling schedule settings
DAILY_SYNC_HOUR=6  # Run daily polling at 6:00 AM
DAILY_SYNC_TIMEZONE=UTC

# Sync Flow 1: Work calendar → Personal busy calendar
SYNC_FLOW_1_NAME=Work to Personal Busy
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=2
SYNC_FLOW_1_SOURCE_CALENDAR_ID=work.email@company.com
SYNC_FLOW_1_TARGET_ACCOUNT_ID=1
SYNC_FLOW_1_TARGET_CALENDAR_ID=calendar_id_here@group.calendar.google.com
SYNC_FLOW_1_START_OFFSET=-15  # Busy block starts 15 minutes before
SYNC_FLOW_1_END_OFFSET=15     # Busy block ends 15 minutes after

# Sync Flow 2: Personal calendar → Work calendar
SYNC_FLOW_2_NAME=Personal to Work
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_2_SOURCE_CALENDAR_ID=personal.email@gmail.com
SYNC_FLOW_2_TARGET_ACCOUNT_ID=2
SYNC_FLOW_2_TARGET_CALENDAR_ID=work.email@company.com
SYNC_FLOW_2_START_OFFSET=-15
SYNC_FLOW_2_END_OFFSET=15
```

## Step 5: Testing

### 5.1 Test Calendar Access

```bash
# Test calendar access for all accounts
python -m pytest tests/integration/test_calendar_access.py -m integration -v
```

### 5.2 Test Sync Engine

```bash
# Test sync engine with sample data
python -m pytest tests/integration/test_sync_engine.py -m integration -v
```

### 5.3 Manual Testing

Start the server and test manually:

```bash
# Start the server
python run.py

# In another terminal, test sync
python -c "
from backend.services.google_calendar.config_loader import load_multi_account_config
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.polling_scheduler import PollingScheduler
from datetime import datetime, timedelta

config = load_multi_account_config()
account_manager = AccountManager(config)
scheduler = PollingScheduler(config, account_manager)

# Run manual sync
start_date = datetime.now() - timedelta(days=1)
end_date = datetime.now() + timedelta(days=7)
result = scheduler.run_manual_sync(days_back=1, days_forward=7)
print(f'Sync completed: {result}')
"
```

## Step 6: Production Deployment

### 6.1 Update Terraform Configuration

Add your environment variables to `terraform/terraform.tfvars`:

```hcl
# Google Calendar API credentials
google_client_id = "your_client_id_here.apps.googleusercontent.com"
google_client_secret = "your_client_secret_here"

# Account configurations
google_account_1_email = "personal@gmail.com"
google_account_1_client_id = "your_client_id_here.apps.googleusercontent.com"
google_account_1_client_secret = "your_client_secret_here"
google_account_1_refresh_token = "1//04_refresh_token_for_account_1"

google_account_2_email = "work@company.com"
google_account_2_client_id = "your_client_id_here.apps.googleusercontent.com"
google_account_2_client_secret = "your_client_secret_here"
google_account_2_refresh_token = "1//04_refresh_token_for_account_2"

# Sync flows
daily_sync_hour = 6
daily_sync_timezone = "UTC"

sync_flow_1_name = "Work to Personal Busy"
sync_flow_1_source_account_id = 2
sync_flow_1_source_calendar_id = "work.email@company.com"
sync_flow_1_target_account_id = 1
sync_flow_1_target_calendar_id = "calendar_id_here@group.calendar.google.com"
sync_flow_1_start_offset = -15
sync_flow_1_end_offset = 15

sync_flow_2_name = "Personal to Work"
sync_flow_2_source_account_id = 1
sync_flow_2_source_calendar_id = "personal.email@gmail.com"
sync_flow_2_target_account_id = 2
sync_flow_2_target_calendar_id = "work.email@company.com"
sync_flow_2_start_offset = -15
sync_flow_2_end_offset = 15
```

### 6.2 Deploy to Production

```bash
cd terraform
terraform apply
```

## Security Notes

1. **Never commit `.env` file** - it contains sensitive OAuth2 refresh tokens
2. **Keep refresh tokens secure** - they provide access to your calendar data
3. **Use strong credentials** - ensure your Google account has 2FA enabled
4. **Rotate tokens periodically** - regenerate refresh tokens if compromised
5. **Monitor access logs** - check Google Cloud Console for unusual API activity

## Common Issues

See [Troubleshooting Guide](troubleshooting.md) for solutions to common problems.

## Next Steps

- [Configuration Examples](configuration_examples.md) - Common sync scenarios
- [API Documentation](calendar_sync.md) - Technical details
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions 