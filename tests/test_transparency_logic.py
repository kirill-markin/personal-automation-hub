"""
Tests for transparency (busy/free) logic in calendar synchronization.

This module tests the logic for handling event transparency:
- Events marked as 'opaque' (busy) should create busy blocks
- Events marked as 'transparent' (free) should not create busy blocks
- Changes from busy to free should delete existing busy blocks
- Changes from free to busy should create new busy blocks
"""

from datetime import datetime
from unittest.mock import Mock

from backend.models.calendar import CalendarEvent, SyncFlow, GoogleAccount, MultiAccountConfig
from backend.services.google_calendar.sync_engine import CalendarSyncEngine
from backend.services.google_calendar.account_manager import AccountManager


class TestTransparencyLogic:
    """Test transparency (busy/free) logic in calendar synchronization."""
    
    # Type annotations for class attributes
    account1: GoogleAccount
    account2: GoogleAccount
    sync_flow: SyncFlow
    config: MultiAccountConfig
    account_manager: Mock
    mock_client: Mock
    sync_engine: CalendarSyncEngine
    
    def setup_method(self) -> None:
        """Setup test environment."""
        # Create test accounts
        self.account1 = GoogleAccount(
            account_id=1,
            name="Test Account 1",
            client_id="test_client_1",
            client_secret="test_secret_1", 
            refresh_token="test_token_1"
        )
        
        self.account2 = GoogleAccount(
            account_id=2,
            name="Test Account 2",
            client_id="test_client_2",
            client_secret="test_secret_2",
            refresh_token="test_token_2"
        )
        
        # Create test sync flow
        self.sync_flow = SyncFlow(
            name="Test Flow",
            source_account_id=1,
            source_calendar_id="source@test.com",
            target_account_id=2,
            target_calendar_id="target@test.com",
            start_offset=-15,
            end_offset=15
        )
        
        # Create config
        self.config = MultiAccountConfig(
            accounts=[self.account1, self.account2],
            sync_flows=[self.sync_flow],
            daily_sync_hour=6,
            daily_sync_timezone="UTC"
        )
        
        # Create mock account manager
        self.account_manager = Mock(spec=AccountManager)
        self.mock_client = Mock()
        self.account_manager.get_client.return_value = self.mock_client
        
        # Create sync engine
        self.sync_engine = CalendarSyncEngine(self.config, self.account_manager)
    
    def test_busy_event_creates_busy_block(self):
        """Test that busy (opaque) events create busy blocks."""
        # Create busy event
        event = CalendarEvent(
            id="test_event_1",
            calendar_id="source@test.com",
            account_id=1,
            title="Test Meeting",
            description="Test description",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            participants=["user1@test.com", "user2@test.com"],
            participant_count=2,
            status="confirmed",
            creator="user1@test.com",
            organizer="user1@test.com",
            transparency="opaque"  # busy
        )
        
        # Mock client methods
        self.mock_client.find_events_by_time_and_title.return_value = []
        self.mock_client.create_event.return_value = {}
        
        # Process event
        results = self.sync_engine.process_event(event)
        
        # Verify busy block was created
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action == 'created'
        assert results[0].reason is None
        
        # Verify create_event was called
        self.mock_client.create_event.assert_called_once()
    
    def test_free_event_skips_busy_block(self):
        """Test that free (transparent) events skip busy block creation."""
        # Create free event
        event = CalendarEvent(
            id="test_event_2",
            calendar_id="source@test.com",
            account_id=1,
            title="Test Meeting",
            description="Test description",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            participants=["user1@test.com", "user2@test.com"],
            participant_count=2,
            status="confirmed",
            creator="user1@test.com",
            organizer="user1@test.com",
            transparency="transparent"  # free
        )
        
        # Mock client methods
        self.mock_client.find_events_by_time_and_title.return_value = []
        
        # Process event
        results = self.sync_engine.process_event(event)
        
        # Verify busy block was skipped
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action == 'skipped'
        assert results[0].reason is not None
        assert "transparency: transparent" in results[0].reason
        
        # Verify create_event was not called
        self.mock_client.create_event.assert_not_called()
    
    def test_busy_to_free_deletes_busy_block(self):
        """Test that changing from busy to free deletes existing busy blocks."""
        # Create event that changed from busy to free
        event = CalendarEvent(
            id="test_event_3",
            calendar_id="source@test.com",
            account_id=1,
            title="Test Meeting",
            description="Test description",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            participants=["user1@test.com", "user2@test.com"],
            participant_count=2,
            status="confirmed",
            creator="user1@test.com",
            organizer="user1@test.com",
            transparency="transparent"  # now free
        )
        
        # Mock that busy block exists
        existing_block = {
            'id': 'existing_busy_block',
            'title': 'Busy',
            'start_time': datetime(2024, 1, 1, 9, 45),
            'end_time': datetime(2024, 1, 1, 11, 15)
        }
        self.mock_client.find_events_by_time_and_title.return_value = [existing_block]
        self.mock_client.delete_event.return_value = True
        
        # Process event
        results = self.sync_engine.process_event(event)
        
        # Verify busy block was deleted
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action == 'deleted'
        assert results[0].reason is not None
        assert "transparency: transparent" in results[0].reason
        
        # Verify delete_event was called
        self.mock_client.delete_event.assert_called_once()
        
        # Verify stats were updated
        assert self.sync_engine.stats['busy_blocks_deleted'] == 1
    
    def test_free_to_busy_creates_busy_block(self):
        """Test that changing from free to busy creates new busy blocks."""
        # Create event that changed from free to busy
        event = CalendarEvent(
            id="test_event_4",
            calendar_id="source@test.com",
            account_id=1,
            title="Test Meeting",
            description="Test description",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            participants=["user1@test.com", "user2@test.com"],
            participant_count=2,
            status="confirmed",
            creator="user1@test.com",
            organizer="user1@test.com",
            transparency="opaque"  # now busy
        )
        
        # Mock that no busy block exists
        self.mock_client.find_events_by_time_and_title.return_value = []
        self.mock_client.create_event.return_value = {}
        
        # Process event
        results = self.sync_engine.process_event(event)
        
        # Verify busy block was created
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action == 'created'
        assert results[0].reason is None
        
        # Verify create_event was called
        self.mock_client.create_event.assert_called_once()
        
        # Verify stats were updated
        assert self.sync_engine.stats['busy_blocks_created'] == 1
    
    def test_single_participant_free_event_skipped(self):
        """Test that free events with single participant are skipped."""
        # Create free event with single participant
        event = CalendarEvent(
            id="test_event_5",
            calendar_id="source@test.com",
            account_id=1,
            title="Test Meeting",
            description="Test description",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            participants=["user1@test.com"],
            participant_count=1,
            status="confirmed",
            creator="user1@test.com",
            organizer="user1@test.com",
            transparency="transparent"  # free
        )
        
        # Mock client methods (even though they shouldn't be called)
        self.mock_client.find_events_by_time_and_title.return_value = []
        
        # Process event
        results = self.sync_engine.process_event(event)
        
        # Verify event was skipped
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action == 'skipped'
        assert results[0].reason is not None
        assert "participants: 1" in results[0].reason
        
        # Verify no API calls were made
        self.mock_client.create_event.assert_not_called()
        self.mock_client.delete_event.assert_not_called()
    
    def test_cancelled_event_still_deletes_busy_block(self):
        """Test that cancelled events still delete busy blocks regardless of transparency."""
        # Create cancelled event
        event = CalendarEvent(
            id="test_event_6",
            calendar_id="source@test.com",
            account_id=1,
            title="Test Meeting",
            description="Test description",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            participants=["user1@test.com", "user2@test.com"],
            participant_count=2,
            status="cancelled",
            creator="user1@test.com",
            organizer="user1@test.com",
            transparency="opaque"  # busy but cancelled
        )
        
        # Mock that busy block exists
        existing_block = {
            'id': 'existing_busy_block',
            'title': 'Busy',
            'start_time': datetime(2024, 1, 1, 9, 45),
            'end_time': datetime(2024, 1, 1, 11, 15)
        }
        self.mock_client.find_events_by_time_and_title.return_value = [existing_block]
        self.mock_client.delete_event.return_value = True
        
        # Process event
        results = self.sync_engine.process_event(event)
        
        # Verify busy block was deleted
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action == 'deleted'
        assert results[0].reason is None
        
        # Verify delete_event was called
        self.mock_client.delete_event.assert_called_once()
        
        # Verify stats were updated
        assert self.sync_engine.stats['busy_blocks_deleted'] == 1
    
    def test_event_is_busy_method(self):
        """Test CalendarEvent.is_busy() method."""
        # Test busy event
        busy_event = CalendarEvent(
            id="test_event",
            calendar_id="test@test.com",
            account_id=1,
            title="Test",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            status="confirmed",
            transparency="opaque"
        )
        assert busy_event.is_busy() is True
        assert busy_event.is_free() is False
        
        # Test free event
        free_event = CalendarEvent(
            id="test_event",
            calendar_id="test@test.com",
            account_id=1,
            title="Test",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            status="confirmed",
            transparency="transparent"
        )
        assert free_event.is_busy() is False
        assert free_event.is_free() is True
        
        # Test default (opaque)
        default_event = CalendarEvent(
            id="test_event",
            calendar_id="test@test.com",
            account_id=1,
            title="Test",
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            status="confirmed"
        )
        assert default_event.is_busy() is True
        assert default_event.is_free() is False 