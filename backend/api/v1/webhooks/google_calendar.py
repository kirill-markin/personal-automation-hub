"""
Google Calendar webhook API endpoints.

This module provides FastAPI endpoints for receiving Google Calendar webhook notifications
and processing calendar events through the sync engine.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.core.security import validate_api_key
from backend.services.google_calendar.config_loader import load_multi_account_config
from backend.services.google_calendar.account_manager import AccountManager
from backend.services.google_calendar.sync_engine import CalendarSyncEngine
from backend.services.google_calendar.webhook_handler import GoogleCalendarWebhookHandler
from backend.services.google_calendar.polling_scheduler import CalendarPollingScheduler
from backend.models.calendar import WebhookProcessingResult

logger = logging.getLogger(__name__)

# Global instances - will be initialized when the app starts
config = None
account_manager = None
sync_engine = None
webhook_handler = None
polling_scheduler = None

router = APIRouter()


def get_calendar_services():
    """Get initialized calendar services."""
    global config, account_manager, sync_engine, webhook_handler, polling_scheduler
    
    if config is None:
        # Initialize services
        config = load_multi_account_config()
        account_manager = AccountManager(config)
        sync_engine = CalendarSyncEngine(config, account_manager)
        webhook_handler = GoogleCalendarWebhookHandler(config, account_manager, sync_engine)
        polling_scheduler = CalendarPollingScheduler(config, account_manager, sync_engine)
        
        # Start polling scheduler
        polling_scheduler.start()
        
        logger.info("Initialized Google Calendar services")
    
    return {
        'config': config,
        'account_manager': account_manager,
        'sync_engine': sync_engine,
        'webhook_handler': webhook_handler,
        'polling_scheduler': polling_scheduler
    }


@router.post("/google-calendar")
async def handle_google_calendar_webhook(
    request: Request,
    api_key: str = Depends(validate_api_key)
) -> WebhookProcessingResult:
    """
    Handle Google Calendar webhook notifications.
    
    This endpoint receives push notifications from Google Calendar
    when events are created, updated, or deleted.
    """
    try:
        # Get services
        services = get_calendar_services()
        handler = services['webhook_handler']
        
        # Get webhook data
        webhook_data = await request.json()
        
        logger.info(f"Received Google Calendar webhook: {webhook_data}")
        
        # Process webhook
        result = handler.handle_webhook(webhook_data)  # type: ignore
        
        # Return the result directly
        return result  # type: ignore
        
    except Exception as e:
        logger.error(f"Error processing Google Calendar webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.get("/google-calendar/status")
async def get_sync_status(
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Get calendar synchronization status.
    
    Returns information about sync engine stats, scheduler status,
    and monitored calendars.
    """
    try:
        # Get services
        services = get_calendar_services()
        sync_engine = services['sync_engine']
        polling_scheduler = services['polling_scheduler']
        webhook_handler = services['webhook_handler']
        
        # Get status information
        sync_stats = sync_engine.get_stats()  # type: ignore
        scheduler_info = polling_scheduler.get_schedule_info()  # type: ignore
        monitored_calendars = webhook_handler.get_monitored_calendars()  # type: ignore
        
        return {
            'sync_engine': sync_stats,
            'scheduler': scheduler_info,
            'monitored_calendars': monitored_calendars,
            'timestamp': sync_stats.last_updated  # type: ignore
        }
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sync status: {str(e)}"
        )


@router.post("/google-calendar/sync/manual")
async def trigger_manual_sync(
    days_back: int = 2,
    days_forward: int = 14,
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Trigger a manual calendar sync.
    
    This endpoint allows triggering a manual sync operation
    outside of the scheduled daily polling.
    """
    try:
        # Get services
        services = get_calendar_services()
        polling_scheduler = services['polling_scheduler']
        
        # Run manual sync
        sync_results = polling_scheduler.run_manual_sync(  # type: ignore
            days_back=days_back,
            days_forward=days_forward
        )
        
        return {
            'success': True,
            'message': 'Manual sync completed',
            'results': sync_results
        }
        
    except Exception as e:
        logger.error(f"Error running manual sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running manual sync: {str(e)}"
        )


@router.get("/google-calendar/accounts")
async def list_accounts(
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    List all configured Google Calendar accounts.
    
    Returns information about all configured accounts including
    connection status and calendar counts.
    """
    try:
        # Get services
        services = get_calendar_services()
        account_manager = services['account_manager']
        
        # Get account summaries
        account_summaries = account_manager.get_account_summary()  # type: ignore
        
        return {
            'accounts': account_summaries,
            'total_accounts': len(account_summaries),  # type: ignore
            'timestamp': account_summaries[0].get('last_updated') if account_summaries else None  # type: ignore
        }
        
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing accounts: {str(e)}"
        )


@router.get("/google-calendar/accounts/{account_id}/calendars")
async def list_calendars_for_account(
    account_id: int,
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    List calendars for a specific account.
    
    Returns all calendars accessible by the specified account.
    """
    try:
        # Get services
        services = get_calendar_services()
        account_manager = services['account_manager']
        
        # Get calendars for account
        calendars = account_manager.list_calendars_for_account(account_id)  # type: ignore
        
        return {
            'account_id': account_id,
            'calendars': calendars,
            'total_calendars': len(calendars)  # type: ignore
        }
        
    except Exception as e:
        logger.error(f"Error listing calendars for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing calendars: {str(e)}"
        )


@router.get("/google-calendar/sync-flows")
async def list_sync_flows(
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    List all configured sync flows.
    
    Returns information about all sync flows including
    source and target calendar details.
    """
    try:
        # Get services
        services = get_calendar_services()
        config = services['config']
        
        # Build sync flow details
        sync_flows = []
        for flow in config.sync_flows:  # type: ignore
            source_account = config.get_account_by_id(flow.source_account_id)  # type: ignore
            target_account = config.get_account_by_id(flow.target_account_id)  # type: ignore
            
            sync_flows.append({  # type: ignore
                'name': flow.name,  # type: ignore
                'source_account_id': flow.source_account_id,  # type: ignore
                'source_account_name': source_account.name if source_account else 'Unknown',  # type: ignore
                'source_calendar_id': flow.source_calendar_id,  # type: ignore
                'target_account_id': flow.target_account_id,  # type: ignore
                'target_account_name': target_account.name if target_account else 'Unknown',  # type: ignore
                'target_calendar_id': flow.target_calendar_id,  # type: ignore
                'start_offset': flow.start_offset,  # type: ignore
                'end_offset': flow.end_offset  # type: ignore
            })
        
        return {
            'sync_flows': sync_flows,
            'total_flows': len(sync_flows)  # type: ignore
        }
        
    except Exception as e:
        logger.error(f"Error listing sync flows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing sync flows: {str(e)}"
        )


@router.post("/google-calendar/scheduler/run-now")
async def run_scheduler_now(
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Force run the daily sync scheduler immediately.
    
    This endpoint triggers the daily sync job outside of the normal schedule.
    """
    try:
        # Get services
        services = get_calendar_services()
        polling_scheduler = services['polling_scheduler']
        
        # Force run
        polling_scheduler.force_run_now()  # type: ignore
        
        return {
            'success': True,
            'message': 'Scheduler run triggered successfully'
        }
        
    except Exception as e:
        logger.error(f"Error forcing scheduler run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error forcing scheduler run: {str(e)}"
        )


@router.get("/google-calendar/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for Google Calendar sync system.
    
    This endpoint does not require authentication and provides
    basic health information about the sync system.
    """
    try:
        # Get services (this will initialize them if needed)
        services = get_calendar_services()
        
        # Basic health check
        health_info = {  # type: ignore
            'status': 'healthy',
            'services': {
                'config': services['config'] is not None,
                'account_manager': services['account_manager'] is not None,
                'sync_engine': services['sync_engine'] is not None,
                'webhook_handler': services['webhook_handler'] is not None,
                'polling_scheduler': services['polling_scheduler'] is not None
            },
            'scheduler_running': services['polling_scheduler'].is_running,  # type: ignore
            'timestamp': services['sync_engine'].get_stats().last_updated  # type: ignore
        }
        
        return health_info  # type: ignore
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': None
        } 