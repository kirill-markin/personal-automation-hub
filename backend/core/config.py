"""
Application configuration settings.

This module defines all configuration settings for the Personal Automation Hub,
including API keys, database connections, and Google Calendar integration settings.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from .llm_models import DEFAULT_CATEGORIZATION_MODEL, DEFAULT_DRAFT_GENERATION_MODEL


class NotionConfig(BaseModel):
    """Notion integration configuration."""
    api_key: str = Field(..., description="Notion API key")
    database_id: str = Field(..., description="Notion tasks database ID")


class GoogleCalendarConfig(BaseModel):
    """Google Calendar integration configuration."""
    
    # Shared OAuth2 credentials (optional - accounts can have their own)
    client_id: Optional[str] = Field(None, description="Shared Google OAuth2 client ID")
    client_secret: Optional[str] = Field(None, description="Shared Google OAuth2 client secret")
    
    # Polling settings
    daily_sync_hour: int = Field(default=6, description="Hour for daily sync (0-23)")
    daily_sync_timezone: str = Field(default="UTC", description="Timezone for daily sync")
    
    # Account discovery settings
    max_accounts: int = Field(default=10, description="Maximum number of accounts to scan for")
    max_sync_flows: int = Field(default=50, description="Maximum number of sync flows to scan for")


class OpenRouterConfig(BaseModel):
    """OpenRouter LLM integration configuration."""
    api_key: str = Field(..., description="OpenRouter API key")
    categorization_model: str = Field(default=DEFAULT_CATEGORIZATION_MODEL, description="Model for email categorization")
    draft_generation_model: str = Field(default=DEFAULT_DRAFT_GENERATION_MODEL, description="Model for draft generation")


class GoogleCloudConfig(BaseModel):
    """Google Cloud integration configuration."""
    project_id: str = Field(..., description="Google Cloud project ID")
    pubsub_topic: str = Field(default="gmail-notifications", description="Pub/Sub topic for Gmail notifications")
    pubsub_subscription: str = Field(default="gmail-notifications-sub", description="Pub/Sub subscription name")


class SecurityConfig(BaseModel):
    """Security configuration."""
    webhook_api_key: str = Field(..., description="API key for webhook endpoints")
    

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = Field(default="Personal Automation Hub", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    
    # Notion configuration
    notion_api_key: str = Field(..., description="Notion API key")
    notion_database_id: str = Field(..., description="Notion personal database ID")
    
    # Security
    webhook_api_key: str = Field(..., description="Webhook API key")
    webhook_base_url: str = Field(..., description="Base URL for webhook endpoints (e.g., https://server.com:8000). Must be https.")
    
    # Google Calendar shared credentials (optional)
    google_client_id: Optional[str] = Field(None, description="Google OAuth2 client ID")
    google_client_secret: Optional[str] = Field(None, description="Google OAuth2 client secret")
    
    # Google Calendar polling settings
    daily_sync_hour: int = Field(default=6, description="Daily sync hour (0-23)")
    daily_sync_timezone: str = Field(default="UTC", description="Daily sync timezone")
    
    # Account discovery limits
    max_google_accounts: int = Field(default=10, description="Maximum accounts to scan")
    max_sync_flows: int = Field(default=50, description="Maximum sync flows to scan")
    
    # OpenRouter LLM settings
    openrouter_api_key: Optional[str] = Field(None, description="OpenRouter API key")
    openrouter_categorization_model: str = Field(default=DEFAULT_CATEGORIZATION_MODEL, description="Model for email categorization")
    openrouter_draft_generation_model: str = Field(default=DEFAULT_DRAFT_GENERATION_MODEL, description="Model for draft generation")
    
    # Google Cloud settings
    google_cloud_project_id: Optional[str] = Field(None, description="Google Cloud project ID")
    google_cloud_pubsub_topic: str = Field(default="gmail-notifications", description="Pub/Sub topic for Gmail notifications")
    google_cloud_pubsub_subscription: str = Field(default="gmail-notifications-sub", description="Pub/Sub subscription name")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
        
    @property
    def notion_config(self) -> NotionConfig:
        """Get Notion configuration."""
        return NotionConfig(
            api_key=self.notion_api_key,
            database_id=self.notion_database_id
        )
    
    @property
    def google_calendar_config(self) -> GoogleCalendarConfig:
        """Get Google Calendar configuration."""
        return GoogleCalendarConfig(
            client_id=self.google_client_id,
            client_secret=self.google_client_secret,
            daily_sync_hour=self.daily_sync_hour,
            daily_sync_timezone=self.daily_sync_timezone,
            max_accounts=self.max_google_accounts,
            max_sync_flows=self.max_sync_flows
        )
    
    @property
    def security_config(self) -> SecurityConfig:
        """Get security configuration."""
        return SecurityConfig(
            webhook_api_key=self.webhook_api_key
        )
    
    @property
    def openrouter_config(self) -> Optional[OpenRouterConfig]:
        """Get OpenRouter configuration."""
        if not self.openrouter_api_key:
            return None
        return OpenRouterConfig(
            api_key=self.openrouter_api_key,
            categorization_model=self.openrouter_categorization_model,
            draft_generation_model=self.openrouter_draft_generation_model
        )
    
    @property
    def google_cloud_config(self) -> Optional[GoogleCloudConfig]:
        """Get Google Cloud configuration."""
        if not self.google_cloud_project_id:
            return None
        return GoogleCloudConfig(
            project_id=self.google_cloud_project_id,
            pubsub_topic=self.google_cloud_pubsub_topic,
            pubsub_subscription=self.google_cloud_pubsub_subscription
        )


def discover_google_accounts(max_accounts: int = 10) -> Dict[str, Any]:
    """Discover Google accounts from environment variables.
    
    Args:
        max_accounts: Maximum number of accounts to scan for
        
    Returns:
        Dictionary with account discovery results
    """
    accounts: Dict[int, Dict[str, Any]] = {}
    
    for account_id in range(1, max_accounts + 1):
        account_env_vars = {
            'email': f"GOOGLE_ACCOUNT_{account_id}_EMAIL",
            'client_id': f"GOOGLE_ACCOUNT_{account_id}_CLIENT_ID",
            'client_secret': f"GOOGLE_ACCOUNT_{account_id}_CLIENT_SECRET",
            'refresh_token': f"GOOGLE_ACCOUNT_{account_id}_REFRESH_TOKEN"
        }
        
        # Check if account exists (at least email variable is set)
        if account_env_vars['email'] in os.environ:
            account_data = {
                'account_id': account_id,
                'email': os.environ.get(account_env_vars['email'], ''),
                'has_client_id': bool(os.environ.get(account_env_vars['client_id'], '')),
                'has_client_secret': bool(os.environ.get(account_env_vars['client_secret'], '')),
                'has_refresh_token': bool(os.environ.get(account_env_vars['refresh_token'], '')),
                'complete': all(
                    os.environ.get(var, '') 
                    for var in account_env_vars.values()
                )
            }
            accounts[account_id] = account_data
    
    return {
        'accounts': accounts,
        'total_found': len(accounts),
        'complete_accounts': len([acc for acc in accounts.values() if acc['complete']])
    }


def discover_sync_flows(max_flows: int = 50) -> Dict[str, Any]:
    """Discover sync flows from environment variables.
    
    Args:
        max_flows: Maximum number of sync flows to scan for
        
    Returns:
        Dictionary with sync flow discovery results
    """
    flows: Dict[int, Dict[str, Any]] = {}
    
    for flow_id in range(1, max_flows + 1):
        flow_env_vars = {
            'name': f"SYNC_FLOW_{flow_id}_NAME",
            'source_account_id': f"SYNC_FLOW_{flow_id}_SOURCE_ACCOUNT_ID",
            'source_calendar_id': f"SYNC_FLOW_{flow_id}_SOURCE_CALENDAR_ID",
            'target_account_id': f"SYNC_FLOW_{flow_id}_TARGET_ACCOUNT_ID",
            'target_calendar_id': f"SYNC_FLOW_{flow_id}_TARGET_CALENDAR_ID",
            'start_offset': f"SYNC_FLOW_{flow_id}_START_OFFSET",
            'end_offset': f"SYNC_FLOW_{flow_id}_END_OFFSET"
        }
        
        # Check if flow exists (at least name variable is set)
        if flow_env_vars['name'] in os.environ:
            flow_data = {
                'flow_id': flow_id,
                'name': os.environ.get(flow_env_vars['name'], ''),
                'source_account_id': os.environ.get(flow_env_vars['source_account_id'], ''),
                'source_calendar_id': os.environ.get(flow_env_vars['source_calendar_id'], ''),
                'target_account_id': os.environ.get(flow_env_vars['target_account_id'], ''),
                'target_calendar_id': os.environ.get(flow_env_vars['target_calendar_id'], ''),
                'start_offset': os.environ.get(flow_env_vars['start_offset'], ''),
                'end_offset': os.environ.get(flow_env_vars['end_offset'], ''),
                'complete': all(
                    os.environ.get(var, '') 
                    for var in flow_env_vars.values()
                )
            }
            flows[flow_id] = flow_data
    
    return {
        'flows': flows,
        'total_found': len(flows),
        'complete_flows': len([flow for flow in flows.values() if flow['complete']])
    }


def get_environment_summary() -> Dict[str, Any]:
    """Get summary of environment configuration.
    
    Returns:
        Dictionary with environment configuration summary
    """
    try:
        settings: Settings = Settings()  # type: ignore
        
        # Basic settings
        summary: Dict[str, Any] = {
            'app_name': settings.app_name,
            'debug': settings.debug,
            'api_v1_prefix': settings.api_v1_prefix,
            'notion_configured': bool(settings.notion_api_key and settings.notion_database_id),
            'webhook_api_key_configured': bool(settings.webhook_api_key),
            'google_shared_credentials': bool(settings.google_client_id and settings.google_client_secret),
            'daily_sync_hour': settings.daily_sync_hour,
            'daily_sync_timezone': settings.daily_sync_timezone
        }
        
        # Discover Google accounts
        accounts_info = discover_google_accounts(settings.max_google_accounts)
        summary['google_accounts'] = accounts_info
        
        # Discover sync flows
        flows_info = discover_sync_flows(settings.max_sync_flows)
        summary['sync_flows'] = flows_info
        
        # Overall status
        summary['ready_for_sync'] = (
            accounts_info['complete_accounts'] > 0 and 
            flows_info['complete_flows'] > 0
        )
        
        return summary
        
    except Exception as e:
        return {
            'error': str(e),
            'ready_for_sync': False
        }


# Global settings instance
settings = Settings()  # type: ignore


# Export commonly used configurations
notion_config = settings.notion_config
google_calendar_config = settings.google_calendar_config
security_config = settings.security_config
openrouter_config = settings.openrouter_config
google_cloud_config = settings.google_cloud_config 