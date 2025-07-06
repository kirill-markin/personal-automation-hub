# Google Calendar Sync Troubleshooting Guide

## Common Issues and Solutions

### OAuth2 Authentication Problems

#### Issue: "This app isn't verified" Error
**Symptoms**: Browser shows "This app isn't verified" warning during OAuth setup

**Solutions**:
1. **Click "Advanced" → "Go to [App Name] (unsafe)"** - This is safe for personal use
2. **Add Test Users**: In Google Cloud Console:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Add your email to "Test users" section
   - Test users can bypass verification warnings

#### Issue: "Access blocked" Error
**Symptoms**: OAuth flow fails with "Access blocked" message

**Solutions**:
1. **Check Test Users**: Ensure you're logging in with an account added as a test user
2. **Verify Consent Screen**: Ensure OAuth consent screen is properly configured
3. **Check Scopes**: Verify calendar scope is added to consent screen
4. **Account Mismatch**: Make sure you're using the correct Google account

#### Issue: "Invalid Client" Error
**Symptoms**: OAuth setup fails with "invalid_client" error

**Solutions**:
1. **Verify Credentials**: Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
2. **Application Type**: Ensure OAuth2 credentials are set to "Desktop application"
3. **Re-create Credentials**: Delete and recreate OAuth2 credentials in Google Cloud Console
4. **Project Status**: Ensure Google Cloud project is active and billing is enabled

#### Issue: "Token Refresh Failed" Error
**Symptoms**: Application logs show "Failed to refresh OAuth2 token"

**Solutions**:
1. **Re-run OAuth Setup**: Get new refresh token using `python scripts/setup_google_oauth.py`
2. **Check Token Expiry**: Refresh tokens can expire if not used for 6 months
3. **Verify Credentials**: Ensure client ID and secret haven't changed
4. **Account Access**: Verify the Google account still has access to required calendars

### Calendar Access Issues

#### Issue: "Calendar Not Found" Error
**Symptoms**: Error when accessing specific calendar IDs

**Solutions**:
1. **List Calendars**: Run `python scripts/list_google_calendars.py --account-id N` to see available calendars
2. **Check Permissions**: Ensure you have read/write access to the calendar
3. **Shared Calendars**: For shared calendars, you need "Make changes to events" permission
4. **Calendar ID Format**: Verify calendar ID format (email format vs. generated ID)

#### Issue: "Permission Denied" Error
**Symptoms**: API calls fail with 403 permission denied

**Solutions**:
1. **APIs Enabled**: Ensure Google Calendar API and Gmail API are enabled in Google Cloud Console
2. **Scope Verification**: Verify you granted both calendar and Gmail access during OAuth setup
3. **Calendar Permissions**: Check permissions on the specific calendar
4. **Account Verification**: Ensure you're using the correct Google account
5. **OAuth Scopes**: If you previously set up OAuth with only calendar scopes, re-run the setup script to get Gmail permissions

### Sync Flow Configuration Issues

#### Issue: "No Sync Flows Found" Error
**Symptoms**: Application starts but no sync flows are configured

**Solutions**:
1. **Environment Variables**: Check `.env` file for `SYNC_FLOW_N_*` variables
2. **Numbering**: Ensure sync flows start from 1 and increment sequentially
3. **Required Fields**: Verify all required fields are set:
   - `SYNC_FLOW_N_NAME`
   - `SYNC_FLOW_N_SOURCE_ACCOUNT_ID`
   - `SYNC_FLOW_N_SOURCE_CALENDAR_ID`
   - `SYNC_FLOW_N_TARGET_ACCOUNT_ID`
   - `SYNC_FLOW_N_TARGET_CALENDAR_ID`
   - `SYNC_FLOW_N_START_OFFSET`
   - `SYNC_FLOW_N_END_OFFSET`

#### Issue: "Invalid Account ID" Error
**Symptoms**: Sync flow references non-existent account

**Solutions**:
1. **Account Configuration**: Ensure `GOOGLE_ACCOUNT_N_*` variables exist for referenced account IDs
2. **Account ID Matching**: Verify account IDs in sync flows match configured accounts
3. **Sequential Numbering**: Ensure account IDs start from 1 and increment sequentially

### Webhook Issues

#### Issue: "Webhook Not Receiving Events" Error
**Symptoms**: Real-time sync not working, only daily polling works

**Solutions**:
1. **Webhook URL**: Verify webhook URL is accessible from internet
2. **Firewall/NAT**: Check firewall rules and NAT configuration
3. **SSL Certificate**: Ensure webhook URL uses valid SSL certificate
4. **Google Requirements**: Webhook URL must be HTTPS with valid certificate
5. **Subscription Status**: Check if webhook subscriptions are active

#### Issue: "Webhook Signature Validation Failed" Error
**Symptoms**: Webhooks received but signature validation fails

**Solutions**:
1. **Time Sync**: Ensure server time is synchronized (webhook signatures are time-sensitive)
2. **Body Modification**: Verify webhook body isn't modified by proxy/load balancer
3. **Header Preservation**: Ensure all Google headers are preserved
4. **API Key**: Verify webhook API key is correct

### Sync Engine Issues

#### Issue: "Events Not Syncing" Error
**Symptoms**: Events created but busy blocks not appearing

**Solutions**:
1. **Participant Count**: Verify events have 2+ participants (single-person events are ignored)
2. **Event Status**: Ensure events are "confirmed" (not tentative or cancelled)
3. **Calendar Matching**: Verify source calendar ID matches sync flow configuration
4. **Permissions**: Check write permissions on target calendar
5. **Logs**: Check application logs for detailed error messages

#### Issue: "Duplicate Busy Blocks" Error
**Symptoms**: Multiple busy blocks created for same event

**Solutions**:
1. **Time Matching**: This shouldn't happen due to time-based matching
2. **Clock Drift**: Ensure server clock is accurate
3. **Configuration**: Check for duplicate sync flows
4. **Manual Cleanup**: Remove duplicate busy blocks manually

### Performance Issues

#### Issue: "API Rate Limit Exceeded" Error
**Symptoms**: Sync operations failing with rate limit errors

**Solutions**:
1. **Retry Logic**: System should handle rate limits automatically with exponential backoff
2. **Sync Frequency**: Reduce sync frequency if hitting limits consistently
3. **Multiple Accounts**: Consider splitting sync across multiple Google accounts
4. **Quota Limits**: Check Google Cloud Console for API quotas

#### Issue: "Slow Sync Performance" Error
**Symptoms**: Daily sync taking too long to complete

**Solutions**:
1. **Date Range**: Reduce sync date range (default: 2 days back, 14 days forward)
2. **Event Volume**: Consider filtering events or reducing sync flows
3. **Parallel Processing**: System already processes multiple calendars in parallel
4. **Resource Allocation**: Ensure sufficient CPU/memory for the application

### Production Deployment Issues

#### Issue: "Environment Variables Not Set" Error
**Symptoms**: Application fails to start in production

**Solutions**:
1. **Terraform Variables**: Ensure all variables are set in `terraform/terraform.tfvars`
2. **EC2 Instance**: Verify environment variables are passed to EC2 instance
3. **Docker Environment**: Check Docker environment variable configuration
4. **Variable Names**: Ensure variable names match exactly (case-sensitive)

#### Issue: "Webhook URL Not Accessible" Error
**Symptoms**: Google cannot reach webhook URL

**Solutions**:
1. **Security Groups**: Configure AWS security groups to allow HTTPS traffic
2. **Load Balancer**: Ensure load balancer is configured for HTTPS
3. **DNS Resolution**: Verify domain name resolves to correct IP
4. **SSL Certificate**: Ensure SSL certificate is valid and not expired

## Debugging Steps

### 1. Check Environment Configuration

```bash
# Verify environment variables are loaded
python -c "
from backend.services.google_calendar.config_loader import load_multi_account_config
config = load_multi_account_config()
print(f'Accounts: {len(config.accounts)}')
print(f'Sync Flows: {len(config.sync_flows)}')
for account in config.accounts:
    print(f'Account {account.account_id}: {account.email}')
for flow in config.sync_flows:
    print(f'Flow: {flow.name} ({flow.source_account_id} -> {flow.target_account_id})')
"
```

### 2. Test Calendar Access

```bash
# Test calendar access for all accounts
python -m pytest tests/integration/test_calendar_access.py -m integration -v

# Test specific account
python -c "
from backend.services.google_calendar.config_loader import load_multi_account_config
from backend.services.google_calendar.account_manager import AccountManager

config = load_multi_account_config()
account_manager = AccountManager(config)

# Test account 1
try:
    client = account_manager.get_client(1)
    calendars = client.list_calendars()
    print(f'Account 1: {len(calendars)} calendars accessible')
    for cal in calendars[:5]:  # Show first 5
        print(f'  {cal["id"]}: {cal["summary"]}')
except Exception as e:
    print(f'Account 1 error: {e}')
"
```

### 3. Test Sync Engine

```bash
# Run manual sync to test sync engine
python -c "
from backend.services.google_calendar.config_loader import load_multi_account_config
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.polling_scheduler import PollingScheduler
from datetime import datetime, timedelta

config = load_multi_account_config()
account_manager = AccountManager(config)
scheduler = PollingScheduler(config, account_manager)

# Run sync for past 1 day, future 3 days
result = scheduler.run_manual_sync(days_back=1, days_forward=3)
print(f'Sync result: {result}')
"
```

### 4. Check Webhook Subscriptions

```bash
# Check webhook subscriptions status
python -c "
from backend.services.google_calendar.config_loader import load_multi_account_config
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.webhook_handler import WebhookHandler

config = load_multi_account_config()
account_manager = AccountManager(config)
webhook_handler = WebhookHandler(config, account_manager)

# This would typically be done during application startup
print('Webhook handler initialized')
print(f'Monitoring {len(config.sync_flows)} sync flows')
"
```

### 5. Enable Debug Logging

Add to your `.env` file:
```bash
LOG_LEVEL=DEBUG
```

Or set environment variable:
```bash
export LOG_LEVEL=DEBUG
python run.py
```

### 6. Check Application Health

```bash
# Check if server is running
curl -X GET "http://localhost:8000/health"

# Check calendar sync health (if endpoint exists)
curl -X GET "http://localhost:8000/api/v1/calendar/health"
```

## Log Analysis

### Important Log Messages

#### Success Messages
```
INFO: Initialized sync engine with N accounts and M sync flows
INFO: Created busy block 'Busy' for event 'Meeting Title' in flow FlowName
INFO: Processed N events from calendar calendar_id
INFO: Daily sync completed successfully
```

#### Warning Messages
```
WARNING: Event event_id not found in calendar calendar_id
WARNING: Webhook subscription channel_id not found or already expired
WARNING: No applicable sync flows for event event_id
```

#### Error Messages
```
ERROR: Failed to refresh OAuth2 token: error_details
ERROR: HTTP error creating event in calendar calendar_id: error_details
ERROR: Error processing event event_id for flow flow_name: error_details
```

### Log Locations

- **Development**: Console output when running `python run.py`
- **Production**: EC2 instance logs, accessible via SSH or CloudWatch
- **Docker**: Container logs via `docker logs container_name`

## Getting Help

### Before Reporting Issues

1. **Check This Guide**: Review all relevant sections
2. **Check Logs**: Enable debug logging and review error messages
3. **Test Configuration**: Run the debugging steps above
4. **Verify Setup**: Ensure all setup steps were completed correctly

### Information to Include

When reporting issues, include:

1. **Environment**: Development vs. production
2. **Configuration**: Sanitized version of your `.env` file (remove sensitive data)
3. **Error Messages**: Complete error messages from logs
4. **Steps to Reproduce**: Detailed steps to reproduce the issue
5. **Expected vs. Actual**: What you expected vs. what happened
6. **Debugging Output**: Results from debugging steps above

### Quick Health Check

Run this comprehensive health check:

```bash
#!/bin/bash
echo "=== Google Calendar Sync Health Check ==="

echo "1. Environment Variables Check:"
python -c "
import os
required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
for var in required_vars:
    if os.getenv(var):
        print(f'  ✓ {var} is set')
    else:
        print(f'  ✗ {var} is missing')
"

echo "2. Configuration Check:"
python -c "
try:
    from backend.services.google_calendar.config_loader import load_multi_account_config
    config = load_multi_account_config()
    print(f'  ✓ {len(config.accounts)} accounts configured')
    print(f'  ✓ {len(config.sync_flows)} sync flows configured')
except Exception as e:
    print(f'  ✗ Configuration error: {e}')
"

echo "3. Calendar Access Check:"
python -c "
try:
    from backend.services.google_calendar.config_loader import load_multi_account_config
    from backend.services.google_calendar.account_manager import AccountManager
    
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    
    for account in config.accounts:
        try:
            client = account_manager.get_client(account.account_id)
            calendars = client.list_calendars()
            print(f'  ✓ Account {account.account_id} ({account.email}): {len(calendars)} calendars')
        except Exception as e:
            print(f'  ✗ Account {account.account_id} error: {e}')
except Exception as e:
    print(f'  ✗ Account manager error: {e}')
"

echo "4. Sync Engine Check:"
python -c "
try:
    from backend.services.google_calendar.config_loader import load_multi_account_config
    from backend.services.google_calendar.account_manager import AccountManager
    from backend.services.google_calendar.sync_engine import CalendarSyncEngine
    
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    
    stats = sync_engine.get_stats()
    print(f'  ✓ Sync engine initialized')
    print(f'  ✓ {stats.accounts} accounts, {stats.sync_flows} sync flows')
except Exception as e:
    print(f'  ✗ Sync engine error: {e}')
"

echo "=== Health Check Complete ==="
```

Save this as `health_check.sh`, make it executable (`chmod +x health_check.sh`), and run it to diagnose issues. 