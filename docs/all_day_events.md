# All-Day Events Support

## Overview

The Google Calendar sync system now supports all-day events with specialized handling that differs from regular timed events.

## How It Works

### All-Day Event Detection

The system automatically detects all-day events by checking the Google Calendar API response:
- Events with `date` fields (instead of `dateTime`) are considered all-day
- The `CalendarEvent.all_day` field is set to `True` for such events
- The `CalendarEvent.is_all_day()` method can be used to check if an event is all-day

### Busy Block Creation Logic

The system creates "busy blocks" in target calendars differently based on event type:

#### For All-Day Events:
- **No time offsets applied**: The busy block uses the exact same start and end times as the original event
- **All-day format preserved**: The busy block is also created as an all-day event
- **Rationale**: All-day events typically represent days when someone is unavailable for the entire day, so adding/subtracting 15 minutes doesn't make sense

#### For Regular Events:
- **Time offsets applied**: The busy block starts 15 minutes before and ends 15 minutes after the original event
- **Timed format preserved**: The busy block is created with specific start/end times
- **Rationale**: Regular meetings need buffer time for preparation and overruns

#### For Multi-Day Events with Specific Times:
- **Time offsets applied**: Even if the event spans multiple days, if it has specific start/end times, offsets are applied
- **Timed format preserved**: The busy block maintains the specific timing
- **Example**: A 3-day conference from Monday 9am to Wednesday 5pm would have a busy block from Monday 8:45am to Wednesday 5:15pm

## Examples

### All-Day Event Example

**Original Event:**
- Title: "Vacation Day"
- Date: January 15, 2024 (all-day)
- Participants: 2+
- Status: Confirmed
- Transparency: Busy

**Generated Busy Block:**
- Title: "Busy"
- Date: January 15, 2024 (all-day)
- No time offsets applied

### Regular Event Example

**Original Event:**
- Title: "Team Meeting"
- Time: January 15, 2024 10:00 AM - 11:00 AM
- Participants: 2+
- Status: Confirmed
- Transparency: Busy

**Generated Busy Block:**
- Title: "Busy"
- Time: January 15, 2024 9:45 AM - 11:15 AM
- 15-minute buffer before and after

### Multi-Day Event Example

**Original Event:**
- Title: "Conference"
- Time: January 15, 2024 9:00 AM - January 17, 2024 5:00 PM
- Participants: 2+
- Status: Confirmed
- Transparency: Busy
- All-day: False (has specific times)

**Generated Busy Block:**
- Title: "Busy"
- Time: January 15, 2024 8:45 AM - January 17, 2024 5:15 PM
- 15-minute buffer before and after

## Technical Implementation

### Model Changes

- Added `all_day: bool` field to `CalendarEvent` model
- Added `is_all_day()` method to `CalendarEvent` class
- Modified `BusyBlock.from_event_and_flow()` to handle all-day events differently

### Client Changes

- Updated `GoogleCalendarClient._parse_event()` to detect all-day events
- Modified `GoogleCalendarClient.create_event()` to support creating all-day events
- All-day events use Google Calendar's `date` field instead of `dateTime`

### Sync Engine Changes

- Updated event processing to pass `all_day` flag when creating busy blocks
- Modified busy block creation to respect all-day event formatting

## Configuration

No additional configuration is required. The system automatically detects and handles all-day events based on the Google Calendar API response format.

## Testing

All-day event support is tested with:
- All-day events should not have time offsets applied
- Regular events should still have offsets applied
- Multi-day events with specific times should have offsets applied
- All-day event detection and `is_all_day()` method functionality

Run tests with:
```bash
python -m pytest tests/test_all_day_events.py -v
``` 