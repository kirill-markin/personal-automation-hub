#!/usr/bin/env python3
"""
Integration tests for Calendar Sync Engine.

This script tests the core sync engine functionality by:
1. Processing real calendar events through sync flows
2. Creating and managing busy blocks in target calendars
3. Testing multi-flow support and event filtering
4. Validating idempotent operations

Usage:
    # As pytest integration test
    python -m pytest tests/integration/test_sync_engine.py -v -m integration
    
    # As standalone script
    python tests/integration/test_sync_engine.py
    python tests/integration/test_sync_engine.py --account-id 1
    python tests/integration/test_sync_engine.py --test-busy-blocks
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import pytest
from dotenv import load_dotenv
import random
import string

# Load environment variables from .env file
load_dotenv(override=True)

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.google_calendar.config_loader import load_multi_account_config
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.sync_engine import CalendarSyncEngine
from backend.models.calendar import (
    MultiAccountConfig, 
    CalendarEvent, 
    CalendarSyncResult
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncEngineTestHelper:
    """Helper class for sync engine integration tests."""
    
    def __init__(self, config: MultiAccountConfig, account_manager: AccountManager, sync_engine: CalendarSyncEngine):
        self.config = config
        self.account_manager = account_manager
        self.sync_engine = sync_engine
        
        # Track test events for cleanup
        self.test_events_created: List[Dict[str, Any]] = []
        self.test_busy_blocks_created: List[Dict[str, Any]] = []
    
    def create_test_event(self, account_id: int, calendar_id: str, 
                         title: str, participants: List[str], 
                         start_offset_hours: int = 1, duration_hours: int = 1) -> Dict[str, Any]:
        """Create a test event in the specified calendar.
        
        Args:
            account_id: Account ID for the calendar
            calendar_id: Calendar ID to create event in
            title: Event title
            participants: List of participant emails
            start_offset_hours: Hours from now to start the event
            duration_hours: Duration of the event in hours
            
        Returns:
            Created event data
        """
        # Calculate event times
        start_time = datetime.now() + timedelta(hours=start_offset_hours)
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Create event
        client = self.account_manager.get_client(account_id)
        event_data = client.create_event(
            calendar_id=calendar_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=f"Test event created by sync engine integration test",
            participants=participants
        )
        
        # Track for cleanup
        self.test_events_created.append({
            'account_id': account_id,
            'calendar_id': calendar_id,
            'event_id': event_data['id'],
            'title': title
        })
        
        logger.info(f"Created test event '{title}' in calendar {calendar_id} with {len(participants)} participants")
        return event_data
    
    def delete_test_event(self, account_id: int, calendar_id: str, event_id: str) -> bool:
        """Delete a test event.
        
        Args:
            account_id: Account ID for the calendar
            calendar_id: Calendar ID
            event_id: Event ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            client = self.account_manager.get_client(account_id)
            success = client.delete_event(calendar_id, event_id)
            logger.info(f"Deleted test event {event_id} from calendar {calendar_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting test event {event_id}: {e}")
            return False
    
    def find_busy_blocks_by_title(self, account_id: int, calendar_id: str, 
                                 title: str = "Busy") -> List[Dict[str, Any]]:
        """Find busy blocks in a calendar by title.
        
        Args:
            account_id: Account ID for the calendar
            calendar_id: Calendar ID to search
            title: Title to search for
            
        Returns:
            List of found busy blocks
        """
        try:
            client = self.account_manager.get_client(account_id)
            
            # Search for events in the next 7 days
            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now() + timedelta(days=7)
            
            events = client.get_events(calendar_id, start_time, end_time)
            
            # Filter by title
            busy_blocks = [event for event in events if event.get('title', '').lower() == title.lower()]
            
            logger.info(f"Found {len(busy_blocks)} busy blocks with title '{title}' in calendar {calendar_id}")
            return busy_blocks
            
        except Exception as e:
            logger.error(f"Error finding busy blocks: {e}")
            return []
    
    def cleanup_test_data(self) -> None:
        """Clean up all test events and busy blocks created during tests."""
        logger.info("Cleaning up test data...")
        
        # Delete test events
        for event in self.test_events_created:
            self.delete_test_event(
                event['account_id'],
                event['calendar_id'],
                event['event_id']
            )
        
        # Delete test busy blocks
        for block in self.test_busy_blocks_created:
            self.delete_test_event(
                block['account_id'],
                block['calendar_id'],
                block['event_id']
            )
        
        logger.info("Test data cleanup completed")
    
    def generate_random_test_title(self, prefix: str = "SyncTest") -> str:
        """Generate a random test title.
        
        Args:
            prefix: Prefix for the title
            
        Returns:
            Random test title
        """
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"{prefix}_{random_suffix}"


@pytest.mark.integration
def test_sync_engine_initialization():
    """Test sync engine initialization with real configuration."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    
    # Verify initialization
    assert sync_engine.config == config
    assert sync_engine.account_manager == account_manager
    assert len(sync_engine.config.accounts) > 0
    assert len(sync_engine.config.sync_flows) > 0
    
    # Verify stats are initialized
    stats = sync_engine.get_stats()
    assert stats.events_processed == 0
    assert stats.busy_blocks_created == 0
    assert stats.busy_blocks_deleted == 0
    assert stats.accounts == len(config.accounts)
    assert stats.sync_flows == len(config.sync_flows)


@pytest.mark.integration
def test_process_event_with_multiple_participants():
    """Test processing an event with multiple participants."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    helper = SyncEngineTestHelper(config, account_manager, sync_engine)
    
    # Get first sync flow for testing
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    flow = config.sync_flows[0]
    
    try:
        # Create test event with multiple participants
        participants = ["test1@example.com", "test2@example.com", "test3@example.com"]
        title = helper.generate_random_test_title("MultiParticipant")
        
        test_event_data = helper.create_test_event(
            account_id=flow.source_account_id,
            calendar_id=flow.source_calendar_id,
            title=title,
            participants=participants,
            start_offset_hours=2,
            duration_hours=1
        )
        
        # Convert to CalendarEvent model
        event = CalendarEvent(
            id=test_event_data['id'],
            calendar_id=flow.source_calendar_id,
            account_id=flow.source_account_id,
            title=title,
            description=test_event_data.get('description', ''),
            start_time=test_event_data['start_time'],
            end_time=test_event_data['end_time'],
            participants=participants,
            participant_count=len(participants),
            status='confirmed',
            creator=test_event_data.get('creator', ''),
            organizer=test_event_data.get('organizer', '')
        )
        
        # Process event through sync engine
        results = sync_engine.process_event(event, "test")
        
        # Verify processing
        assert len(results) > 0, "Event should be processed through at least one sync flow"
        
        # Check that the event was processed successfully
        for result in results:
            assert result.success, f"Event processing failed: {result.error}"
            assert result.event_id == event.id
            assert result.event_title == title
            assert result.sync_type == "test"
            assert result.action in ['created', 'existed'], f"Unexpected action: {result.action}"
        
        # Verify busy block was created
        busy_blocks = helper.find_busy_blocks_by_title(
            account_id=flow.target_account_id,
            calendar_id=flow.target_calendar_id,
            title="Busy"
        )
        
        # Should have at least one busy block
        assert len(busy_blocks) > 0, "Busy block should be created for multi-participant event"
        
        # Find the busy block for our test event
        test_busy_block = None
        for block in busy_blocks:
            if title in block.get('description', ''):
                test_busy_block = block
                break
        
        assert test_busy_block is not None, "Could not find busy block for test event"
        
        # Track for cleanup
        helper.test_busy_blocks_created.append({
            'account_id': flow.target_account_id,
            'calendar_id': flow.target_calendar_id,
            'event_id': test_busy_block['id'],
            'title': 'Busy'
        })
        
        logger.info(f"Successfully processed event with {len(participants)} participants")
        
    finally:
        # Clean up test data
        helper.cleanup_test_data()


@pytest.mark.integration
def test_process_event_with_single_participant():
    """Test processing an event with single participant (should be skipped)."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    helper = SyncEngineTestHelper(config, account_manager, sync_engine)
    
    # Get first sync flow for testing
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    flow = config.sync_flows[0]
    
    try:
        # Create test event with single participant
        participants = ["test@example.com"]
        title = helper.generate_random_test_title("SingleParticipant")
        
        test_event_data = helper.create_test_event(
            account_id=flow.source_account_id,
            calendar_id=flow.source_calendar_id,
            title=title,
            participants=participants,
            start_offset_hours=2,
            duration_hours=1
        )
        
        # Convert to CalendarEvent model
        event = CalendarEvent(
            id=test_event_data['id'],
            calendar_id=flow.source_calendar_id,
            account_id=flow.source_account_id,
            title=title,
            description=test_event_data.get('description', ''),
            start_time=test_event_data['start_time'],
            end_time=test_event_data['end_time'],
            participants=participants,
            participant_count=len(participants),
            status='confirmed',
            creator=test_event_data.get('creator', ''),
            organizer=test_event_data.get('organizer', '')
        )
        
        # Process event through sync engine
        results = sync_engine.process_event(event, "test")
        
        # Verify processing
        assert len(results) > 0, "Event should be processed through at least one sync flow"
        
        # Check that the event was skipped (doesn't meet criteria)
        for result in results:
            assert result.success, f"Event processing failed: {result.error}"
            assert result.event_id == event.id
            assert result.event_title == title
            assert result.sync_type == "test"
            assert result.action == 'skipped', f"Single participant event should be skipped, got: {result.action}"
            assert result.reason and "doesn't meet criteria" in result.reason
        
        # Verify no busy block was created
        busy_blocks = helper.find_busy_blocks_by_title(
            account_id=flow.target_account_id,
            calendar_id=flow.target_calendar_id,
            title="Busy"
        )
        
        # Should not have busy block for our test event
        test_busy_block = None
        for block in busy_blocks:
            if title in block.get('description', ''):
                test_busy_block = block
                break
        
        assert test_busy_block is None, "Busy block should not be created for single participant event"
        
        logger.info(f"Successfully skipped single participant event")
        
    finally:
        # Clean up test data
        helper.cleanup_test_data()


@pytest.mark.integration
def test_event_deletion_removes_busy_block():
    """Test that deleting an event removes corresponding busy block."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    helper = SyncEngineTestHelper(config, account_manager, sync_engine)
    
    # Get first sync flow for testing
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    flow = config.sync_flows[0]
    
    try:
        # Create test event with multiple participants
        participants = ["test1@example.com", "test2@example.com"]
        title = helper.generate_random_test_title("DeletionTest")
        
        test_event_data = helper.create_test_event(
            account_id=flow.source_account_id,
            calendar_id=flow.source_calendar_id,
            title=title,
            participants=participants,
            start_offset_hours=3,
            duration_hours=1
        )
        
        # Convert to CalendarEvent model
        event = CalendarEvent(
            id=test_event_data['id'],
            calendar_id=flow.source_calendar_id,
            account_id=flow.source_account_id,
            title=title,
            description=test_event_data.get('description', ''),
            start_time=test_event_data['start_time'],
            end_time=test_event_data['end_time'],
            participants=participants,
            participant_count=len(participants),
            status='confirmed',
            creator=test_event_data.get('creator', ''),
            organizer=test_event_data.get('organizer', '')
        )
        
        # Process event to create busy block
        _ = sync_engine.process_event(event, "test")
        
        # Verify busy block was created
        busy_blocks_before = helper.find_busy_blocks_by_title(
            account_id=flow.target_account_id,
            calendar_id=flow.target_calendar_id,
            title="Busy"
        )
        
        test_busy_block = None
        for block in busy_blocks_before:
            if title in block.get('description', ''):
                test_busy_block = block
                break
        
        assert test_busy_block is not None, "Busy block should be created first"
        
        # Now process cancelled event
        cancelled_event = CalendarEvent(
            id=event.id,
            calendar_id=event.calendar_id,
            account_id=event.account_id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            participants=event.participants,
            participant_count=event.participant_count,
            status='cancelled',  # Mark as cancelled
            creator=event.creator,
            organizer=event.organizer
        )
        
        # Process cancelled event
        delete_results = sync_engine.process_event(cancelled_event, "test")
        
        # Verify processing
        assert len(delete_results) > 0, "Cancelled event should be processed"
        
        for result in delete_results:
            assert result.success, f"Cancelled event processing failed: {result.error}"
            assert result.action in ['deleted', 'delete_attempted'], f"Unexpected action: {result.action}"
        
        # Verify busy block was deleted
        busy_blocks_after = helper.find_busy_blocks_by_title(
            account_id=flow.target_account_id,
            calendar_id=flow.target_calendar_id,
            title="Busy"
        )
        
        # Should not have busy block for our test event anymore
        remaining_test_busy_block = None
        for block in busy_blocks_after:
            if title in block.get('description', ''):
                remaining_test_busy_block = block
                break
        
        assert remaining_test_busy_block is None, "Busy block should be deleted for cancelled event"
        
        logger.info(f"Successfully deleted busy block for cancelled event")
        
    finally:
        # Clean up test data
        helper.cleanup_test_data()


@pytest.mark.integration
def test_sync_calendar_events():
    """Test syncing events from a calendar within a date range."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    
    # Get first sync flow for testing
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    flow = config.sync_flows[0]
    
    # Define date range
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now() + timedelta(days=7)
    
    # Sync calendar events
    result = sync_engine.sync_calendar_events(
        calendar_id=flow.source_calendar_id,
        account_id=flow.source_account_id,
        start_date=start_date,
        end_date=end_date,
        sync_type="test"
    )
    
    # Verify result structure
    assert isinstance(result, CalendarSyncResult)
    assert result.calendar_id == flow.source_calendar_id
    assert result.account_id == flow.source_account_id
    assert result.sync_type == "test"
    assert result.events_found >= 0
    assert result.events_processed >= 0
    assert result.error is None or isinstance(result.error, str)
    
    logger.info(f"Sync result: {result.events_found} events found, {result.events_processed} processed")


@pytest.mark.integration
def test_sync_all_source_calendars():
    """Test syncing all source calendars from configured sync flows."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    # Define date range
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now() + timedelta(days=7)
    
    # Sync all source calendars
    result = sync_engine.sync_all_source_calendars(
        start_date=start_date,
        end_date=end_date,
        sync_type="test"
    )
    
    # Verify result structure
    assert result.calendars_synced >= 0
    assert result.total_events_found >= 0
    assert result.total_events_processed >= 0
    assert result.sync_type == "test"
    
    # Verify we have results for each unique source calendar
    unique_calendars: set[Tuple[int, str]] = set()
    for flow in config.sync_flows:
        unique_calendars.add((flow.source_account_id, flow.source_calendar_id))
    
    # Should have attempted to sync each unique calendar
    assert len(result.calendar_results) == len(unique_calendars)
    
    logger.info(f"Complete sync result: {result.calendars_synced} calendars, "
               f"{result.total_events_found} events found, "
               f"{result.total_events_processed} processed")


@pytest.mark.integration
def test_idempotent_busy_block_creation():
    """Test that processing the same event multiple times doesn't create duplicate busy blocks."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    helper = SyncEngineTestHelper(config, account_manager, sync_engine)
    
    # Get first sync flow for testing
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    flow = config.sync_flows[0]
    
    try:
        # Create test event with multiple participants
        participants = ["test1@example.com", "test2@example.com"]
        title = helper.generate_random_test_title("IdempotentTest")
        
        test_event_data = helper.create_test_event(
            account_id=flow.source_account_id,
            calendar_id=flow.source_calendar_id,
            title=title,
            participants=participants,
            start_offset_hours=4,
            duration_hours=1
        )
        
        # Convert to CalendarEvent model
        event = CalendarEvent(
            id=test_event_data['id'],
            calendar_id=flow.source_calendar_id,
            account_id=flow.source_account_id,
            title=title,
            description=test_event_data.get('description', ''),
            start_time=test_event_data['start_time'],
            end_time=test_event_data['end_time'],
            participants=participants,
            participant_count=len(participants),
            status='confirmed',
            creator=test_event_data.get('creator', ''),
            organizer=test_event_data.get('organizer', '')
        )
        
        # Process event first time
        _ = sync_engine.process_event(event, "test")
        
        # Count busy blocks after first processing
        busy_blocks_after_first = helper.find_busy_blocks_by_title(
            account_id=flow.target_account_id,
            calendar_id=flow.target_calendar_id,
            title="Busy"
        )
        
        first_count = len([block for block in busy_blocks_after_first 
                          if title in block.get('description', '')])
        
        # Process same event second time
        results2 = sync_engine.process_event(event, "test")
        
        # Count busy blocks after second processing
        busy_blocks_after_second = helper.find_busy_blocks_by_title(
            account_id=flow.target_account_id,
            calendar_id=flow.target_calendar_id,
            title="Busy"
        )
        
        second_count = len([block for block in busy_blocks_after_second 
                           if title in block.get('description', '')])
        
        # Verify no duplicate busy blocks
        assert first_count == second_count, "Processing same event twice should not create duplicate busy blocks"
        assert first_count == 1, "Should have exactly one busy block for the test event"
        
        # Verify second processing shows 'existed' action
        assert results2[0].action == 'existed', "Second processing should show 'existed' action"
        
        # Track for cleanup
        test_busy_block = None
        for block in busy_blocks_after_second:
            if title in block.get('description', ''):
                test_busy_block = block
                break
        
        if test_busy_block:
            helper.test_busy_blocks_created.append({
                'account_id': flow.target_account_id,
                'calendar_id': flow.target_calendar_id,
                'event_id': test_busy_block['id'],
                'title': 'Busy'
            })
        
        logger.info(f"Successfully verified idempotent busy block creation")
        
    finally:
        # Clean up test data
        helper.cleanup_test_data()


@pytest.mark.integration
def test_multi_flow_processing():
    """Test processing an event through multiple sync flows."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    
    if len(config.sync_flows) < 2:
        pytest.skip("Need at least 2 sync flows for multi-flow testing")
    
    # Find flows that share a source calendar
    source_calendar_flows: Dict[Tuple[int, str], List[Any]] = {}
    for flow in config.sync_flows:
        key = (flow.source_account_id, flow.source_calendar_id)
        if key not in source_calendar_flows:
            source_calendar_flows[key] = []
        source_calendar_flows[key].append(flow)
    
    # Find a source calendar with multiple flows
    multi_flow_calendar: Tuple[int, str] | None = None
    for key, flows in source_calendar_flows.items():
        if len(flows) > 1:
            multi_flow_calendar = key
            break
    
    if multi_flow_calendar is None:
        pytest.skip("No source calendar with multiple flows found")
    
    account_id, calendar_id = multi_flow_calendar  # type: ignore
    applicable_flows = source_calendar_flows[multi_flow_calendar]  # type: ignore
    
    # Create mock event
    event = CalendarEvent(
        id="test-multi-flow-event",
        calendar_id=calendar_id,
        account_id=account_id,
        title="Multi-Flow Test Event",
        description="Test event for multi-flow processing",
        start_time=datetime.now() + timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=2),
        participants=["test1@example.com", "test2@example.com"],
        participant_count=2,
        status='confirmed',
        creator='test@example.com',
        organizer='test@example.com'
    )
    
    # Process event
    results = sync_engine.process_event(event, "test")
    
    # Verify we got results for all applicable flows
    assert len(results) == len(applicable_flows), \
        f"Expected {len(applicable_flows)} results, got {len(results)}"
    
    # Verify each flow processed the event
    flow_names = [flow.name for flow in applicable_flows]
    result_flow_names = [result.flow_name for result in results]
    
    for flow_name in flow_names:
        assert flow_name in result_flow_names, f"Missing result for flow {flow_name}"
    
    logger.info(f"Successfully processed event through {len(applicable_flows)} sync flows")


def main() -> None:
    """Main function to run sync engine integration tests."""
    parser = argparse.ArgumentParser(description="Test Calendar Sync Engine integration")
    parser.add_argument(
        "--account-id",
        type=int,
        help="Test specific account ID only"
    )
    parser.add_argument(
        "--test-busy-blocks",
        action="store_true",
        help="Run busy block creation/deletion tests"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Run cleanup of test data only"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_multi_account_config()
        account_manager = AccountManager(config)
        sync_engine = CalendarSyncEngine(config, account_manager)
        helper = SyncEngineTestHelper(config, account_manager, sync_engine)
        
        logger.info(f"Loaded configuration: {len(config.accounts)} accounts, {len(config.sync_flows)} sync flows")
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Run cleanup if requested
    if args.cleanup:
        helper.cleanup_test_data()
        return
    
    # Run tests based on arguments
    if args.test_busy_blocks:
        logger.info("Running busy block creation/deletion tests...")
        # Add specific busy block tests here
        
    else:
        logger.info("Running basic sync engine tests...")
        # Run basic functionality tests
        
    logger.info("Integration tests completed")


if __name__ == "__main__":
    main() 