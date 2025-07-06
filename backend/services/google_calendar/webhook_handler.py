"""
Google Calendar webhook handler.

This module handles incoming Google Calendar webhook notifications,
validates them, and processes calendar events through the sync engine.
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from backend.models.calendar import (
    MultiAccountConfig,
    WebhookProcessingResult,
    MonitoredCalendar,
    CalendarSyncResult,
    WebhookHeaders,
    WebhookValidationResult,
    ChannelSubscriptionResult
)
from backend.services.google_calendar.sync_engine import CalendarSyncEngine
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.client import GoogleCalendarError

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
                    account_email=account.email,
                    flow_name=flow.name
                ))
        
        return monitored
    
    def validate_webhook_signature(self, headers: Dict[str, str], webhook_data: Optional[Dict[str, Any]] = None) -> WebhookValidationResult:
        """Validate webhook headers and data from Google Calendar.
        
        Args:
            headers: HTTP request headers from webhook
            webhook_data: Optional webhook payload data
            
        Returns:
            WebhookValidationResult with validation status and details
            
        Note:
            Google Calendar webhooks use header-based validation rather than HMAC signatures.
            We validate the required headers and check if the channel/resource IDs match our subscriptions.
        """
        try:
            # Parse headers into typed structure
            webhook_headers = WebhookHeaders.from_request_headers(headers)
            
            # Validate required headers are present
            if not webhook_headers.x_goog_channel_id:
                return WebhookValidationResult(
                    is_valid=False,
                    reason="Missing X-Goog-Channel-Id header",
                    channel_id=None,
                    resource_id=None,
                    resource_state=None
                )
            
            if not webhook_headers.x_goog_resource_id:
                return WebhookValidationResult(
                    is_valid=False,
                    reason="Missing X-Goog-Resource-Id header",
                    channel_id=None,
                    resource_id=None,
                    resource_state=None
                )
            
            if not webhook_headers.x_goog_resource_state:
                return WebhookValidationResult(
                    is_valid=False,
                    reason="Missing X-Goog-Resource-State header",
                    channel_id=None,
                    resource_id=None,
                    resource_state=None
                )
            
            # Validate resource state is valid
            valid_states = ['sync', 'exists', 'not_exists']
            if webhook_headers.x_goog_resource_state not in valid_states:
                return WebhookValidationResult(
                    is_valid=False,
                    reason=f"Invalid resource state: {webhook_headers.x_goog_resource_state}",
                    channel_id=None,
                    resource_id=None,
                    resource_state=None
                )
            
            # Check if we have a subscription for this channel/resource
            calendar_id = webhook_headers.x_goog_resource_id
            if not self._is_monitored_calendar(calendar_id):
                return WebhookValidationResult(
                    is_valid=False,
                    reason=f"Webhook for non-monitored calendar: {calendar_id}",
                    channel_id=None,
                    resource_id=None,
                    resource_state=None
                )
            
            logger.debug(f"Webhook validation successful for channel {webhook_headers.x_goog_channel_id}")
            
            return WebhookValidationResult(
                is_valid=True,
                reason=None,
                channel_id=webhook_headers.x_goog_channel_id,
                resource_id=webhook_headers.x_goog_resource_id,
                resource_state=webhook_headers.x_goog_resource_state
            )
            
        except Exception as e:
            logger.error(f"Error validating webhook: {e}")
            return WebhookValidationResult(
                is_valid=False,
                reason=f"Validation error: {str(e)}",
                channel_id=None,
                resource_id=None,
                resource_state=None
            )
    
    def _is_monitored_calendar(self, calendar_id: str) -> bool:
        """Check if a calendar ID is being monitored by any sync flow.
        
        Args:
            calendar_id: Calendar ID to check
            
        Returns:
            True if calendar is monitored, False otherwise
        """
        return calendar_id in self.calendar_to_account
    
    def create_webhook_subscription(self, calendar_id: str, account_id: int, callback_url: str, 
                                  channel_token: Optional[str] = None) -> ChannelSubscriptionResult:
        """Create a webhook subscription for a calendar.
        
        Args:
            calendar_id: Calendar ID to subscribe to
            account_id: Account ID for the calendar
            callback_url: URL to receive webhook notifications
            channel_token: Optional verification token for the channel
            
        Returns:
            Subscription result
        """
        try:
            # Get calendar client
            client = self.account_manager.get_client(account_id)
            
            # Generate unique channel ID
            channel_id = f"cal-sync-{uuid.uuid4().hex[:16]}"
            
            logger.info(f"Creating webhook subscription for calendar {calendar_id} at {callback_url} with channel {channel_id}")
            
            # Create push notification channel using Google Calendar API
            channel_result = client.create_push_notification_channel(
                calendar_id=calendar_id,
                webhook_url=callback_url,
                channel_id=channel_id,
                channel_token=channel_token
            )
            
            logger.info(f"Successfully created webhook subscription {channel_id} for calendar {calendar_id}")
            
            return ChannelSubscriptionResult(
                success=True,
                channel_id=channel_result['channel_id'],
                calendar_id=calendar_id,
                resource_id=channel_result.get('resource_id'),
                expiration=channel_result.get('expiration'),
                error=None
            )
            
        except GoogleCalendarError as e:
            logger.error(f"Google Calendar API error creating webhook subscription for calendar {calendar_id}: {e}")
            return ChannelSubscriptionResult(
                success=False,
                channel_id="",
                calendar_id=calendar_id,
                resource_id=None,
                expiration=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error creating webhook subscription for calendar {calendar_id}: {e}")
            return ChannelSubscriptionResult(
                success=False,
                channel_id="",
                calendar_id=calendar_id,
                resource_id=None,
                expiration=None,
                error=str(e)
            )
    
    def delete_webhook_subscription(self, channel_id: str, resource_id: str, account_id: Optional[int] = None) -> ChannelSubscriptionResult:
        """Delete a webhook subscription.
        
        Args:
            channel_id: Channel ID to delete
            resource_id: Resource ID for the subscription
            account_id: Optional account ID if specific client is needed
            
        Returns:
            Deletion result
        """
        try:
            logger.info(f"Deleting webhook subscription {channel_id} for resource {resource_id}")
            
            # If account_id is provided, use specific client, otherwise try with any available client
            if account_id:
                client = self.account_manager.get_client(account_id)
            else:
                # Use the first available client for channel deletion
                if not self.config.accounts:
                    raise GoogleCalendarError("No accounts configured for webhook deletion")
                client = self.account_manager.get_client(self.config.accounts[0].account_id)
            
            # Stop the push notification channel using Google Calendar API
            success = client.stop_push_notification_channel(channel_id, resource_id)
            
            if success:
                logger.info(f"Successfully deleted webhook subscription {channel_id}")
                return ChannelSubscriptionResult(
                    success=True,
                    channel_id=channel_id,
                    calendar_id="",  # Not applicable for deletion
                    resource_id=resource_id,
                    expiration=None,
                    error=None
                )
            else:
                logger.warning(f"Webhook subscription {channel_id} not found or already expired")
                return ChannelSubscriptionResult(
                    success=True,  # Consider not found as success for idempotency
                    channel_id=channel_id,
                    calendar_id="",
                    resource_id=resource_id,
                    expiration=None,
                    error="Channel not found or already expired"
                )
            
        except GoogleCalendarError as e:
            logger.error(f"Google Calendar API error deleting webhook subscription {channel_id}: {e}")
            return ChannelSubscriptionResult(
                success=False,
                channel_id=channel_id,
                calendar_id="",
                resource_id=resource_id,
                expiration=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error deleting webhook subscription {channel_id}: {e}")
            return ChannelSubscriptionResult(
                success=False,
                channel_id=channel_id,
                calendar_id="",
                resource_id=resource_id,
                expiration=None,
                error=str(e)
            ) 