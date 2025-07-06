# Google Calendar Setup Guide

This guide explains how to set up Google Calendar integration for calendar synchronization in the Personal Automation Hub.

## Prerequisites

1. Google Cloud Project with Calendar API enabled
2. OAuth2 credentials (client ID and secret)
3. Access to source and target calendars

## Step 1: Create Google Cloud Project and Enable Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

## Step 2: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" user type (allows personal Gmail accounts)
3. Fill in the required application information:
   - Application name: "Personal Automation Hub"
   - User support email: your work email (from dropdown)
   - Developer contact information: your work email
4. **Add Calendar API Scope:**
   - Click "Add or remove scopes"
   - Search for "calendar" and select: `https://www.googleapis.com/auth/calendar`
   - This scope provides full calendar access (read/write)
5. Save the consent screen configuration

## Step 3: Configure Test Users

1. Go to "Google Auth Platform" → "Audience" (or find "Audience" in the left sidebar)
2. Click "Make External" if not already external
3. **Important:** Add test users in the "Test users" section:
   - Click "Add users"
   - Add your personal Gmail account (e.g., `your.personal@gmail.com`)
   - This allows your personal account to access the app without verification
4. Save the test user configuration

**⚠️ Critical:** You MUST add your personal Gmail as a test user BEFORE running the OAuth setup script, otherwise Google will block the authorization.

## Step 4: Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. **Select "Desktop application" as the application type**
   - Even though your app runs on a server, choose "Desktop application"
   - This is correct for server apps that use OAuth2 refresh tokens
   - "Web application" would require redirect URL configuration (not needed)
4. Give it a descriptive name (e.g., "Personal Automation Hub")
5. Copy the Client ID and Client Secret (you'll need these for the next step)

### About Test Users

When you add test users in Google Auth Platform → Audience:
- **No verification required:** Test users can access your app without Google verification
- **Personal Gmail accounts:** You can use any Gmail account as a test user
- **Limited to 100 users:** You can add up to 100 test users
- **Full functionality:** Test users have the same access as verified users
- **No expiration:** Test user access doesn't expire

This is perfect for personal automation tools where you don't need public access.

### Why This Setup Works

This configuration allows you to:
- **Create the app** under your work Google Cloud account
- **Authorize calendar access** using your personal Gmail account
- **Access calendars** that are visible to your personal account (both owned and shared)
- **Avoid Google verification** process since you're using test users

The OAuth2 flow happens once during setup, then your server uses the refresh token for ongoing API access.

## Step 5: Obtain Refresh Token

**⚠️ Prerequisites Check:**
- ✅ Calendar API is enabled in your Google Cloud project (Step 1)
- ✅ OAuth consent screen is configured with your app information (Step 2)
- ✅ Test user (your personal Gmail) is added in Google Auth Platform → Audience (Step 3)
- ✅ Calendar API scope is added to your consent screen (Step 2)
- ✅ OAuth2 credentials are created with "Desktop application" type (Step 4)

Now set up your environment variables and run the OAuth setup script:

```bash
# Set your OAuth2 credentials (from Step 4)
export GOOGLE_CLIENT_ID="your_client_id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your_client_secret"

# Run the OAuth setup script
python scripts/setup_google_oauth.py
```

This script will:
1. Open your browser for Google OAuth consent
2. You'll login with your **personal Gmail account** (the test user)
3. Request calendar access permissions
4. Generate a refresh token
5. Display the token for adding to your `.env` file

**Important:** When the browser opens, make sure to login with your personal Gmail account (the one you added as a test user), not your work account.

## Step 6: Configure Environment Variables

Add the following variables to your `.env` file:

```bash
# Google Calendar Integration (OAuth2)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token

# Calendar Sync Schedule
DAILY_SYNC_HOUR=6
DAILY_SYNC_TIMEZONE=UTC

# Sync Flow 1 Example: Work calendar to personal busy calendar
SYNC_FLOW_1_NAME=Work to Personal
SYNC_FLOW_1_SOURCE_CALENDAR_ID=work.calendar@company.com
SYNC_FLOW_1_TARGET_CALENDAR_IDS=busy.personal@gmail.com
SYNC_FLOW_1_START_OFFSET=-15
SYNC_FLOW_1_END_OFFSET=15

# Sync Flow 2 Example: Personal calendar to work busy calendar
SYNC_FLOW_2_NAME=Personal to Work
SYNC_FLOW_2_SOURCE_CALENDAR_ID=primary
SYNC_FLOW_2_TARGET_CALENDAR_IDS=busy.work@company.com
SYNC_FLOW_2_START_OFFSET=-15
SYNC_FLOW_2_END_OFFSET=15

# Add more sync flows as needed: SYNC_FLOW_3_*, SYNC_FLOW_4_*, etc.
```

## Step 7: Test Your Setup

Run the calendar access test to verify everything is working:

```bash
python scripts/test_calendar_access.py
```

This script will:
1. Test environment variables
2. Test Google Calendar API connection
3. List accessible calendars
4. Validate sync flow configuration
5. Show sample configuration

## Sync Flow Configuration

### Environment Variable Pattern

Each sync flow uses numbered environment variables:

- `SYNC_FLOW_N_NAME` - Human-readable name for the sync flow
- `SYNC_FLOW_N_SOURCE_CALENDAR_ID` - Source calendar ID to monitor
- `SYNC_FLOW_N_TARGET_CALENDAR_IDS` - Target calendar ID(s) for busy blocks (comma-separated)
- `SYNC_FLOW_N_START_OFFSET` - Minutes before event start for busy block (negative number)
- `SYNC_FLOW_N_END_OFFSET` - Minutes after event end for busy block (positive number)

### Calendar ID Format

- **Primary calendar:** Use `primary`
- **Other Google calendars:** Use the email address (e.g., `user@gmail.com`)
- **Shared calendars:** Use the full calendar ID from Google Calendar settings

### Offset Configuration

- `START_OFFSET=-15` means busy block starts 15 minutes before the original event
- `END_OFFSET=15` means busy block ends 15 minutes after the original event
- Negative values = earlier time, positive values = later time

### Example Scenarios

**Scenario 1: Work-Life Separation**
```bash
# Block work meetings on personal calendar
SYNC_FLOW_1_NAME=Work to Personal
SYNC_FLOW_1_SOURCE_CALENDAR_ID=work@company.com
SYNC_FLOW_1_TARGET_CALENDAR_IDS=personal@gmail.com
SYNC_FLOW_1_START_OFFSET=-15
SYNC_FLOW_1_END_OFFSET=15

# Block personal events on work calendar
SYNC_FLOW_2_NAME=Personal to Work
SYNC_FLOW_2_SOURCE_CALENDAR_ID=personal@gmail.com
SYNC_FLOW_2_TARGET_CALENDAR_IDS=work@company.com
SYNC_FLOW_2_START_OFFSET=-15
SYNC_FLOW_2_END_OFFSET=15
```

**Scenario 2: Multiple Target Calendars**
```bash
# Block main calendar events on multiple busy calendars
SYNC_FLOW_1_NAME=Main to Multiple Busy Calendars
SYNC_FLOW_1_SOURCE_CALENDAR_ID=primary
SYNC_FLOW_1_TARGET_CALENDAR_IDS=busy1@gmail.com,busy2@gmail.com,busy3@gmail.com
SYNC_FLOW_1_START_OFFSET=-10
SYNC_FLOW_1_END_OFFSET=10
```

## How It Works

### Event Filtering
- Only events with 2 or more participants are synchronized
- Single-person events are ignored
- Events must be confirmed (not cancelled)

### Busy Block Creation
- Creates events titled "Busy" in target calendars
- Uses exact time matching to prevent duplicates
- Resistant to manual editing (won't break if user modifies busy blocks)

### Sync Methods
- **Real-time webhooks:** Immediate synchronization when events change
- **Daily polling:** Backup sync runs once daily (6 AM by default)
- **Idempotent operations:** Safe to run multiple times without creating duplicates

## Troubleshooting

### Common Issues

**OAuth2 Errors:**
- Ensure calendar API is enabled in Google Cloud Console
- Check that OAuth2 credentials are for "Desktop application" type
- Verify client ID and secret are correct
- **"This app isn't verified" error:** Make sure you added your personal Gmail as a test user in Google Auth Platform → Audience
- **Access blocked error:** Ensure you're logging in with the Gmail account that was added as a test user
- **Can't find test users section:** Go to Google Auth Platform → Audience (not OAuth consent screen)

**Calendar Access Issues:**
- Ensure you have read/write access to both source and target calendars
- For shared calendars, you need at least "Make changes to events" permission
- Test with `python scripts/test_calendar_access.py`

**Sync Flow Issues:**
- Verify calendar IDs are correct (check output of test script)
- Ensure sync flow environment variables follow the exact naming pattern
- Check that offset values are integers (negative for start, positive for end)

### Debug Mode

To enable debug logging, set the following in your `.env` file:
```bash
LOG_LEVEL=DEBUG
```

### Verification Steps

1. **Test OAuth:** `python scripts/setup_google_oauth.py`
2. **Test Access:** `python scripts/test_calendar_access.py`
3. **Check Logs:** Look for sync operations in application logs
4. **Manual Test:** Create a test event with 2+ participants and verify busy block creation

## Security Considerations

- Keep your `.env` file secure and never commit it to version control
- Use least-privilege access - only grant calendar permissions needed
- Regularly rotate OAuth2 credentials if compromised
- Monitor sync operations through application logs

## Next Steps

After setup is complete:
1. Start the FastAPI server: `python run.py`
2. Monitor logs for sync operations
3. Test with real calendar events
4. Configure additional sync flows as needed 