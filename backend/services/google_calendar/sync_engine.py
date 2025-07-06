"""
Core calendar synchronization engine.

This module provides the main sync logic for processing calendar events
and creating/deleting busy blocks across multiple sync flows.
"""

import logging
from typing import List, Tuple
from datetime import datetime

from backend.models.calendar import (
    CalendarEvent, 
    SyncFlow, 
    BusyBlock, 
    MultiAccountConfig,
    EventProcessingResult,
    CalendarSyncResult,
    CompleteSyncResult,
    SyncEngineStats
)
from backend.services.google_calendar.account_manager import AccountManager

logger = logging.getLogger(__name__)


class SyncEngineError(Exception):
    """Exception raised when sync engine operations fail."""
    pass


class CalendarSyncEngine:
    """Core calendar synchronization engine for processing events and managing busy blocks."""
    
    def __init__(self, config: MultiAccountConfig, account_manager: AccountManager) -> None:
        """Initialize sync engine.
        
        Args:
            config: Multi-account configuration
            account_manager: Account manager for accessing Google Calendar clients
        """
        self.config = config
        self.account_manager = account_manager
        
        # Stats tracking
        self.stats = {
            'events_processed': 0,
            'busy_blocks_created': 0,
            'busy_blocks_deleted': 0,
            'errors': 0
        }
        
        logger.info(f"Initialized sync engine with {len(config.accounts)} accounts and {len(config.sync_flows)} sync flows")
    
    def process_event(self, event: CalendarEvent, sync_type: str = "webhook") -> List[EventProcessingResult]:
        """Process a calendar event through all applicable sync flows.
        
        Args:
            event: Calendar event to process
            sync_type: Type of sync operation ("webhook" or "polling")
            
        Returns:
            List of processing results for each applicable sync flow
        """
        results: List[EventProcessingResult] = []
        
        # Find all sync flows that apply to this event
        applicable_flows = self._find_applicable_flows(event)
        
        if not applicable_flows:
            logger.debug(f"No applicable sync flows for event {event.id} from calendar {event.calendar_id}")
            return results
        
        logger.info(f"Processing event '{event.title}' ({event.id}) through {len(applicable_flows)} sync flows (type: {sync_type})")
        
        # Process through each applicable flow
        for flow in applicable_flows:
            try:
                result = self._process_event_for_flow(event, flow, sync_type)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing event {event.id} for flow {flow.name}: {e}")
                self.stats['errors'] += 1
                results.append(EventProcessingResult(
                    flow_name=flow.name,
                    event_id=event.id,
                    event_title=event.title,
                    sync_type=sync_type,
                    success=False,
                    action='error',
                    error=str(e),
                    reason=None
                ))
        
        self.stats['events_processed'] += 1
        return results
    
    def _find_applicable_flows(self, event: CalendarEvent) -> List[SyncFlow]:
        """Find all sync flows that apply to the given event.
        
        Args:
            event: Calendar event to check
            
        Returns:
            List of applicable sync flows
        """
        applicable_flows: List[SyncFlow] = []
        
        for flow in self.config.sync_flows:
            # Check if this flow monitors the event's calendar
            if (flow.source_account_id == event.account_id and 
                flow.source_calendar_id == event.calendar_id):
                applicable_flows.append(flow)
        
        return applicable_flows
    
    def _process_event_for_flow(self, event: CalendarEvent, flow: SyncFlow, sync_type: str) -> EventProcessingResult:
        """Process an event for a specific sync flow.
        
        Args:
            event: Calendar event to process
            flow: Sync flow to apply
            sync_type: Type of sync operation
            
        Returns:
            Processing result
        """
        try:
            # Check if event meets criteria (2+ participants, confirmed)
            if not self._event_meets_criteria(event):
                return EventProcessingResult(
                    flow_name=flow.name,
                    event_id=event.id,
                    event_title=event.title,
                    sync_type=sync_type,
                    success=True,
                    action='skipped',
                    error=None,
                    reason=f"Event doesn't meet criteria (participants: {event.participant_count}, status: {event.status})"
                )
            
            if event.is_cancelled():
                # Handle cancelled event - remove busy block
                deleted = self._delete_busy_block_for_event(event, flow)
                action = 'deleted' if deleted else 'delete_attempted'
                if deleted:
                    self.stats['busy_blocks_deleted'] += 1
                
                return EventProcessingResult(
                    flow_name=flow.name,
                    event_id=event.id,
                    event_title=event.title,
                    sync_type=sync_type,
                    success=True,
                    action=action,
                    error=None,
                    reason=None
                )
                
            else:
                # Handle active event - create busy block
                created = self._create_busy_block_for_event(event, flow)
                action = 'created' if created else 'existed'
                if created:
                    self.stats['busy_blocks_created'] += 1
                
                return EventProcessingResult(
                    flow_name=flow.name,
                    event_id=event.id,
                    event_title=event.title,
                    sync_type=sync_type,
                    success=True,
                    action=action,
                    error=None,
                    reason=None
                )
            
        except Exception as e:
            logger.error(f"Error processing event {event.id} for flow {flow.name}: {e}")
            self.stats['errors'] += 1
            return EventProcessingResult(
                flow_name=flow.name,
                event_id=event.id,
                event_title=event.title,
                sync_type=sync_type,
                success=False,
                action='error',
                error=str(e),
                reason=None
            )
    
    def _event_meets_criteria(self, event: CalendarEvent) -> bool:
        """Check if event meets sync criteria.
        
        Args:
            event: Calendar event to check
            
        Returns:
            True if event should be synced, False otherwise
        """
        # Must have 2+ participants
        if not event.has_multiple_participants():
            return False
        
        # Must be confirmed (not cancelled, tentative, etc.)
        if not event.is_confirmed():
            return False
        
        return True
    
    def _create_busy_block_for_event(self, event: CalendarEvent, flow: SyncFlow) -> bool:
        """Create a busy block for an event in the target calendar.
        
        Args:
            event: Source calendar event
            flow: Sync flow configuration
            
        Returns:
            True if busy block was created, False if it already existed
        """
        # Create busy block configuration
        busy_block = BusyBlock.from_event_and_flow(event, flow)
        
        # Check if busy block already exists
        if self._busy_block_exists(busy_block):
            logger.debug(f"Busy block already exists for event {event.id} in flow {flow.name}")
            return False
        
        # Create the busy block
        target_client = self.account_manager.get_client(flow.target_account_id)
        
        created_event = target_client.create_event(
            calendar_id=flow.target_calendar_id,
            title=busy_block.title,
            start_time=busy_block.start_time,
            end_time=busy_block.end_time,
            description=f"Busy block for: {event.title}"
        )
        
        logger.info(f"Created busy block '{busy_block.title}' for event '{event.title}' in flow {flow.name}")
        return True
    
    def _delete_busy_block_for_event(self, event: CalendarEvent, flow: SyncFlow) -> bool:
        """Delete busy block for a cancelled event.
        
        Args:
            event: Source calendar event (cancelled)
            flow: Sync flow configuration
            
        Returns:
            True if busy block was deleted, False if not found
        """
        # Calculate what the busy block would be for this event
        busy_block = BusyBlock.from_event_and_flow(event, flow)
        
        # Search for existing busy block
        target_client = self.account_manager.get_client(flow.target_account_id)
        
        existing_blocks = target_client.find_events_by_time_and_title(
            calendar_id=flow.target_calendar_id,
            start_time=busy_block.start_time,
            end_time=busy_block.end_time,
            title=busy_block.title
        )
        
        if not existing_blocks:
            logger.debug(f"No busy block found to delete for cancelled event {event.id} in flow {flow.name}")
            return False
        
        # Delete all matching busy blocks
        deleted_count = 0
        for block in existing_blocks:
            if target_client.delete_event(flow.target_calendar_id, block['id']):
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} busy block(s) for cancelled event '{event.title}' in flow {flow.name}")
        
        return deleted_count > 0
    
    def _busy_block_exists(self, busy_block: BusyBlock) -> bool:
        """Check if a busy block already exists.
        
        Args:
            busy_block: Busy block to check for
            
        Returns:
            True if busy block exists, False otherwise
        """
        try:
            target_client = self.account_manager.get_client(busy_block.target_account_id)
            
            existing_blocks = target_client.find_events_by_time_and_title(
                calendar_id=busy_block.target_calendar_id,
                start_time=busy_block.start_time,
                end_time=busy_block.end_time,
                title=busy_block.title
            )
            
            return len(existing_blocks) > 0
            
        except Exception as e:
            logger.error(f"Error checking if busy block exists: {e}")
            return False
    
    def sync_calendar_events(self, calendar_id: str, account_id: int, 
                           start_date: datetime, end_date: datetime,
                           sync_type: str = "polling") -> CalendarSyncResult:
        """Sync events from a specific calendar within a date range.
        
        Args:
            calendar_id: Calendar ID to sync
            account_id: Account ID for the calendar
            start_date: Start date for sync range
            end_date: End date for sync range
            sync_type: Type of sync operation ("webhook" or "polling")
            
        Returns:
            Sync results
        """
        result = CalendarSyncResult(
            calendar_id=calendar_id,
            account_id=account_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            sync_type=sync_type,
            events_found=0,
            events_processed=0,
            results=[],
            error=None
        )
        
        try:
            # Get calendar client
            client = self.account_manager.get_client(account_id)
            
            # Get events in date range
            events = client.get_events(calendar_id, start_date, end_date)
            result.events_found = len(events)
            
            logger.info(f"Found {len(events)} events in calendar {calendar_id} from {start_date.date()} to {end_date.date()}")
            
            # Process each event
            for event_data in events:
                try:
                    # Convert to CalendarEvent model
                    event = CalendarEvent(
                        id=event_data['id'],
                        calendar_id=calendar_id,
                        account_id=account_id,
                        title=event_data['title'],
                        description=event_data.get('description', ''),
                        start_time=event_data['start_time'],
                        end_time=event_data['end_time'],
                        participants=event_data.get('participants', []),
                        participant_count=event_data.get('participant_count', 0),
                        status=event_data.get('status', 'unknown'),
                        creator=event_data.get('creator', ''),
                        organizer=event_data.get('organizer', '')
                    )
                    
                    # Process event through sync flows
                    event_results = self.process_event(event, sync_type)
                    result.results.extend(event_results)
                    
                    if event_results:
                        result.events_processed += 1
                        
                except Exception as e:
                    logger.error(f"Error processing event {event_data.get('id', 'unknown')}: {e}")
                    result.results.append(EventProcessingResult(
                        flow_name='unknown',
                        event_id=event_data.get('id', 'unknown'),
                        event_title=event_data.get('title', 'unknown'),
                        sync_type=sync_type,
                        success=False,
                        action='error',
                        error=str(e),
                        reason=None
                    ))
            
            logger.info(f"Processed {result.events_processed} events from calendar {calendar_id}")
            
        except Exception as e:
            logger.error(f"Error syncing calendar {calendar_id}: {e}")
            result.error = str(e)
            self.stats['errors'] += 1
        
        return result
    
    def sync_all_source_calendars(self, start_date: datetime, end_date: datetime,
                                 sync_type: str = "polling") -> CompleteSyncResult:
        """Sync all source calendars from configured sync flows.
        
        Args:
            start_date: Start date for sync range
            end_date: End date for sync range
            sync_type: Type of sync operation
            
        Returns:
            Complete sync results
        """
        sync_results = CompleteSyncResult(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            sync_type=sync_type,
            calendars_synced=0,
            total_events_found=0,
            total_events_processed=0,
            calendar_results=[],
            sync_duration_seconds=None,
            sync_start_time=None
        )
        
        # Get unique source calendars from all sync flows
        source_calendars: set[Tuple[int, str]] = set()
        for flow in self.config.sync_flows:
            source_calendars.add((flow.source_account_id, flow.source_calendar_id))
        
        logger.info(f"Starting sync of {len(source_calendars)} source calendars from {start_date.date()} to {end_date.date()}")
        
        # Sync each unique source calendar
        for account_id, calendar_id in source_calendars:
            try:
                calendar_result = self.sync_calendar_events(
                    calendar_id, account_id, start_date, end_date, sync_type
                )
                
                sync_results.calendar_results.append(calendar_result)
                sync_results.calendars_synced += 1
                sync_results.total_events_found += calendar_result.events_found
                sync_results.total_events_processed += calendar_result.events_processed
                
            except Exception as e:
                logger.error(f"Error syncing calendar {calendar_id} for account {account_id}: {e}")
                error_result = CalendarSyncResult(
                    calendar_id=calendar_id,
                    account_id=account_id,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    sync_type=sync_type,
                    events_found=0,
                    events_processed=0,
                    results=[],
                    error=str(e)
                )
                sync_results.calendar_results.append(error_result)
        
        logger.info(f"Completed sync: {sync_results.calendars_synced} calendars, "
                   f"{sync_results.total_events_found} events found, "
                   f"{sync_results.total_events_processed} events processed")
        
        return sync_results
    
    def get_stats(self) -> SyncEngineStats:
        """Get sync engine statistics.
        
        Returns:
            Statistics
        """
        return SyncEngineStats(
            events_processed=self.stats['events_processed'],
            busy_blocks_created=self.stats['busy_blocks_created'],
            busy_blocks_deleted=self.stats['busy_blocks_deleted'],
            errors=self.stats['errors'],
            accounts=len(self.config.accounts),
            sync_flows=len(self.config.sync_flows),
            last_updated=datetime.now().isoformat()
        )
    
    def reset_stats(self) -> None:
        """Reset sync engine statistics."""
        self.stats = {
            'events_processed': 0,
            'busy_blocks_created': 0,
            'busy_blocks_deleted': 0,
            'errors': 0
        }
        logger.info("Reset sync engine statistics") 