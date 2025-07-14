# Google Calendar Sync Configuration Examples

This document provides practical configuration examples for common Google Calendar synchronization scenarios.

## Basic Configuration Template

```bash
# Shared OAuth2 Application
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# Polling Schedule
SYNC_INTERVAL_MINUTES=60  # Hourly sync

# Account and sync flow configurations follow...
```

## Scenario 1: Work-Life Balance (2 Accounts)

**Use Case**: Prevent double-booking between work and personal calendars

### Configuration

```bash
# Google Account 1: Personal Gmail
GOOGLE_ACCOUNT_1_EMAIL=personal@gmail.com
GOOGLE_ACCOUNT_1_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=1//04_personal_refresh_token

# Google Account 2: Work Account
GOOGLE_ACCOUNT_2_EMAIL=work@company.com
GOOGLE_ACCOUNT_2_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_2_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_2_REFRESH_TOKEN=1//04_work_refresh_token

# Sync Flow 1: Work meetings → Personal calendar (as busy blocks)
SYNC_FLOW_1_NAME=Work to Personal
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=2
SYNC_FLOW_1_SOURCE_CALENDAR_ID=work.email@company.com
SYNC_FLOW_1_TARGET_ACCOUNT_ID=1
SYNC_FLOW_1_TARGET_CALENDAR_ID=personal.email@gmail.com
SYNC_FLOW_1_START_OFFSET=-15  # 15 minutes before
SYNC_FLOW_1_END_OFFSET=15     # 15 minutes after

# Sync Flow 2: Personal events → Work calendar (as busy blocks)
SYNC_FLOW_2_NAME=Personal to Work
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_2_SOURCE_CALENDAR_ID=personal.email@gmail.com
SYNC_FLOW_2_TARGET_ACCOUNT_ID=2
SYNC_FLOW_2_TARGET_CALENDAR_ID=work.email@company.com
SYNC_FLOW_2_START_OFFSET=-15
SYNC_FLOW_2_END_OFFSET=15
```

### Result
- Work meetings create "Busy" blocks in personal calendar
- Personal events create "Busy" blocks in work calendar
- Both calendars show availability conflicts
- 15-minute buffer prevents back-to-back scheduling

## Scenario 2: Multiple Calendar Views (1 Account)

**Use Case**: Sync from main calendar to multiple specialized calendars

### Configuration

```bash
# Google Account 1: Single account with multiple calendars
GOOGLE_ACCOUNT_1_EMAIL=main@gmail.com
GOOGLE_ACCOUNT_1_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=1//04_main_refresh_token

# Sync Flow 1: Main calendar → Busy calendar (for sharing)
SYNC_FLOW_1_NAME=Main to Busy
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_1_SOURCE_CALENDAR_ID=main.email@gmail.com
SYNC_FLOW_1_TARGET_ACCOUNT_ID=1
SYNC_FLOW_1_TARGET_CALENDAR_ID=busy.calendar.id@group.calendar.google.com
SYNC_FLOW_1_START_OFFSET=-10
SYNC_FLOW_1_END_OFFSET=10

# Sync Flow 2: Main calendar → Public calendar (different timing)
SYNC_FLOW_2_NAME=Main to Public
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_2_SOURCE_CALENDAR_ID=main.email@gmail.com
SYNC_FLOW_2_TARGET_ACCOUNT_ID=1
SYNC_FLOW_2_TARGET_CALENDAR_ID=public.calendar.id@group.calendar.google.com
SYNC_FLOW_2_START_OFFSET=-5
SYNC_FLOW_2_END_OFFSET=5
```

### Result
- Main calendar events sync to multiple target calendars
- Different timing offsets for different purposes
- Busy calendar has 20-minute buffer (10 before + 10 after)
- Public calendar has 10-minute buffer (5 before + 5 after)

## Scenario 3: Team Coordination (3 Accounts)

**Use Case**: Coordinate calendars across team members

### Configuration

```bash
# Google Account 1: Team Lead
GOOGLE_ACCOUNT_1_EMAIL=teamlead@company.com
GOOGLE_ACCOUNT_1_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=1//04_lead_refresh_token

# Google Account 2: Team Member 1
GOOGLE_ACCOUNT_2_EMAIL=member1@company.com
GOOGLE_ACCOUNT_2_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_2_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_2_REFRESH_TOKEN=1//04_member1_refresh_token

# Google Account 3: Team Member 2
GOOGLE_ACCOUNT_3_EMAIL=member2@company.com
GOOGLE_ACCOUNT_3_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_3_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_3_REFRESH_TOKEN=1//04_member2_refresh_token

# Sync Flow 1: Team Lead → Member 1 busy calendar
SYNC_FLOW_1_NAME=Lead to Member 1
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_1_SOURCE_CALENDAR_ID=lead@company.com
SYNC_FLOW_1_TARGET_ACCOUNT_ID=2
SYNC_FLOW_1_TARGET_CALENDAR_ID=member1.busy@company.com
SYNC_FLOW_1_START_OFFSET=-20
SYNC_FLOW_1_END_OFFSET=20

# Sync Flow 2: Team Lead → Member 2 busy calendar
SYNC_FLOW_2_NAME=Lead to Member 2
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_2_SOURCE_CALENDAR_ID=lead@company.com
SYNC_FLOW_2_TARGET_ACCOUNT_ID=3
SYNC_FLOW_2_TARGET_CALENDAR_ID=member2.busy@company.com
SYNC_FLOW_2_START_OFFSET=-20
SYNC_FLOW_2_END_OFFSET=20

# Sync Flow 3: Member 1 → Team Lead busy calendar
SYNC_FLOW_3_NAME=Member 1 to Lead
SYNC_FLOW_3_SOURCE_ACCOUNT_ID=2
SYNC_FLOW_3_SOURCE_CALENDAR_ID=member1@company.com
SYNC_FLOW_3_TARGET_ACCOUNT_ID=1
SYNC_FLOW_3_TARGET_CALENDAR_ID=lead.busy@company.com
SYNC_FLOW_3_START_OFFSET=-15
SYNC_FLOW_3_END_OFFSET=15

# Sync Flow 4: Member 2 → Team Lead busy calendar
SYNC_FLOW_4_NAME=Member 2 to Lead
SYNC_FLOW_4_SOURCE_ACCOUNT_ID=3
SYNC_FLOW_4_SOURCE_CALENDAR_ID=member2@company.com
SYNC_FLOW_4_TARGET_ACCOUNT_ID=1
SYNC_FLOW_4_TARGET_CALENDAR_ID=lead.busy@company.com
SYNC_FLOW_4_START_OFFSET=-15
SYNC_FLOW_4_END_OFFSET=15
```

### Result
- Team lead's meetings appear in team members' calendars
- Team members' conflicts appear in lead's calendar
- 40-minute buffer for lead meetings (20 before + 20 after)
- 30-minute buffer for member meetings (15 before + 15 after)

## Scenario 4: Client-Focused Setup

**Use Case**: Separate client calendars with different buffer times

### Configuration

```bash
# Google Account 1: Main business account
GOOGLE_ACCOUNT_1_EMAIL=main@business.com
GOOGLE_ACCOUNT_1_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=1//04_business_refresh_token

# Sync Flow 1: Main calendar → VIP client calendar (longer buffer)
SYNC_FLOW_1_NAME=Main to VIP Clients
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_1_SOURCE_CALENDAR_ID=main@business.com
SYNC_FLOW_1_TARGET_ACCOUNT_ID=1
SYNC_FLOW_1_TARGET_CALENDAR_ID=vip.clients@business.com
SYNC_FLOW_1_START_OFFSET=-30  # 30 minutes before
SYNC_FLOW_1_END_OFFSET=30     # 30 minutes after

# Sync Flow 2: Main calendar → Regular client calendar (standard buffer)
SYNC_FLOW_2_NAME=Main to Regular Clients
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_2_SOURCE_CALENDAR_ID=main@business.com
SYNC_FLOW_2_TARGET_ACCOUNT_ID=1
SYNC_FLOW_2_TARGET_CALENDAR_ID=regular.clients@business.com
SYNC_FLOW_2_START_OFFSET=-15
SYNC_FLOW_2_END_OFFSET=15

# Sync Flow 3: Main calendar → Internal team calendar (minimal buffer)
SYNC_FLOW_3_NAME=Main to Internal
SYNC_FLOW_3_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_3_SOURCE_CALENDAR_ID=main@business.com
SYNC_FLOW_3_TARGET_ACCOUNT_ID=1
SYNC_FLOW_3_TARGET_CALENDAR_ID=internal.team@business.com
SYNC_FLOW_3_START_OFFSET=-5
SYNC_FLOW_3_END_OFFSET=5
```

### Result
- Different buffer times for different stakeholders
- VIP clients see 1-hour busy blocks (30 min before + 30 min after)
- Regular clients see 30-minute busy blocks
- Internal team sees 10-minute busy blocks

## Scenario 5: Timezone-Aware Setup

**Use Case**: Different timezones and custom scheduling

### Configuration

```bash
# Custom polling schedule
SYNC_INTERVAL_MINUTES=180  # Every 3 hours

# Google Account 1: US East Coast
GOOGLE_ACCOUNT_1_EMAIL=useast@company.com
GOOGLE_ACCOUNT_1_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=1//04_us_east_refresh_token

# Google Account 2: US West Coast
GOOGLE_ACCOUNT_2_EMAIL=uswest@company.com
GOOGLE_ACCOUNT_2_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ACCOUNT_2_CLIENT_SECRET=your_client_secret
GOOGLE_ACCOUNT_2_REFRESH_TOKEN=1//04_us_west_refresh_token

# Sync Flow 1: East Coast → West Coast (account for timezone)
SYNC_FLOW_1_NAME=East to West
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_1_SOURCE_CALENDAR_ID=east@company.com
SYNC_FLOW_1_TARGET_ACCOUNT_ID=2
SYNC_FLOW_1_TARGET_CALENDAR_ID=west.busy@company.com
SYNC_FLOW_1_START_OFFSET=-45  # Extra buffer for timezone coordination
SYNC_FLOW_1_END_OFFSET=45

# Sync Flow 2: West Coast → East Coast
SYNC_FLOW_2_NAME=West to East
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=2
SYNC_FLOW_2_SOURCE_CALENDAR_ID=west@company.com
SYNC_FLOW_2_TARGET_ACCOUNT_ID=1
SYNC_FLOW_2_TARGET_CALENDAR_ID=east.busy@company.com
SYNC_FLOW_2_START_OFFSET=-45
SYNC_FLOW_2_END_OFFSET=45
```

### Result
- Daily sync runs at 9:00 AM Eastern Time
- 1.5-hour busy blocks to account for timezone coordination
- Calendar times are automatically converted by Google Calendar API

## Advanced Configuration Options

### Custom Sync Timing

```bash
# Early morning sync for European timezones
SYNC_INTERVAL_MINUTES=240  # Every 4 hours

# Late evening sync for Asian timezones
SYNC_INTERVAL_MINUTES=30   # Every 30 minutes
```

### Minimal vs. Maximum Buffer Examples

```bash
# Minimal buffer (tight scheduling)
SYNC_FLOW_1_START_OFFSET=-5
SYNC_FLOW_1_END_OFFSET=5

# Standard buffer (normal scheduling)
SYNC_FLOW_2_START_OFFSET=-15
SYNC_FLOW_2_END_OFFSET=15

# Maximum buffer (executive scheduling)
SYNC_FLOW_3_START_OFFSET=-60
SYNC_FLOW_3_END_OFFSET=60
```

### Multiple Sync Flows from Same Source

```bash
# One source calendar syncing to multiple targets
SYNC_FLOW_1_SOURCE_CALENDAR_ID=main@company.com
SYNC_FLOW_1_TARGET_CALENDAR_ID=busy1@company.com

SYNC_FLOW_2_SOURCE_CALENDAR_ID=main@company.com
SYNC_FLOW_2_TARGET_CALENDAR_ID=busy2@company.com

SYNC_FLOW_3_SOURCE_CALENDAR_ID=main@company.com
SYNC_FLOW_3_TARGET_CALENDAR_ID=busy3@company.com
```

## Calendar ID Reference

### Finding Calendar IDs

Use the list calendars script to find calendar IDs:

```bash
python scripts/list_google_calendars.py --account-id 1
```

### Common Calendar ID Formats

- **Primary calendar**: `your.email@gmail.com`
- **Secondary calendar**: `your.email@gmail.com` (same format)
- **Shared calendar**: `calendar_id@group.calendar.google.com`
- **Google Workspace**: `your.email@company.com`

### Calendar ID Examples

```bash
# Personal Gmail primary calendar
SOURCE_CALENDAR_ID=john.doe@gmail.com

# Work Google Workspace calendar
SOURCE_CALENDAR_ID=john.doe@company.com

# Shared calendar (generated ID)
TARGET_CALENDAR_ID=abc123def456@group.calendar.google.com

# Google Workspace shared calendar
TARGET_CALENDAR_ID=team.busy@company.com
```

## Validation and Testing

### Configuration Validation

```bash
# Test configuration loading
python -c "
from backend.services.google_calendar.config_loader import load_multi_account_config
config = load_multi_account_config()
print(f'✓ {len(config.accounts)} accounts loaded')
print(f'✓ {len(config.sync_flows)} sync flows loaded')
for flow in config.sync_flows:
    print(f'  {flow.name}: {flow.source_account_id} -> {flow.target_account_id}')
"
```

### Test Calendar Access

```bash
# Test calendar access for all accounts
python -m pytest tests/integration/test_calendar_access.py -m integration -v
```

### Manual Sync Test

```bash
# Run manual sync to test configuration
python -c "
from backend.services.google_calendar.config_loader import load_multi_account_config
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.polling_scheduler import PollingScheduler

config = load_multi_account_config()
account_manager = AccountManager(config)
scheduler = PollingScheduler(config, account_manager)

result = scheduler.run_manual_sync(days_back=1, days_forward=3)
print(f'Manual sync result: {result}')
"
```

## Common Configuration Patterns

### Pattern 1: Bidirectional Sync
```bash
# Account A → Account B
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=1
SYNC_FLOW_1_TARGET_ACCOUNT_ID=2

# Account B → Account A
SYNC_FLOW_2_SOURCE_ACCOUNT_ID=2
SYNC_FLOW_2_TARGET_ACCOUNT_ID=1
```

### Pattern 2: Hub and Spoke
```bash
# Central calendar → Multiple targets
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=1  # Hub
SYNC_FLOW_1_TARGET_ACCOUNT_ID=2  # Spoke 1

SYNC_FLOW_2_SOURCE_ACCOUNT_ID=1  # Hub
SYNC_FLOW_2_TARGET_ACCOUNT_ID=3  # Spoke 2
```

### Pattern 3: Cascading Sync
```bash
# A → B → C (requires multiple Personal Automation Hub instances)
# Instance 1: A → B
# Instance 2: B → C
```

## Best Practices

1. **Start Simple**: Begin with 2 accounts and 2 sync flows
2. **Test Incrementally**: Add one sync flow at a time
3. **Use Descriptive Names**: Make sync flow names clear and descriptive
4. **Document Calendar IDs**: Keep a record of which calendar IDs correspond to which calendars
5. **Monitor Logs**: Check logs regularly for sync issues
6. **Backup Configuration**: Keep a backup of your working `.env` file
7. **Use Consistent Offsets**: Use similar offset values for related sync flows

## Troubleshooting Configuration

### Common Issues

1. **Sequential Numbering**: Account and sync flow IDs must start from 1 and increment
2. **Account Reference**: Sync flows must reference existing account IDs
3. **Calendar Access**: Ensure you have write access to target calendars
4. **Offset Values**: Negative for start offset, positive for end offset

### Validation Commands

```bash
# Check environment variables
env | grep GOOGLE_ACCOUNT | sort
env | grep SYNC_FLOW | sort

# Test specific account
python -c "
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.config_loader import load_multi_account_config

config = load_multi_account_config()
account_manager = AccountManager(config)
client = account_manager.get_client(1)
print(f'Account 1 calendars: {len(client.list_calendars())}')
"
```

This guide provides practical examples for configuring Google Calendar synchronization in various scenarios. Adapt these examples to your specific needs and test thoroughly before deploying to production. 