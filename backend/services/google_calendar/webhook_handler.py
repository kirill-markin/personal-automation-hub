"""
Google Calendar webhook handler.

This module handles incoming Google Calendar webhook notifications,
validates them, and processes calendar events through the sync engine.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from backend.models.calendar import (
    MultiAccountConfig,
    WebhookProcessingResult,
    MonitoredCalendar,
    CalendarSyncResult,
    WebhookSubscription
)
from backend.services.google_calendar.sync_engine import CalendarSyncEngine
from backend.services.google_calendar.account_manager import AccountManager

logger = logging.getLogger(__name__)


class WebhookHandlerError(Exception):
    """Exception raised when webhook handling fails."""
    pass


class GoogleCalendarWebhookHandler:
    """Handles Google Calendar webhook notifications and processes events."""
    
    def __init__(self, config: MultiAccountConfig, account_manager: AccountManager, sync_engine: CalendarSyncEngine) -> None:
        """Initialize webhook handler.
        
        Args:
            config: Multi-account configuration
            account_manager: Account manager for accessing Google Calendar clients
            sync_engine: Sync engine for processing events
        """
        self.config = config
        self.account_manager = account_manager
        self.sync_engine = sync_engine
        
        # Build calendar to account mapping for faster lookups
        self.calendar_to_account: Dict[str, int] = {}
        for flow in config.sync_flows:
            self.calendar_to_account[flow.source_calendar_id] = flow.source_account_id
        
        logger.info(f"Initialized webhook handler for {len(config.sync_flows)} sync flows")
    
    def handle_webhook(self, webhook_data: Dict[str, Any]) -> WebhookProcessingResult:
        """Handle incoming Google Calendar webhook notification.
        
        Args:
            webhook_data: Webhook payload from Google Calendar
            
        Returns:
            Processing result
        """
        timestamp = datetime.now().isoformat()
        
        try:
            # Validate webhook data
            if not self._validate_webhook_data(webhook_data):
                return WebhookProcessingResult(
                    success=False,
                    webhook_type='google_calendar',
                    timestamp=timestamp,
                    processed_events=0,
                    results=[],
                    error='Invalid webhook data format'
                )
            
            # Extract calendar information
            calendar_id = webhook_data.get('resourceId', '')
            channel_id = webhook_data.get('channelId', '')
            resource_state = webhook_data.get('resourceState', '')
            
            logger.info(f"Processing webhook for calendar {calendar_id}, channel {channel_id}, state {resource_state}")
            
            # Find the account for this calendar
            account_id = self._find_account_for_calendar(calendar_id)
            if account_id is None:
                return WebhookProcessingResult(
                    success=False,
                    webhook_type='google_calendar',
                    timestamp=timestamp,
                    processed_events=0,
                    results=[],
                    error=f'No account found for calendar {calendar_id}'
                )
            
            # Process based on resource state
            if resource_state in ['sync', 'update']:
                # Fetch and process recent events
                events_result = self._fetch_and_process_recent_events(calendar_id, account_id)
                return WebhookProcessingResult(
                    success=True,
                    webhook_type='google_calendar',
                    timestamp=timestamp,
                    processed_events=events_result.events_processed,
                    results=events_result.results,
                    error=events_result.error
                )
            
            elif resource_state == 'exists':
                # Initial sync notification - can be ignored or used for status
                logger.info(f"Received 'exists' notification for calendar {calendar_id}")
                return WebhookProcessingResult(
                    success=True,
                    webhook_type='google_calendar',
                    timestamp=timestamp,
                    processed_events=0,
                    results=[],
                    error=None
                )
            
            else:
                logger.warning(f"Unknown resource state: {resource_state}")
                return WebhookProcessingResult(
                    success=False,
                    webhook_type='google_calendar',
                    timestamp=timestamp,
                    processed_events=0,
                    results=[],
                    error=f'Unknown resource state: {resource_state}'
                )
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return WebhookProcessingResult(
                success=False,
                webhook_type='google_calendar',
                timestamp=timestamp,
                processed_events=0,
                results=[],
                error=str(e)
            )
    
    def _validate_webhook_data(self, webhook_data: Dict[str, Any]) -> bool:
        """Validate webhook data format.
        
        Args:
            webhook_data: Webhook payload to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['resourceId', 'channelId', 'resourceState']
        
        for field in required_fields:
            if field not in webhook_data or not webhook_data[field]:
                logger.warning(f"Missing required webhook field: {field}")
                return False
        
        return True
    
    def _find_account_for_calendar(self, calendar_id: str) -> Optional[int]:
        """Find the account ID for a given calendar ID.
        
        Args:
            calendar_id: Calendar ID to find account for
            
        Returns:
            Account ID or None if not found
        """
        return self.calendar_to_account.get(calendar_id)
    
    def _fetch_and_process_recent_events(self, calendar_id: str, account_id: int) -> CalendarSyncResult:
        """Fetch and process recent events from a calendar.
        
        Args:
            calendar_id: Calendar ID to fetch events from
            account_id: Account ID for the calendar
            
        Returns:
            Processing results
        """
        
        # Get recent events (last 24 hours to next 7 days)
        now = datetime.now()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)  # Start of today
        end_time = start_time.replace(hour=23, minute=59, second=59, microsecond=999999)  # End of today
        
        # Extend range to catch events that might be modified
        start_time = start_time - timedelta(days=1)
        end_time = end_time + timedelta(days=7)
        
        # Use sync engine to fetch and process events
        return self.sync_engine.sync_calendar_events(
            calendar_id=calendar_id,
            account_id=account_id,
            start_date=start_time,
            end_date=end_time,
            sync_type="webhook"
        )
    
    def get_monitored_calendars(self) -> List[MonitoredCalendar]:
        """Get list of calendars being monitored by webhooks.
        
        Returns:
            List of monitored calendar information
        """
        monitored: List[MonitoredCalendar] = []
        
        for flow in self.config.sync_flows:
            account = self.config.get_account_by_id(flow.source_account_id)
            if account:
                monitored.append(MonitoredCalendar(
                    calendar_id=flow.source_calendar_id,
                    account_id=flow.source_account_id,
                    account_name=account.name,
                    flow_name=flow.name
                ))
        
        return monitored
    
    def validate_webhook_signature(self, webhook_data: Dict[str, Any], signature: str) -> bool:
        """Validate webhook signature from Google Calendar.
        
        Args:
            webhook_data: Webhook payload
            signature: Signature from Google Calendar
            
        Returns:
            True if signature is valid, False otherwise
            
        Note:
            This is a placeholder for Google Calendar webhook signature validation.
            In production, you should implement proper signature validation.
        """
        # TODO: Implement proper Google Calendar webhook signature validation
        # For now, we'll just log the attempt
        logger.debug(f"Webhook signature validation requested (not implemented): {signature}")
        return True
    
    def create_webhook_subscription(self, calendar_id: str, account_id: int, callback_url: str) -> WebhookSubscription:
        """Create a webhook subscription for a calendar.
        
        Args:
            calendar_id: Calendar ID to subscribe to
            account_id: Account ID for the calendar
            callback_url: URL to receive webhook notifications
            
        Returns:
            Subscription result
        """
        try:
            # Get calendar client
            client = self.account_manager.get_client(account_id)
            
            # TODO: Implement actual Google Calendar webhook subscription
            # This would use the Google Calendar API to create a push notification channel
            # For now, we'll just log the attempt
            logger.info(f"Creating webhook subscription for calendar {calendar_id} at {callback_url}")
            
            return WebhookSubscription(
                success=True,
                calendar_id=calendar_id,
                account_id=account_id,
                callback_url=callback_url,
                channel_id=f"channel_{calendar_id}_{account_id}",
                resource_id=f"resource_{calendar_id}",
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error creating webhook subscription for calendar {calendar_id}: {e}")
            return WebhookSubscription(
                success=False,
                calendar_id=calendar_id,
                account_id=account_id,
                callback_url=callback_url,
                channel_id=None,
                resource_id=None,
                error=str(e)
            )
    
    def delete_webhook_subscription(self, channel_id: str, resource_id: str) -> WebhookSubscription:
        """Delete a webhook subscription.
        
        Args:
            channel_id: Channel ID to delete
            resource_id: Resource ID for the subscription
            
        Returns:
            Deletion result
        """
        try:
            # TODO: Implement actual Google Calendar webhook subscription deletion
            # This would use the Google Calendar API to stop the push notification channel
            logger.info(f"Deleting webhook subscription {channel_id} for resource {resource_id}")
            
            return WebhookSubscription(
                success=True,
                calendar_id="",  # Not applicable for deletion
                account_id=0,    # Not applicable for deletion
                callback_url="", # Not applicable for deletion
                channel_id=channel_id,
                resource_id=resource_id,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error deleting webhook subscription {channel_id}: {e}")
            return WebhookSubscription(
                success=False,
                calendar_id="",  # Not applicable for deletion
                account_id=0,    # Not applicable for deletion
                callback_url="", # Not applicable for deletion
                channel_id=channel_id,
                resource_id=resource_id,
                error=str(e)
            ) 