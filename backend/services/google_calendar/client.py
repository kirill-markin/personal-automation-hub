"""
Google Calendar API client with OAuth2 refresh token authentication.

This client handles:
- OAuth2 refresh token authentication
- Calendar API operations (list, create, delete events)
- Rate limiting and error handling
- Automatic token refresh
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class GoogleCalendarError(Exception):
    """Base exception for Google Calendar API errors."""
    pass

class GoogleCalendarClient:
    """Google Calendar API client with OAuth2 refresh token authentication."""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str) -> None:
        """Initialize Google Calendar client.
        
        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret
            refresh_token: OAuth2 refresh token for authentication
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._service = None  # type: ignore
        self._credentials: Optional[Credentials] = None
        
    def _get_credentials(self) -> Credentials:
        """Get or refresh OAuth2 credentials."""
        if self._credentials is None:
            self._credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        
        # Refresh token if needed
        if not self._credentials.valid:
            try:
                self._credentials.refresh(Request())  # type: ignore
                logger.info("OAuth2 token refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh OAuth2 token: {e}")
                raise GoogleCalendarError(f"Authentication failed: {e}")
        
        return self._credentials
    
    def _get_service(self):  # type: ignore
        """Get or create Google Calendar service."""
        if self._service is None:  # type: ignore
            credentials = self._get_credentials()
            self._service = build('calendar', 'v3', credentials=credentials)  # type: ignore
        return self._service  # type: ignore
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError, TimeoutError)),
        reraise=True
    )
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all accessible calendars.
        
        Returns:
            List of calendar dictionaries with id, summary, and access role
        """
        try:
            service = self._get_service()  # type: ignore
            calendars_result = service.calendarList().list().execute()  # type: ignore
            calendars = calendars_result.get('items', [])  # type: ignore
            
            # Return simplified calendar info
            return [
                {
                    'id': cal['id'],
                    'summary': cal.get('summary', 'Unknown'),  # type: ignore
                    'access_role': cal.get('accessRole', 'unknown'),  # type: ignore
                    'primary': cal.get('primary', False)  # type: ignore
                }
                for cal in calendars  # type: ignore
            ]
            
        except HttpError as e:
            logger.error(f"HTTP error listing calendars: {e}")
            raise GoogleCalendarError(f"Failed to list calendars: {e}")
        except Exception as e:
            logger.error(f"Unexpected error listing calendars: {e}")
            raise GoogleCalendarError(f"Unexpected error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError, TimeoutError)),
        reraise=True
    )
    def get_events(self, calendar_id: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get events from a calendar within a time range.
        
        Args:
            calendar_id: Calendar ID to query
            start_time: Start of time range (inclusive)
            end_time: End of time range (exclusive)
            
        Returns:
            List of event dictionaries
        """
        try:
            service = self._get_service()  # type: ignore
            
            # Format times for API - convert to UTC and use proper ISO format
            if start_time.tzinfo is not None:
                # Convert timezone-aware datetime to UTC
                start_utc = start_time.astimezone(timezone.utc).replace(tzinfo=None)
                time_min = start_utc.isoformat() + 'Z'
            else:
                # Assume naive datetime is already UTC
                time_min = start_time.isoformat() + 'Z'
                
            if end_time.tzinfo is not None:
                # Convert timezone-aware datetime to UTC
                end_utc = end_time.astimezone(timezone.utc).replace(tzinfo=None)
                time_max = end_utc.isoformat() + 'Z'
            else:
                # Assume naive datetime is already UTC
                time_max = end_time.isoformat() + 'Z'
            
            events_result = service.events().list(  # type: ignore
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()  # type: ignore
            
            events = events_result.get('items', [])  # type: ignore
            
            # Parse events into simplified format
            parsed_events = []
            for event in events:  # type: ignore
                parsed_events.append(self._parse_event(event))  # type: ignore
            
            return parsed_events  # type: ignore
            
        except HttpError as e:
            logger.error(f"HTTP error getting events for calendar {calendar_id}: {e}")
            raise GoogleCalendarError(f"Failed to get events: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting events for calendar {calendar_id}: {e}")
            raise GoogleCalendarError(f"Unexpected error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError, TimeoutError)),
        reraise=True
    )
    def create_event(self, calendar_id: str, title: str, start_time: datetime, end_time: datetime, 
                    description: str = "", participants: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new event in the specified calendar.
        
        Args:
            calendar_id: Calendar ID where to create the event
            title: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description (optional)
            participants: List of participant email addresses (optional)
            
        Returns:
            Created event dictionary
        """
        try:
            service = self._get_service()  # type: ignore
            
            event: Dict[str, Any] = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            # Add attendees if participants are provided
            if participants:
                event['attendees'] = [{'email': email} for email in participants]
            
            event_result = service.events().insert(calendarId=calendar_id, body=event).execute()  # type: ignore
            logger.info(f"Created event '{title}' in calendar {calendar_id}")
            
            return self._parse_event(event_result)  # type: ignore
            
        except HttpError as e:
            logger.error(f"HTTP error creating event in calendar {calendar_id}: {e}")
            raise GoogleCalendarError(f"Failed to create event: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating event in calendar {calendar_id}: {e}")
            raise GoogleCalendarError(f"Unexpected error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError, TimeoutError)),
        reraise=True
    )
    def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete an event from the specified calendar.
        
        Args:
            calendar_id: Calendar ID containing the event
            event_id: Event ID to delete
            
        Returns:
            True if deleted successfully, False if event not found
        """
        try:
            service = self._get_service()  # type: ignore
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()  # type: ignore
            logger.info(f"Deleted event {event_id} from calendar {calendar_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:  # type: ignore
                logger.warning(f"Event {event_id} not found in calendar {calendar_id}")
                return False
            else:
                logger.error(f"HTTP error deleting event {event_id}: {e}")
                raise GoogleCalendarError(f"Failed to delete event: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting event {event_id}: {e}")
            raise GoogleCalendarError(f"Unexpected error: {e}")
    
    def find_events_by_time_and_title(self, calendar_id: str, start_time: datetime, 
                                     end_time: datetime, title: str) -> List[Dict[str, Any]]:
        """Find events matching exact start time, end time, and title.
        
        Args:
            calendar_id: Calendar ID to search
            start_time: Exact start time to match
            end_time: Exact end time to match
            title: Exact title to match
            
        Returns:
            List of matching events
        """
        try:
            # Get events in a wider time range to ensure we capture the event
            search_start = start_time - timedelta(hours=1)
            search_end = end_time + timedelta(hours=1)
            
            events = self.get_events(calendar_id, search_start, search_end)
            
            # Normalize the comparison times (remove seconds, microseconds)
            # Handle timezone conversion: if search times are naive, treat them as UTC
            # and convert event times to UTC for comparison
            if start_time.tzinfo is None:
                # Search times are naive, treat as UTC and convert event times to UTC
                normalized_start = start_time.replace(second=0, microsecond=0)
                normalized_end = end_time.replace(second=0, microsecond=0)
            else:
                # Search times have timezone, convert to UTC naive
                normalized_start = start_time.astimezone(timezone.utc).replace(second=0, microsecond=0, tzinfo=None)
                normalized_end = end_time.astimezone(timezone.utc).replace(second=0, microsecond=0, tzinfo=None)
            
            # Filter by exact match with normalized times
            matching_events = []
            for event in events:
                # Convert event times to UTC naive for comparison
                if event['start_time'].tzinfo is not None:
                    event_start = event['start_time'].astimezone(timezone.utc).replace(second=0, microsecond=0, tzinfo=None)
                    event_end = event['end_time'].astimezone(timezone.utc).replace(second=0, microsecond=0, tzinfo=None)
                else:
                    event_start = event['start_time'].replace(second=0, microsecond=0)
                    event_end = event['end_time'].replace(second=0, microsecond=0)
                
                # Case-insensitive title comparison to handle Google Calendar auto-capitalization
                if (event['title'].lower() == title.lower() and 
                    event_start == normalized_start and 
                    event_end == normalized_end):
                    matching_events.append(event)  # type: ignore
            
            return matching_events  # type: ignore
            
        except Exception as e:
            logger.error(f"Error finding events by time and title: {e}")
            raise GoogleCalendarError(f"Failed to find events: {e}")
    
    def _parse_event(self, event: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        """Parse Google Calendar API event into simplified format.
        
        Args:
            event: Raw event from Google Calendar API
            
        Returns:
            Simplified event dictionary
        """
        # Parse start time
        start = event.get('start', {})
        if 'dateTime' in start:
            start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
        else:
            # All-day event
            start_time = datetime.fromisoformat(start.get('date', ''))
        
        # Parse end time
        end = event.get('end', {})
        if 'dateTime' in end:
            end_time = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
        else:
            # All-day event
            end_time = datetime.fromisoformat(end.get('date', ''))
        
        # Parse attendees
        attendees = event.get('attendees', [])
        participants = [attendee.get('email', '') for attendee in attendees]
        
        return {
            'id': event.get('id', ''),
            'title': event.get('summary', ''),
            'description': event.get('description', ''),
            'start_time': start_time,
            'end_time': end_time,
            'participants': participants,
            'participant_count': len(participants),
            'status': event.get('status', 'unknown'),
            'creator': event.get('creator', {}).get('email', ''),
            'organizer': event.get('organizer', {}).get('email', '')
        }
    
    def test_connection(self) -> bool:
        """Test if the client can connect to Google Calendar API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            calendars = self.list_calendars()
            logger.info(f"Connection test successful. Found {len(calendars)} calendars.")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError, TimeoutError)),
        reraise=True
    )
    def create_push_notification_channel(self, calendar_id: str, webhook_url: str, 
                                       channel_id: str, channel_token: Optional[str] = None) -> Dict[str, Any]:
        """Create a push notification channel for calendar events.
        
        Args:
            calendar_id: Calendar ID to watch for changes
            webhook_url: URL to receive webhook notifications
            channel_id: Unique channel identifier
            channel_token: Optional verification token
            
        Returns:
            Channel information from Google Calendar API
        """
        try:
            service = self._get_service()  # type: ignore
            
            # Prepare channel configuration
            channel_body = {
                'id': channel_id,
                'type': 'web_hook',
                'address': webhook_url
            }
            
            if channel_token:
                channel_body['token'] = channel_token
            
            # Create the watch request
            result = service.events().watch(  # type: ignore
                calendarId=calendar_id,
                body=channel_body
            ).execute()  # type: ignore
            
            logger.info(f"Created push notification channel {channel_id} for calendar {calendar_id}")
            
            return {
                'channel_id': result.get('id', ''),  # type: ignore
                'resource_id': result.get('resourceId', ''),  # type: ignore
                'resource_uri': result.get('resourceUri', ''),  # type: ignore
                'expiration': result.get('expiration'),  # type: ignore
                'kind': result.get('kind', ''),  # type: ignore
                'calendar_id': calendar_id
            }
            
        except HttpError as e:
            logger.error(f"HTTP error creating push notification channel for calendar {calendar_id}: {e}")
            raise GoogleCalendarError(f"Failed to create webhook subscription: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating push notification channel for calendar {calendar_id}: {e}")
            raise GoogleCalendarError(f"Unexpected error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError, TimeoutError)),
        reraise=True
    )
    def stop_push_notification_channel(self, channel_id: str, resource_id: str) -> bool:
        """Stop a push notification channel.
        
        Args:
            channel_id: Channel ID to stop
            resource_id: Resource ID for the channel
            
        Returns:
            True if stopped successfully, False if channel not found
        """
        try:
            service = self._get_service()  # type: ignore
            
            # Stop the channel
            service.channels().stop(  # type: ignore
                body={
                    'id': channel_id,
                    'resourceId': resource_id
                }
            ).execute()  # type: ignore
            
            logger.info(f"Stopped push notification channel {channel_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:  # type: ignore
                logger.warning(f"Channel {channel_id} not found or already expired")
                return False
            else:
                logger.error(f"HTTP error stopping push notification channel {channel_id}: {e}")
                raise GoogleCalendarError(f"Failed to stop webhook subscription: {e}")
        except Exception as e:
            logger.error(f"Unexpected error stopping push notification channel {channel_id}: {e}")
            raise GoogleCalendarError(f"Unexpected error: {e}") 