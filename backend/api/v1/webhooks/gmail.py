"""
Gmail webhook endpoint for handling Google Cloud Pub/Sub notifications.

This endpoint receives Gmail push notifications via Google Cloud Pub/Sub
and processes them for email automation.
"""

import logging
import base64
import json
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.core.security import validate_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


class PubSubMessage(BaseModel):
    """Pub/Sub message model."""
    data: str = Field(..., description="Base64-encoded message data")
    messageId: str = Field(..., description="Unique message ID")
    publishTime: str = Field(..., description="Message publish time")


class PubSubNotification(BaseModel):
    """Pub/Sub notification model."""
    message: PubSubMessage = Field(..., description="Pub/Sub message")
    subscription: str = Field(..., description="Subscription name")


@router.post("/gmail/pubsub")
async def handle_gmail_pubsub_notification(
    notification: PubSubNotification,
    request: Request,
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Handle Gmail push notification from Google Cloud Pub/Sub.
    
    Args:
        notification: Pub/Sub notification with Gmail data
        request: FastAPI request object
        api_key: API key for authentication
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"📧 Received Gmail notification: {notification.message.messageId}")
        
        # Decode the Pub/Sub message data
        try:
            decoded_data = base64.b64decode(notification.message.data).decode('utf-8')
            gmail_data = json.loads(decoded_data)
            logger.info(f"🔓 Decoded Gmail data: {gmail_data}")
        except Exception as e:
            logger.error(f"❌ Failed to decode Pub/Sub message: {e}")
            raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")
        
        # Extract Gmail notification details
        email_address = gmail_data.get('emailAddress')
        history_id = gmail_data.get('historyId')
        
        if not email_address or not history_id:
            logger.error(f"❌ Missing required Gmail data: email={email_address}, historyId={history_id}")
            raise HTTPException(status_code=400, detail="Missing required Gmail notification data")
        
        logger.info(f"📬 Processing Gmail notification for: {email_address}, historyId: {history_id}")
        
        # TODO: Implement email processing logic
        # For now, just log the notification
        logger.info(f"✅ Gmail notification processed successfully")
        
        return {
            "status": "success",
            "message": "Gmail notification processed",
            "data": {
                "email_address": email_address,
                "history_id": history_id,
                "message_id": notification.message.messageId
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Error processing Gmail notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/gmail/health")
async def gmail_health_check() -> Dict[str, str]:
    """
    Health check endpoint for Gmail webhook.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "gmail-webhook",
        "message": "Gmail webhook is ready to receive notifications"
    }


@router.post("/gmail/manual-process")
async def manual_process_emails(
    request: Request,
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Manual email processing endpoint for user-triggered actions.
    
    Args:
        request: FastAPI request object
        api_key: API key for authentication
        
    Returns:
        Processing result
    """
    # TODO: Implement manual email processing
    return {
        "status": "success",
        "message": "Manual email processing endpoint (not implemented yet)",
        "available_actions": [
            "process_unread_emails",
            "categorize_emails",
            "generate_drafts"
        ]
    }


@router.get("/gmail/status")
async def get_gmail_status(
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Get Gmail automation status for all accounts.
    
    Args:
        api_key: API key for authentication
        
    Returns:
        Status information
    """
    # TODO: Implement status check
    return {
        "status": "active",
        "message": "Gmail automation status (not implemented yet)",
        "accounts": [],
        "last_processed": None,
        "pending_emails": 0
    }


@router.post("/gmail/test")
async def test_gmail_endpoint(
    request: Request,
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Test endpoint for Gmail webhook development.
    
    Args:
        request: FastAPI request object
        api_key: API key for authentication
        
    Returns:
        Test result
    """
    return {
        "status": "success",
        "message": "Gmail test endpoint working",
        "timestamp": "2024-01-01T00:00:00Z",
        "endpoints": {
            "pubsub": "/api/v1/webhooks/gmail/pubsub",
            "health": "/api/v1/webhooks/gmail/health", 
            "manual_process": "/api/v1/webhooks/gmail/manual-process",
            "status": "/api/v1/webhooks/gmail/status",
            "test": "/api/v1/webhooks/gmail/test"
        }
    } 