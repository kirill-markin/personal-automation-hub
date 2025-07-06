"""
Test covering busy block logic.

This module tests the logic for checking if existing busy blocks already cover
the required period for a new busy block, including proper handling of all-day events.
"""
# type: ignore

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from typing import Tuple

from backend.models.calendar import CalendarEvent, SyncFlow, GoogleAccount, MultiAccountConfig
from backend.services.google_calendar.sync_engine import CalendarSyncEngine
from backend.services.google_calendar.account_manager import AccountManager


@pytest.fixture
def mock_account_manager() -> Tuple[MagicMock, MagicMock]:
    """Mock account manager for testing."""
    account_manager = MagicMock(spec=AccountManager)
    mock_client = MagicMock()
    account_manager.get_client.return_value = mock_client
    return account_manager, mock_client


@pytest.fixture
def config() -> MultiAccountConfig:
    """Test configuration."""
    return MultiAccountConfig(
        accounts=[
            GoogleAccount(
                account_id=1,
                email="test@example.com",
                client_id="test_client_id",
                client_secret="test_client_secret",
                refresh_token="test_refresh_token"
            )
        ],
        sync_flows=[
            SyncFlow(
                name="Test Flow",
                source_account_id=1,
                source_calendar_id="source@example.com",
                target_account_id=1,
                target_calendar_id="target@example.com",
                start_offset=-15,  # 15 minutes before
                end_offset=15      # 15 minutes after
            )
        ]
    )


@pytest.fixture
def test_event() -> CalendarEvent:
    """Test calendar event."""
    return CalendarEvent(
        id="test_event_123",
        calendar_id="source@example.com",
        account_id=1,
        title="Test Meeting",
        start_time=datetime(2024, 1, 15, 10, 0),  # 10:00 AM
        end_time=datetime(2024, 1, 15, 11, 0),    # 11:00 AM
        participant_count=2,
        status="confirmed",
        transparency="opaque"
    )


@pytest.fixture
def sync_engine(config: MultiAccountConfig, mock_account_manager: Tuple[MagicMock, MagicMock]) -> CalendarSyncEngine:
    """Test sync engine."""
    account_manager, _ = mock_account_manager
    return CalendarSyncEngine(config, account_manager)


def test_no_covering_busy_block_creates_new_one(
    sync_engine: CalendarSyncEngine, 
    mock_account_manager: Tuple[MagicMock, MagicMock], 
    config: MultiAccountConfig, 
    test_event: CalendarEvent
) -> None:
    """Test that when no covering busy block exists, a new one is created."""
    _, mock_client = mock_account_manager
    
    # Mock: no exact match found
    mock_client.find_events_by_time_and_title.return_value = []  # type: ignore
    
    # Mock: no covering events found
    mock_client.get_events.return_value = []  # type: ignore
    
    # Process the event
    results = sync_engine.process_event(test_event)
    
    # Should create a new busy block
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].action == 'created'
    
    # Verify create_event was called
    mock_client.create_event.assert_called_once()  # type: ignore


def test_exact_matching_busy_block_prevents_creation(
    sync_engine: CalendarSyncEngine, 
    mock_account_manager: Tuple[MagicMock, MagicMock], 
    config: MultiAccountConfig, 
    test_event: CalendarEvent
) -> None:
    """Test that exact matching busy block prevents creation of new one."""
    _, mock_client = mock_account_manager
    
    # Mock: exact match found
    mock_client.find_events_by_time_and_title.return_value = [  # type: ignore
        {
            'id': 'existing_busy_block',
            'title': 'Busy',
            'start_time': datetime(2024, 1, 15, 9, 45),   # 9:45 AM (15 min before)
            'end_time': datetime(2024, 1, 15, 11, 15),    # 11:15 AM (15 min after)
            'all_day': False
        }
    ]
    
    # Process the event
    results = sync_engine.process_event(test_event)
    
    # Should not create a new busy block
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].action == 'existed'
    
    # Verify create_event was not called
    mock_client.create_event.assert_not_called()  # type: ignore


def test_regular_covering_busy_block_prevents_creation(
    sync_engine: CalendarSyncEngine, 
    mock_account_manager: Tuple[MagicMock, MagicMock], 
    config: MultiAccountConfig, 
    test_event: CalendarEvent
) -> None:
    """Test that regular (non-all-day) covering busy block prevents creation."""
    _, mock_client = mock_account_manager
    
    # Mock: no exact match found
    mock_client.find_events_by_time_and_title.return_value = []  # type: ignore
    
    # Mock: covering busy block found (longer than needed)
    mock_client.get_events.return_value = [  # type: ignore
        {
            'id': 'covering_busy_block',
            'title': 'Busy',
            'start_time': datetime(2024, 1, 15, 9, 30),   # 9:30 AM (earlier than needed)
            'end_time': datetime(2024, 1, 15, 11, 30),    # 11:30 AM (later than needed)
            'all_day': False
        }
    ]
    
    # Process the event
    results = sync_engine.process_event(test_event)
    
    # Should not create a new busy block
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].action == 'existed'
    
    # Verify create_event was not called
    mock_client.create_event.assert_not_called()  # type: ignore


def test_all_day_covering_busy_block_still_creates_new_one(
    sync_engine: CalendarSyncEngine, 
    mock_account_manager: Tuple[MagicMock, MagicMock], 
    config: MultiAccountConfig, 
    test_event: CalendarEvent
) -> None:
    """Test that all-day covering busy block is ignored and new one is still created."""
    _, mock_client = mock_account_manager
    
    # Mock: no exact match found
    mock_client.find_events_by_time_and_title.return_value = []  # type: ignore
    
    # Mock: all-day busy block found that covers the period
    mock_client.get_events.return_value = [  # type: ignore
        {
            'id': 'all_day_busy_block',
            'title': 'Busy',
            'start_time': datetime(2024, 1, 15, 0, 0),    # Start of day
            'end_time': datetime(2024, 1, 15, 23, 59),    # End of day
            'all_day': True
        }
    ]
    
    # Process the event
    results = sync_engine.process_event(test_event)
    
    # Should create a new busy block (ignoring all-day coverage)
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].action == 'created'
    
    # Verify create_event was called
    mock_client.create_event.assert_called_once()  # type: ignore


def test_partially_covering_busy_block_creates_new_one(
    sync_engine: CalendarSyncEngine, 
    mock_account_manager: Tuple[MagicMock, MagicMock], 
    config: MultiAccountConfig, 
    test_event: CalendarEvent
) -> None:
    """Test that partially covering busy block allows creation of new one."""
    _, mock_client = mock_account_manager
    
    # Mock: no exact match found
    mock_client.find_events_by_time_and_title.return_value = []  # type: ignore
    
    # Mock: partially covering busy block found (doesn't fully cover)
    mock_client.get_events.return_value = [  # type: ignore
        {
            'id': 'partial_busy_block',
            'title': 'Busy',
            'start_time': datetime(2024, 1, 15, 9, 45),   # 9:45 AM (covers start)
            'end_time': datetime(2024, 1, 15, 11, 0),     # 11:00 AM (doesn't cover end)
            'all_day': False
        }
    ]
    
    # Process the event
    results = sync_engine.process_event(test_event)
    
    # Should create a new busy block
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].action == 'created'
    
    # Verify create_event was called
    mock_client.create_event.assert_called_once()  # type: ignore


def test_mixed_events_with_all_day_and_regular_coverage(
    sync_engine: CalendarSyncEngine, 
    mock_account_manager: Tuple[MagicMock, MagicMock], 
    config: MultiAccountConfig, 
    test_event: CalendarEvent
) -> None:
    """Test scenario with both all-day events and regular events, where regular event covers."""
    _, mock_client = mock_account_manager
    
    # Mock: no exact match found
    mock_client.find_events_by_time_and_title.return_value = []  # type: ignore
    
    # Mock: mixed events - all-day (should be ignored) and regular covering event
    mock_client.get_events.return_value = [  # type: ignore
        {
            'id': 'all_day_busy_block',
            'title': 'Busy',
            'start_time': datetime(2024, 1, 15, 0, 0),
            'end_time': datetime(2024, 1, 15, 23, 59),
            'all_day': True
        },
        {
            'id': 'regular_covering_busy_block',
            'title': 'Busy',
            'start_time': datetime(2024, 1, 15, 9, 0),    # 9:00 AM (covers start)
            'end_time': datetime(2024, 1, 15, 12, 0),     # 12:00 PM (covers end)
            'all_day': False
        }
    ]
    
    # Process the event
    results = sync_engine.process_event(test_event)
    
    # Should not create a new busy block (regular event covers, all-day is ignored)
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].action == 'existed'
    
    # Verify create_event was not called
    mock_client.create_event.assert_not_called()  # type: ignore


def test_different_title_events_do_not_prevent_creation(
    sync_engine: CalendarSyncEngine, 
    mock_account_manager: Tuple[MagicMock, MagicMock], 
    config: MultiAccountConfig, 
    test_event: CalendarEvent
) -> None:
    """Test that events with different titles don't prevent busy block creation."""
    _, mock_client = mock_account_manager
    
    # Mock: no exact match found
    mock_client.find_events_by_time_and_title.return_value = []  # type: ignore
    
    # Mock: events with different titles that would cover the period
    mock_client.get_events.return_value = [  # type: ignore
        {
            'id': 'other_event',
            'title': 'Different Title',  # Different title, should be ignored
            'start_time': datetime(2024, 1, 15, 9, 0),
            'end_time': datetime(2024, 1, 15, 12, 0),
            'all_day': False
        }
    ]
    
    # Process the event
    results = sync_engine.process_event(test_event)
    
    # Should create a new busy block
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].action == 'created'
    
    # Verify create_event was called
    mock_client.create_event.assert_called_once()  # type: ignore


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 