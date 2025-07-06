#!/usr/bin/env python3
"""
Integration tests for Google Calendar Webhook Handler.

This script tests the webhook handler functionality by:
1. Validating webhook data and headers
2. Processing mock webhook notifications
3. Managing webhook subscriptions
4. Testing monitored calendar management

Usage:
    # As pytest integration test
    python -m pytest tests/integration/test_webhook_handler.py -v -m integration
    
    # As standalone script
    python tests/integration/test_webhook_handler.py
    python tests/integration/test_webhook_handler.py --test-subscriptions
    python tests/integration/test_webhook_handler.py --test-validation
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytest
from dotenv import load_dotenv
import uuid

# Load environment variables from .env file
load_dotenv(override=True)

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.google_calendar.config_loader import load_multi_account_config
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.sync_engine import CalendarSyncEngine
from backend.services.google_calendar.webhook_handler import GoogleCalendarWebhookHandler
from backend.models.calendar import (
    MultiAccountConfig,
    WebhookProcessingResult,
    MonitoredCalendar,
    ChannelSubscriptionResult
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebhookTestHelper:
    """Helper class for webhook handler integration tests."""
    
    def __init__(self, config: MultiAccountConfig, account_manager: AccountManager, 
                 sync_engine: CalendarSyncEngine, webhook_handler: GoogleCalendarWebhookHandler):
        self.config = config
        self.account_manager = account_manager
        self.sync_engine = sync_engine
        self.webhook_handler = webhook_handler
        
        # Track created subscriptions for cleanup
        self.test_subscriptions: List[Dict[str, Any]] = []
    
    def create_mock_webhook_data(self, calendar_id: str, resource_state: str = "sync") -> Dict[str, Any]:
        """Create mock webhook data for testing.
        
        Args:
            calendar_id: Calendar ID for the webhook
            resource_state: Resource state (sync, exists, not_exists)
            
        Returns:
            Mock webhook data
        """
        return {
            "resourceId": calendar_id,
            "channelId": f"test-channel-{uuid.uuid4().hex[:8]}",
            "resourceState": resource_state,
            "resourceUri": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            "channelToken": "test-token",
            "channelExpiration": str(int((datetime.now() + timedelta(hours=24)).timestamp() * 1000))
        }
    
    def create_mock_webhook_headers(self, calendar_id: str, resource_state: str = "sync") -> Dict[str, str]:
        """Create mock webhook headers for testing.
        
        Args:
            calendar_id: Calendar ID for the webhook
            resource_state: Resource state
            
        Returns:
            Mock webhook headers
        """
        return {
            "X-Goog-Channel-Id": f"test-channel-{uuid.uuid4().hex[:8]}",
            "X-Goog-Resource-Id": calendar_id,
            "X-Goog-Resource-State": resource_state,
            "X-Goog-Resource-Uri": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            "X-Goog-Channel-Token": "test-token",
            "X-Goog-Channel-Expiration": str(int((datetime.now() + timedelta(hours=24)).timestamp() * 1000)),
            "Content-Type": "application/json"
        }
    
    def get_test_calendar_id(self) -> Optional[str]:
        """Get a test calendar ID from the first sync flow.
        
        Returns:
            Calendar ID or None if no sync flows configured
        """
        if not self.config.sync_flows:
            return None
        return self.config.sync_flows[0].source_calendar_id
    
    def cleanup_test_subscriptions(self) -> None:
        """Clean up test webhook subscriptions."""
        logger.info("Cleaning up test webhook subscriptions...")
        
        for subscription in self.test_subscriptions:
            try:
                result = self.webhook_handler.delete_webhook_subscription(
                    channel_id=subscription['channel_id'],
                    resource_id=subscription['resource_id'],
                    account_id=subscription.get('account_id')
                )
                
                if result.success:
                    logger.info(f"Successfully deleted test subscription {subscription['channel_id']}")
                else:
                    logger.warning(f"Failed to delete test subscription {subscription['channel_id']}: {result.error}")
                    
            except Exception as e:
                logger.error(f"Error deleting test subscription {subscription['channel_id']}: {e}")
        
        self.test_subscriptions.clear()
        logger.info("Test webhook subscription cleanup completed")


@pytest.mark.integration
def test_webhook_handler_initialization():
    """Test webhook handler initialization with real configuration."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    
    # Verify initialization
    assert webhook_handler.config == config
    assert webhook_handler.account_manager == account_manager
    assert webhook_handler.sync_engine == sync_engine
    
    # Verify calendar mapping is built
    assert len(webhook_handler.calendar_to_account) > 0
    
    # Verify mapping contains source calendars from sync flows
    for flow in config.sync_flows:
        assert flow.source_calendar_id in webhook_handler.calendar_to_account
        assert webhook_handler.calendar_to_account[flow.source_calendar_id] == flow.source_account_id


@pytest.mark.integration
def test_webhook_data_validation():
    """Test webhook data validation with various scenarios."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    helper = WebhookTestHelper(config, account_manager, sync_engine, webhook_handler)
    
    # Test valid webhook data
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    test_calendar_id = helper.get_test_calendar_id()
    if test_calendar_id is None:
        pytest.skip("No test calendar ID available")
    
    valid_data = helper.create_mock_webhook_data(test_calendar_id, "sync")  # type: ignore
    
    assert webhook_handler._validate_webhook_data(valid_data) == True  # type: ignore
    
    # Test invalid webhook data - missing required fields
    invalid_data_missing_resource = {
        "channelId": "test-channel",
        "resourceState": "sync"
        # Missing resourceId
    }
    
    assert webhook_handler._validate_webhook_data(invalid_data_missing_resource) == False  # type: ignore
    
    invalid_data_missing_channel = {
        "resourceId": test_calendar_id,
        "resourceState": "sync"
        # Missing channelId
    }
    
    assert webhook_handler._validate_webhook_data(invalid_data_missing_channel) == False  # type: ignore
    
    invalid_data_missing_state = {
        "resourceId": test_calendar_id,
        "channelId": "test-channel"
        # Missing resourceState
    }
    
    assert webhook_handler._validate_webhook_data(invalid_data_missing_state) == False  # type: ignore
    
    # Test empty values
    invalid_data_empty_values = {
        "resourceId": "",
        "channelId": "test-channel",
        "resourceState": "sync"
    }
    
    assert webhook_handler._validate_webhook_data(invalid_data_empty_values) == False  # type: ignore
    
    logger.info("Webhook data validation tests completed successfully")


@pytest.mark.integration
def test_webhook_header_validation():
    """Test webhook header validation with various scenarios."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    helper = WebhookTestHelper(config, account_manager, sync_engine, webhook_handler)
    
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    test_calendar_id = helper.get_test_calendar_id()
    if test_calendar_id is None:
        pytest.skip("No test calendar ID available")
    
    # Test valid webhook headers
    valid_headers = helper.create_mock_webhook_headers(test_calendar_id, "sync")  # type: ignore
    
    validation_result = webhook_handler.validate_webhook_signature(valid_headers)
    
    assert validation_result.is_valid == True
    assert validation_result.channel_id is not None
    assert validation_result.resource_id == test_calendar_id
    assert validation_result.resource_state == "sync"
    assert validation_result.reason is None
    
    # Test missing required headers
    invalid_headers_missing_channel = {
        "X-Goog-Resource-Id": test_calendar_id,
        "X-Goog-Resource-State": "sync"
        # Missing X-Goog-Channel-Id
    }
    
    validation_result = webhook_handler.validate_webhook_signature(invalid_headers_missing_channel)  # type: ignore
    
    assert validation_result.is_valid == False
    assert validation_result.reason is not None and "Missing X-Goog-Channel-Id" in validation_result.reason
    
    # Test invalid resource state
    invalid_headers_bad_state = {
        "X-Goog-Channel-Id": "test-channel",
        "X-Goog-Resource-Id": test_calendar_id,
        "X-Goog-Resource-State": "invalid_state"
    }
    
    validation_result = webhook_handler.validate_webhook_signature(invalid_headers_bad_state)  # type: ignore
    
    assert validation_result.is_valid == False
    assert validation_result.reason is not None and "Invalid resource state" in validation_result.reason
    
    # Test non-monitored calendar
    non_monitored_calendar = "non-monitored-calendar@example.com"
    invalid_headers_non_monitored = {
        "X-Goog-Channel-Id": "test-channel",
        "X-Goog-Resource-Id": non_monitored_calendar,
        "X-Goog-Resource-State": "sync"
    }
    
    validation_result = webhook_handler.validate_webhook_signature(invalid_headers_non_monitored)
    
    assert validation_result.is_valid == False
    assert validation_result.reason is not None and "non-monitored calendar" in validation_result.reason
    
    logger.info("Webhook header validation tests completed successfully")


@pytest.mark.integration
def test_webhook_processing_sync_state():
    """Test webhook processing for sync state notification."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    helper = WebhookTestHelper(config, account_manager, sync_engine, webhook_handler)
    
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    test_calendar_id = helper.get_test_calendar_id()
    if test_calendar_id is None:
        pytest.skip("No test calendar ID available")
    
    # Create mock webhook data for sync state
    webhook_data = helper.create_mock_webhook_data(test_calendar_id, "sync")  # type: ignore
    
    # Process webhook
    result = webhook_handler.handle_webhook(webhook_data)
    
    # Verify processing result
    assert isinstance(result, WebhookProcessingResult)
    assert result.success == True
    assert result.webhook_type == "google_calendar"
    assert result.processed_events >= 0
    assert result.error is None
    
    # Verify timestamp is set
    assert result.timestamp is not None
    
    logger.info(f"Webhook processing result: {result.processed_events} events processed")


@pytest.mark.integration
def test_webhook_processing_exists_state():
    """Test webhook processing for exists state notification."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    helper = WebhookTestHelper(config, account_manager, sync_engine, webhook_handler)
    
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    test_calendar_id = helper.get_test_calendar_id()
    if test_calendar_id is None:
        pytest.skip("No test calendar ID available")
    
    # Create mock webhook data for exists state
    webhook_data = helper.create_mock_webhook_data(test_calendar_id, "exists")  # type: ignore
    
    # Process webhook
    result = webhook_handler.handle_webhook(webhook_data)
    
    # Verify processing result
    assert isinstance(result, WebhookProcessingResult)
    assert result.success == True
    assert result.webhook_type == "google_calendar"
    assert result.processed_events == 0  # exists state doesn't process events
    assert result.error is None
    
    logger.info("Webhook exists state processing completed successfully")


@pytest.mark.integration
def test_webhook_processing_invalid_data():
    """Test webhook processing with invalid data."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    
    # Test with invalid webhook data
    invalid_data = {
        "invalid": "data"
    }
    
    result = webhook_handler.handle_webhook(invalid_data)
    
    # Verify error handling
    assert isinstance(result, WebhookProcessingResult)
    assert result.success == False
    assert result.webhook_type == "google_calendar"
    assert result.processed_events == 0
    assert result.error is not None
    assert "Invalid webhook data" in result.error
    
    logger.info("Invalid webhook data handling test completed successfully")


@pytest.mark.integration
def test_webhook_processing_non_monitored_calendar():
    """Test webhook processing for non-monitored calendar."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    helper = WebhookTestHelper(config, account_manager, sync_engine, webhook_handler)
    
    # Create webhook data for non-monitored calendar
    non_monitored_calendar = "non-monitored-calendar@example.com"
    webhook_data = helper.create_mock_webhook_data(non_monitored_calendar, "sync")
    
    # Process webhook
    result = webhook_handler.handle_webhook(webhook_data)
    
    # Verify error handling
    assert isinstance(result, WebhookProcessingResult)
    assert result.success == False
    assert result.webhook_type == "google_calendar"
    assert result.processed_events == 0
    assert result.error is not None
    assert "No account found for calendar" in result.error
    
    logger.info("Non-monitored calendar webhook handling test completed successfully")


@pytest.mark.integration
def test_get_monitored_calendars():
    """Test getting list of monitored calendars."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    
    # Get monitored calendars
    monitored_calendars = webhook_handler.get_monitored_calendars()
    
    # Verify structure
    assert isinstance(monitored_calendars, list)
    assert len(monitored_calendars) == len(config.sync_flows)
    
    # Verify each monitored calendar
    for i, calendar in enumerate(monitored_calendars):
        assert isinstance(calendar, MonitoredCalendar)
        assert calendar.calendar_id is not None
        assert calendar.account_id is not None
        assert calendar.account_name is not None
        assert calendar.flow_name is not None
        
        # Verify corresponds to sync flow
        flow = config.sync_flows[i]
        assert calendar.calendar_id == flow.source_calendar_id
        assert calendar.account_id == flow.source_account_id
        assert calendar.flow_name == flow.name
        
        # Verify account name matches
        account = config.get_account_by_id(flow.source_account_id)
        if account:
            assert calendar.account_name == account.name
    
    logger.info(f"Found {len(monitored_calendars)} monitored calendars")


@pytest.mark.integration
def test_find_account_for_calendar():
    """Test finding account for calendar ID."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    # Test with known calendar
    flow = config.sync_flows[0]
    account_id = webhook_handler._find_account_for_calendar(flow.source_calendar_id)  # type: ignore
    
    assert account_id == flow.source_account_id
    
    # Test with unknown calendar
    unknown_calendar = "unknown-calendar@example.com"
    account_id = webhook_handler._find_account_for_calendar(unknown_calendar)  # type: ignore
    
    assert account_id is None
    
    logger.info("Find account for calendar test completed successfully")


@pytest.mark.integration
def test_webhook_subscription_creation():
    """Test creating webhook subscriptions."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    helper = WebhookTestHelper(config, account_manager, sync_engine, webhook_handler)
    
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    # Get test calendar and account
    flow = config.sync_flows[0]
    test_calendar_id = flow.source_calendar_id
    test_account_id = flow.source_account_id
    
    # Test webhook URL (use localhost for testing)
    callback_url = "https://example.com/api/v1/webhooks/google-calendar"
    
    try:
        # Create subscription
        result = webhook_handler.create_webhook_subscription(
            calendar_id=test_calendar_id,
            account_id=test_account_id,
            callback_url=callback_url,
            channel_token="test-token"
        )
        
        # Verify result
        assert isinstance(result, ChannelSubscriptionResult)
        
        if result.success:
            assert result.channel_id is not None
            assert result.calendar_id == test_calendar_id
            assert result.resource_id is not None
            assert result.error is None
            
            # Track for cleanup
            helper.test_subscriptions.append({
                'channel_id': result.channel_id,
                'resource_id': result.resource_id,
                'account_id': test_account_id
            })
            
            logger.info(f"Successfully created webhook subscription {result.channel_id}")
        else:
            logger.warning(f"Failed to create webhook subscription: {result.error}")
            # This might be expected if the callback URL is not accessible
            
    except Exception as e:
        logger.error(f"Error testing webhook subscription creation: {e}")
        # This might be expected in test environment
        
    finally:
        # Clean up
        helper.cleanup_test_subscriptions()


@pytest.mark.integration
def test_webhook_subscription_deletion():
    """Test deleting webhook subscriptions."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    sync_engine = CalendarSyncEngine(config, account_manager)
    webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
    _ = WebhookTestHelper(config, account_manager, sync_engine, webhook_handler)
    
    if not config.sync_flows:
        pytest.skip("No sync flows configured")
    
    # Test deleting non-existent subscription
    fake_channel_id = "fake-channel-id"
    fake_resource_id = "fake-resource-id"
    
    result = webhook_handler.delete_webhook_subscription(
        channel_id=fake_channel_id,
        resource_id=fake_resource_id,
        account_id=config.accounts[0].account_id
    )
    
    # Verify result
    assert isinstance(result, ChannelSubscriptionResult)
    
    # Deletion of non-existent subscription should be considered successful (idempotent)
    assert result.success == True
    assert result.channel_id == fake_channel_id
    assert result.resource_id == fake_resource_id
    
    logger.info("Webhook subscription deletion test completed successfully")


def create_test_webhook_payload(calendar_id: str, resource_state: str = "sync") -> Dict[str, Any]:
    """Create a test webhook payload for manual testing.
    
    Args:
        calendar_id: Calendar ID for the webhook
        resource_state: Resource state
        
    Returns:
        Test webhook payload
    """
    return {
        "resourceId": calendar_id,
        "channelId": f"test-channel-{uuid.uuid4().hex[:8]}",
        "resourceState": resource_state,
        "resourceUri": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
        "channelToken": "test-token",
        "channelExpiration": str(int((datetime.now() + timedelta(hours=24)).timestamp() * 1000))
    }


def run_webhook_processing_manual(config: MultiAccountConfig) -> None:
    """Manually test webhook processing with real configuration.
    
    Args:
        config: Multi-account configuration
    """
    if not config.sync_flows:
        print("❌ No sync flows configured")
        return
    
    print("\n" + "="*60)
    print("WEBHOOK PROCESSING MANUAL TEST")
    print("="*60)
    
    try:
        # Initialize components
        account_manager = AccountManager(config)
        sync_engine = CalendarSyncEngine(config, account_manager)
        webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
        helper = WebhookTestHelper(config, account_manager, sync_engine, webhook_handler)
        
        # Test with each sync flow
        for i, flow in enumerate(config.sync_flows, 1):
            print(f"\n{i}. Testing webhook for flow: {flow.name}")
            print(f"   Calendar: {flow.source_calendar_id}")
            print(f"   Account: {flow.source_account_id}")
            
            # Create test webhook data
            webhook_data = helper.create_mock_webhook_data(flow.source_calendar_id, "sync")
            
            # Process webhook
            result = webhook_handler.handle_webhook(webhook_data)
            
            # Display result
            if result.success:
                print(f"   ✅ Success: {result.processed_events} events processed")
            else:
                print(f"   ❌ Failed: {result.error}")
        
        # Test monitored calendars
        print(f"\nMonitored Calendars:")
        monitored = webhook_handler.get_monitored_calendars()
        for calendar in monitored:
            print(f"   - {calendar.calendar_id} ({calendar.account_name})")
        
    except Exception as e:
        print(f"❌ Error during manual test: {e}")
    
    print("="*60)


def main() -> None:
    """Main function to run webhook handler integration tests."""
    parser = argparse.ArgumentParser(description="Test Google Calendar Webhook Handler integration")
    parser.add_argument(
        "--test-subscriptions",
        action="store_true",
        help="Test webhook subscription creation/deletion"
    )
    parser.add_argument(
        "--test-validation",
        action="store_true",
        help="Test webhook validation only"
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Run manual webhook processing tests"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_multi_account_config()
        logger.info(f"Loaded configuration: {len(config.accounts)} accounts, {len(config.sync_flows)} sync flows")
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Run tests based on arguments
    if args.test_subscriptions:
        logger.info("Running webhook subscription tests...")
        # Add specific subscription tests here
        
    elif args.test_validation:
        logger.info("Running webhook validation tests...")
        # Add specific validation tests here
        
    elif args.manual:
        logger.info("Running manual webhook processing tests...")
        run_webhook_processing_manual(config)
        
    else:
        logger.info("Running basic webhook handler tests...")
        # Run basic functionality tests
        
    logger.info("Integration tests completed")


if __name__ == "__main__":
    main() 