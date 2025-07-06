"""
Pydantic models for Google Calendar sync configuration and operations.

This module defines:
- GoogleAccount: Configuration for a single Google account
- SyncFlow: Configuration for calendar synchronization flows (one source → one target)
- CalendarEvent: Event data structure
- BusyBlockSearchCriteria: Search criteria for finding busy blocks
- MultiAccountConfig: Complete configuration for all accounts and sync flows
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class GoogleAccount(BaseModel):
    """Configuration for a single Google account."""
    
    account_id: int = Field(..., description="Unique account identifier")
    name: str = Field(..., description="Human-readable account name")
    client_id: str = Field(..., description="Google OAuth2 client ID")
    client_secret: str = Field(..., description="Google OAuth2 client secret")
    refresh_token: str = Field(..., description="OAuth2 refresh token for this account")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'GoogleAccount':
        # Validate account_id
        if self.account_id <= 0:
            raise ValueError('account_id must be positive')
        
        # Validate name
        if not self.name.strip():
            raise ValueError('name cannot be empty')
        self.name = self.name.strip()
        
        # Validate client_id
        if not self.client_id.strip():
            raise ValueError('client_id cannot be empty')
        self.client_id = self.client_id.strip()
        
        # Validate client_secret
        if not self.client_secret.strip():
            raise ValueError('client_secret cannot be empty')
        self.client_secret = self.client_secret.strip()
        
        # Validate refresh_token
        if not self.refresh_token.strip():
            raise ValueError('refresh_token cannot be empty')
        self.refresh_token = self.refresh_token.strip()
        
        return self


class SyncFlow(BaseModel):
    """Configuration for a calendar synchronization flow (one source → one target)."""
    
    name: str = Field(..., description="Human-readable name for the sync flow")
    source_account_id: int = Field(..., description="Source account ID (refers to GoogleAccount.account_id)")
    source_calendar_id: str = Field(..., description="Source calendar ID to monitor")
    target_account_id: int = Field(..., description="Target account ID (refers to GoogleAccount.account_id)")
    target_calendar_id: str = Field(..., description="Target calendar ID for busy blocks")
    start_offset: int = Field(..., description="Minutes before event start for busy block (negative for earlier)")
    end_offset: int = Field(..., description="Minutes after event end for busy block (positive for later)")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'SyncFlow':
        # Validate start_offset
        if self.start_offset > 0:
            raise ValueError('start_offset should be negative or zero (minutes before event)')
        
        # Validate end_offset
        if self.end_offset < 0:
            raise ValueError('end_offset should be positive or zero (minutes after event)')
        
        # Validate source_account_id
        if self.source_account_id <= 0:
            raise ValueError('source_account_id must be positive')
        
        # Validate target_account_id
        if self.target_account_id <= 0:
            raise ValueError('target_account_id must be positive')
        
        return self


class CalendarEvent(BaseModel):
    """Calendar event data structure."""
    
    id: str = Field(..., description="Event ID")
    calendar_id: str = Field(..., description="Calendar ID containing the event")
    account_id: int = Field(..., description="Account ID this event belongs to")
    title: str = Field(..., description="Event title/summary")
    description: str = Field(default="", description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    participants: List[str] = Field(default_factory=list, description="List of participant email addresses")
    participant_count: int = Field(default=0, description="Number of participants")
    status: str = Field(..., description="Event status (confirmed, cancelled, etc.)")
    creator: str = Field(default="", description="Event creator email")
    organizer: str = Field(default="", description="Event organizer email")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'CalendarEvent':
        # Set participant_count based on participants list
        if not self.participant_count and self.participants:
            self.participant_count = len(self.participants)
        
        return self
    
    def has_multiple_participants(self) -> bool:
        """Check if event has 2 or more participants."""
        return self.participant_count >= 2
    
    def is_confirmed(self) -> bool:
        """Check if event is confirmed."""
        return self.status.lower() == 'confirmed'
    
    def is_cancelled(self) -> bool:
        """Check if event is cancelled."""
        return self.status.lower() == 'cancelled'


class BusyBlockSearchCriteria(BaseModel):
    """Search criteria for finding existing busy blocks."""
    
    account_id: int = Field(..., description="Account ID to search in")
    calendar_id: str = Field(..., description="Calendar ID to search")
    start_time: datetime = Field(..., description="Exact start time to match")
    end_time: datetime = Field(..., description="Exact end time to match")
    title: str = Field(default="busy", description="Event title to match")
    
    @model_validator(mode='after')
    def validate_end_time(self) -> 'BusyBlockSearchCriteria':
        if self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self


class BusyBlock(BaseModel):
    """Busy block configuration for sync flows."""
    
    source_event: CalendarEvent = Field(..., description="Source event that triggered the busy block")
    target_account_id: int = Field(..., description="Target account ID for the busy block")
    target_calendar_id: str = Field(..., description="Target calendar for the busy block")
    start_time: datetime = Field(..., description="Busy block start time")
    end_time: datetime = Field(..., description="Busy block end time")
    title: str = Field(default="busy", description="Busy block title")
    
    @model_validator(mode='after')
    def validate_end_time(self) -> 'BusyBlock':
        if self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self
    
    @classmethod
    def from_event_and_flow(cls, event: CalendarEvent, flow: SyncFlow) -> 'BusyBlock':
        """Create a BusyBlock from an event and sync flow configuration.
        
        Args:
            event: Source calendar event
            flow: Sync flow configuration
            
        Returns:
            BusyBlock instance with calculated timing
        """
        # Calculate busy block timing
        start_time = event.start_time.replace(second=0, microsecond=0)
        end_time = event.end_time.replace(second=0, microsecond=0)
        
        # Apply offsets (start_offset is negative, end_offset is positive)
        from datetime import timedelta
        busy_start = start_time + timedelta(minutes=flow.start_offset)
        busy_end = end_time + timedelta(minutes=flow.end_offset)
        
        return cls(
            source_event=event,
            target_account_id=flow.target_account_id,
            target_calendar_id=flow.target_calendar_id,
            start_time=busy_start,
            end_time=busy_end,
            title="busy"
        )


class SyncFlowStatus(BaseModel):
    """Status information for a sync flow."""
    
    flow_name: str = Field(..., description="Sync flow name")
    source_account_id: int = Field(..., description="Source account ID")
    source_calendar_id: str = Field(..., description="Source calendar ID")
    target_account_id: int = Field(..., description="Target account ID")
    target_calendar_id: str = Field(..., description="Target calendar ID")
    last_sync_time: Optional[datetime] = Field(None, description="Last successful sync time")
    last_error: Optional[str] = Field(None, description="Last error message")
    events_processed: int = Field(default=0, description="Number of events processed")
    busy_blocks_created: int = Field(default=0, description="Number of busy blocks created")
    busy_blocks_deleted: int = Field(default=0, description="Number of busy blocks deleted")
    is_active: bool = Field(default=True, description="Whether the flow is active")


class MultiAccountConfig(BaseModel):
    """Complete calendar synchronization configuration for multiple accounts."""
    
    accounts: List[GoogleAccount] = Field(..., description="List of Google accounts")
    sync_flows: List[SyncFlow] = Field(..., description="List of sync flows")
    daily_sync_hour: int = Field(default=6, description="Hour of day for daily polling (0-23)")
    daily_sync_timezone: str = Field(default="UTC", description="Timezone for daily sync")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'MultiAccountConfig':
        # Validate daily_sync_hour
        if not (0 <= self.daily_sync_hour <= 23):
            raise ValueError('daily_sync_hour must be between 0 and 23')
        
        # Validate accounts
        if not self.accounts:
            raise ValueError('At least one account must be configured')
        
        # Check for duplicate account IDs
        account_ids = [account.account_id for account in self.accounts]
        if len(account_ids) != len(set(account_ids)):
            raise ValueError('Account IDs must be unique')
        
        # Validate sync_flows
        if not self.sync_flows:
            raise ValueError('At least one sync flow must be configured')
        
        # Validate account references
        account_ids_set = {account.account_id for account in self.accounts}
        
        for flow in self.sync_flows:
            if flow.source_account_id not in account_ids_set:
                raise ValueError(f'Sync flow "{flow.name}" references non-existent source account ID: {flow.source_account_id}')
            
            if flow.target_account_id not in account_ids_set:
                raise ValueError(f'Sync flow "{flow.name}" references non-existent target account ID: {flow.target_account_id}')
        
        return self
    
    def get_account_by_id(self, account_id: int) -> Optional[GoogleAccount]:
        """Get account by ID."""
        for account in self.accounts:
            if account.account_id == account_id:
                return account
        return None
    
    def get_flows_for_source_account(self, account_id: int) -> List[SyncFlow]:
        """Get all sync flows that use the specified account as source."""
        return [flow for flow in self.sync_flows if flow.source_account_id == account_id]
    
    def get_flows_for_target_account(self, account_id: int) -> List[SyncFlow]:
        """Get all sync flows that use the specified account as target."""
        return [flow for flow in self.sync_flows if flow.target_account_id == account_id]


 