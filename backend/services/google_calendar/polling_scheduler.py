"""
Daily polling scheduler for Google Calendar synchronization.

This module provides a backup polling system that runs daily to catch
any events that might have been missed by the webhook system.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore

from backend.models.calendar import (
    MultiAccountConfig,
    CompleteSyncResult,
    SchedulerInfo,
    SchedulerStats,
    JobHistoryEntry
)
from backend.services.google_calendar.sync_engine import CalendarSyncEngine
from backend.services.google_calendar.account_manager import AccountManager

logger = logging.getLogger(__name__)


class PollingSchedulerError(Exception):
    """Exception raised when polling scheduler operations fail."""
    pass


class CalendarPollingScheduler:
    """Daily polling scheduler for calendar synchronization backup."""
    
    def __init__(self, config: MultiAccountConfig, account_manager: AccountManager, sync_engine: CalendarSyncEngine) -> None:
        """Initialize polling scheduler.
        
        Args:
            config: Multi-account configuration
            account_manager: Account manager for accessing Google Calendar clients
            sync_engine: Sync engine for processing events
        """
        self.config = config
        self.account_manager = account_manager
        self.sync_engine = sync_engine
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        
        # Stats tracking
        self.stats: Dict[str, Any] = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'last_run_time': None,
            'last_run_success': False,
            'last_run_error': None
        }
        
        logger.info(f"Initialized polling scheduler for {len(config.sync_flows)} sync flows")
    
    def start(self) -> None:
        """Start the polling scheduler."""
        if self.is_running:
            logger.warning("Polling scheduler is already running")
            return
        
        try:
            # Create scheduler
            self.scheduler = AsyncIOScheduler()
            
            # Schedule periodic sync job
            trigger = CronTrigger(
                minute=f"*/{self.config.sync_interval_minutes}",
                second=0
            )
            
            self.scheduler.add_job(  # type: ignore
                self._run_periodic_sync,
                trigger=trigger,
                id='periodic_calendar_sync',
                name='Periodic Calendar Sync',
                replace_existing=True
            )
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Started polling scheduler - periodic sync every {self.config.sync_interval_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Error starting polling scheduler: {e}")
            raise PollingSchedulerError(f"Failed to start polling scheduler: {e}")
    
    def stop(self) -> None:
        """Stop the polling scheduler."""
        if not self.is_running:
            logger.warning("Polling scheduler is not running")
            return
        
        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=False)  # type: ignore
                self.scheduler = None
            
            self.is_running = False
            logger.info("Stopped polling scheduler")
            
        except Exception as e:
            logger.error(f"Error stopping polling scheduler: {e}")
            raise PollingSchedulerError(f"Failed to stop polling scheduler: {e}")
    
    async def _run_periodic_sync(self) -> None:
        """Run periodic sync job."""
        run_start_time = datetime.now()
        
        logger.info("Starting periodic calendar sync job")
        
        try:
            # Update stats
            self.stats['total_runs'] += 1
            self.stats['last_run_time'] = run_start_time.isoformat()
            
            # Calculate sync date range
            # Sync from 2 days ago to 14 days from now
            start_date = run_start_time - timedelta(days=2)
            end_date = run_start_time + timedelta(days=14)
            
            # Run sync
            sync_results = self.sync_engine.sync_all_source_calendars(
                start_date=start_date,
                end_date=end_date,
                sync_type="polling"
            )
            
            # Update stats
            self.stats['successful_runs'] += 1
            self.stats['last_run_success'] = True
            self.stats['last_run_error'] = None
            
            # Log results
            run_duration = (datetime.now() - run_start_time).total_seconds()
            logger.info(f"Daily sync completed successfully in {run_duration:.2f}s: "
                       f"{sync_results.calendars_synced} calendars, "
                       f"{sync_results.total_events_found} events found, "
                       f"{sync_results.total_events_processed} events processed")
            
        except Exception as e:
            # Update stats
            self.stats['failed_runs'] += 1
            self.stats['last_run_success'] = False
            self.stats['last_run_error'] = str(e)
            
            logger.error(f"Daily sync failed: {e}")
            
            # Don't re-raise - we want the scheduler to continue
    
    def run_manual_sync(self, days_back: int = 2, days_forward: int = 14) -> CompleteSyncResult:
        """Run manual sync operation.
        
        Args:
            days_back: Number of days back to sync (default: 2)
            days_forward: Number of days forward to sync (default: 14)
            
        Returns:
            Sync results
        """
        sync_start_time = datetime.now()
        
        logger.info(f"Starting manual sync: {days_back} days back, {days_forward} days forward")
        
        try:
            # Calculate sync date range
            start_date = sync_start_time - timedelta(days=days_back)
            end_date = sync_start_time + timedelta(days=days_forward)
            
            # Run sync
            sync_results = self.sync_engine.sync_all_source_calendars(
                start_date=start_date,
                end_date=end_date,
                sync_type="manual"
            )
            
            # Add timing info
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            sync_results.sync_duration_seconds = sync_duration
            sync_results.sync_start_time = sync_start_time.isoformat()
            
            logger.info(f"Manual sync completed in {sync_duration:.2f}s: "
                       f"{sync_results.calendars_synced} calendars, "
                       f"{sync_results.total_events_found} events found, "
                       f"{sync_results.total_events_processed} events processed")
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            # Calculate sync date range for error result
            start_date = sync_start_time - timedelta(days=days_back)
            end_date = sync_start_time + timedelta(days=days_forward)
            
            # Return a failed sync result
            return CompleteSyncResult(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                sync_type="manual",
                calendars_synced=0,
                total_events_found=0,
                total_events_processed=0,
                calendar_results=[],
                sync_duration_seconds=(datetime.now() - sync_start_time).total_seconds(),
                sync_start_time=sync_start_time.isoformat()
            )
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time.
        
        Returns:
            Next run time or None if scheduler is not running
        """
        if not self.is_running or not self.scheduler:
            return None
        
        try:
            job = self.scheduler.get_job('daily_calendar_sync')  # type: ignore
            if job and job.next_run_time:  # type: ignore
                return job.next_run_time  # type: ignore
        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
        
        return None
    
    def get_schedule_info(self) -> SchedulerInfo:
        """Get scheduler information.
        
        Returns:
            Scheduler information
        """
        next_run = self.get_next_run_time()
        
        stats = SchedulerStats(
            total_runs=self.stats['total_runs'],  # type: ignore
            successful_runs=self.stats['successful_runs'],  # type: ignore
            failed_runs=self.stats['failed_runs'],  # type: ignore
            last_run_time=self.stats['last_run_time'],  # type: ignore
            last_run_success=self.stats['last_run_success'],  # type: ignore
            last_run_error=self.stats['last_run_error']  # type: ignore
        )
        
        return SchedulerInfo(
            is_running=self.is_running,
            sync_interval_minutes=self.config.sync_interval_minutes,
            next_run_time=next_run.isoformat() if next_run else None,
            stats=stats
        )
    
    def get_stats(self) -> SchedulerInfo:
        """Get polling scheduler statistics.
        
        Returns:
            Complete scheduler information including stats
        """
        return self.get_schedule_info()
    
    def reset_stats(self) -> None:
        """Reset polling scheduler statistics."""
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'last_run_time': None,
            'last_run_success': False,
            'last_run_error': None
        }
        logger.info("Reset polling scheduler statistics")
    
    def update_schedule(self, interval_minutes: int) -> None:
        """Update the polling schedule.
        
        Args:
            interval_minutes: Sync interval in minutes (1-1440)
        """
        if not (1 <= interval_minutes <= 1440):
            raise ValueError("Interval must be between 1 and 1440 minutes")
        
        # Update config
        self.config.sync_interval_minutes = interval_minutes
        
        # Restart scheduler with new schedule if it's running
        if self.is_running:
            logger.info(f"Updating schedule to every {interval_minutes} minutes")
            self.stop()
            self.start()
        
        logger.info(f"Updated schedule to every {interval_minutes} minutes")
    
    def force_run_now(self) -> None:
        """Force run the daily sync job immediately.
        
        This will trigger the sync job outside of the normal schedule.
        """
        if not self.is_running or not self.scheduler:
            raise PollingSchedulerError("Scheduler is not running")
        
        try:
            # Add one-time job to run immediately
            self.scheduler.add_job(  # type: ignore
                self._run_periodic_sync,
                trigger='date',
                run_date=datetime.now(),
                id='manual_sync_now',
                name='Manual Sync Now',
                replace_existing=True
            )
            
            logger.info("Scheduled immediate sync run")
            
        except Exception as e:
            logger.error(f"Error scheduling immediate sync: {e}")
            raise PollingSchedulerError(f"Failed to schedule immediate sync: {e}")
    
    def get_job_history(self) -> List[JobHistoryEntry]:
        """Get history of scheduler jobs.
        
        Returns:
            List of job execution information
        """
        # This is a simple implementation - in production you might want
        # to store job history in a database
        history: List[JobHistoryEntry] = []
        
        if self.stats['last_run_time']:  # type: ignore
            history.append(JobHistoryEntry(
                run_time=self.stats['last_run_time'],  # type: ignore
                success=self.stats['last_run_success'],  # type: ignore
                error=self.stats['last_run_error'],  # type: ignore
                type='periodic_sync'
            ))
        
        return history 