"""
Tests for all-day events support in Google Calendar sync.

This module tests the logic for handling all-day events:
- All-day events should not have +/- 15 minute offsets applied
- Regular events should still have offsets applied
- BusyBlock creation should respect all-day flag
"""

from datetime import datetime, timedelta
from backend.models.calendar import CalendarEvent, SyncFlow, BusyBlock


class TestAllDayEvents:
    """Test cases for all-day events support."""
    
    def test_all_day_event_no_offsets(self) -> None:
        """Test that all-day events don't get time offsets applied."""
        # Create an all-day event
        start_time = datetime(2024, 1, 15, 0, 0, 0)
        end_time = datetime(2024, 1, 16, 0, 0, 0)
        
        event = CalendarEvent(
            id="test-event-1",
            calendar_id="source-cal",
            account_id=1,
            title="All Day Meeting",
            start_time=start_time,
            end_time=end_time,
            all_day=True,
            status="confirmed",
            participant_count=2
        )
        
        # Create sync flow with offsets
        flow = SyncFlow(
            name="test-flow",
            source_account_id=1,
            source_calendar_id="source-cal",
            target_account_id=2,
            target_calendar_id="target-cal",
            start_offset=-15,  # 15 minutes before
            end_offset=15      # 15 minutes after
        )
        
        # Create busy block
        busy_block = BusyBlock.from_event_and_flow(event, flow)
        
        # For all-day events, times should NOT have offsets applied
        assert busy_block.start_time == start_time
        assert busy_block.end_time == end_time
        assert busy_block.source_event.is_all_day() is True
    
    def test_regular_event_with_offsets(self) -> None:
        """Test that regular events still get time offsets applied."""
        # Create a regular event
        start_time = datetime(2024, 1, 15, 10, 30, 0)
        end_time = datetime(2024, 1, 15, 11, 30, 0)
        
        event = CalendarEvent(
            id="test-event-2",
            calendar_id="source-cal",
            account_id=1,
            title="Regular Meeting",
            start_time=start_time,
            end_time=end_time,
            all_day=False,
            status="confirmed",
            participant_count=3
        )
        
        # Create sync flow with offsets
        flow = SyncFlow(
            name="test-flow",
            source_account_id=1,
            source_calendar_id="source-cal",
            target_account_id=2,
            target_calendar_id="target-cal",
            start_offset=-15,  # 15 minutes before
            end_offset=15      # 15 minutes after
        )
        
        # Create busy block
        busy_block = BusyBlock.from_event_and_flow(event, flow)
        
        # For regular events, times should have offsets applied
        expected_start = start_time + timedelta(minutes=-15)
        expected_end = end_time + timedelta(minutes=15)
        
        assert busy_block.start_time == expected_start
        assert busy_block.end_time == expected_end
        assert busy_block.source_event.is_all_day() is False
    
    def test_multi_day_event_with_offsets(self) -> None:
        """Test that multi-day events with specific times still get offsets."""
        # Create a multi-day event with specific times (not all-day)
        start_time = datetime(2024, 1, 15, 9, 0, 0)  # Monday 9 AM
        end_time = datetime(2024, 1, 17, 17, 0, 0)   # Wednesday 5 PM
        
        event = CalendarEvent(
            id="test-event-3",
            calendar_id="source-cal",
            account_id=1,
            title="Multi-Day Conference",
            start_time=start_time,
            end_time=end_time,
            all_day=False,  # Not all-day, has specific times
            status="confirmed",
            participant_count=5
        )
        
        # Create sync flow with offsets
        flow = SyncFlow(
            name="test-flow",
            source_account_id=1,
            source_calendar_id="source-cal",
            target_account_id=2,
            target_calendar_id="target-cal",
            start_offset=-15,  # 15 minutes before
            end_offset=15      # 15 minutes after
        )
        
        # Create busy block
        busy_block = BusyBlock.from_event_and_flow(event, flow)
        
        # For multi-day events with specific times, offsets should still apply
        expected_start = start_time + timedelta(minutes=-15)
        expected_end = end_time + timedelta(minutes=15)
        
        assert busy_block.start_time == expected_start
        assert busy_block.end_time == expected_end
        assert busy_block.source_event.is_all_day() is False
    
    def test_calendar_event_all_day_methods(self) -> None:
        """Test CalendarEvent all-day related methods."""
        # Test all-day event
        all_day_event = CalendarEvent(
            id="all-day-event",
            calendar_id="cal-1",
            account_id=1,
            title="All Day Event",
            start_time=datetime(2024, 1, 15, 0, 0, 0),
            end_time=datetime(2024, 1, 16, 0, 0, 0),
            all_day=True,
            status="confirmed",
            participant_count=2
        )
        
        assert all_day_event.is_all_day() is True
        assert all_day_event.all_day is True
        
        # Test regular event
        regular_event = CalendarEvent(
            id="regular-event",
            calendar_id="cal-1",
            account_id=1,
            title="Regular Event",
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            end_time=datetime(2024, 1, 15, 11, 0, 0),
            all_day=False,
            status="confirmed",
            participant_count=2
        )
        
        assert regular_event.is_all_day() is False
        assert regular_event.all_day is False
        
        # Test default behavior (all_day defaults to False)
        default_event = CalendarEvent(
            id="default-event",
            calendar_id="cal-1",
            account_id=1,
            title="Default Event",
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            end_time=datetime(2024, 1, 15, 11, 0, 0),
            status="confirmed",
            participant_count=2
        )
        
        assert default_event.is_all_day() is False
        assert default_event.all_day is False 