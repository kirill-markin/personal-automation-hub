"""
Configuration loader for Google Calendar synchronization.

This module loads configuration from environment variables and creates
MultiAccountConfig instances for managing multiple Google accounts and sync flows.
"""

import os
import logging
from typing import Dict, List, Any

from backend.models.calendar import (
    GoogleAccount, 
    SyncFlow, 
    MultiAccountConfig
)

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Exception raised when configuration loading fails."""
    pass


def load_google_accounts_from_env() -> List[GoogleAccount]:
    """Load Google accounts from environment variables.
    
    Expected environment variables:
    - GOOGLE_ACCOUNT_N_NAME: Human-readable name for account N
    - GOOGLE_ACCOUNT_N_CLIENT_ID: OAuth2 client ID for account N
    - GOOGLE_ACCOUNT_N_CLIENT_SECRET: OAuth2 client secret for account N
    - GOOGLE_ACCOUNT_N_REFRESH_TOKEN: OAuth2 refresh token for account N
    
    Where N is a positive integer (1, 2, 3, ...)
    
    Returns:
        List of GoogleAccount instances
        
    Raises:
        ConfigurationError: If required environment variables are missing
    """
    accounts: List[GoogleAccount] = []
    account_id = 1
    
    while True:
        # Check for account configuration
        name_key = f"GOOGLE_ACCOUNT_{account_id}_NAME"
        client_id_key = f"GOOGLE_ACCOUNT_{account_id}_CLIENT_ID"
        client_secret_key = f"GOOGLE_ACCOUNT_{account_id}_CLIENT_SECRET"
        refresh_token_key = f"GOOGLE_ACCOUNT_{account_id}_REFRESH_TOKEN"
        
        # If the first key doesn't exist, stop looking
        if name_key not in os.environ:
            break
        
        # Validate all required keys exist
        missing_keys: List[str] = []
        for key in [name_key, client_id_key, client_secret_key, refresh_token_key]:
            if key not in os.environ or not os.environ[key].strip():
                missing_keys.append(key)
        
        if missing_keys:
            raise ConfigurationError(f"Missing or empty environment variables for account {account_id}: {', '.join(missing_keys)}")
        
        # Create account
        account = GoogleAccount(
            account_id=account_id,
            name=os.environ[name_key].strip(),
            client_id=os.environ[client_id_key].strip(),
            client_secret=os.environ[client_secret_key].strip(),
            refresh_token=os.environ[refresh_token_key].strip()
        )
        
        accounts.append(account)
        logger.info(f"Loaded account {account_id}: {account.name}")
        
        account_id += 1
    
    if not accounts:
        raise ConfigurationError("No Google accounts configured. Please set GOOGLE_ACCOUNT_1_* environment variables.")
    
    return accounts


def load_sync_flows_from_env() -> List[SyncFlow]:
    """Load sync flows from environment variables.
    
    Expected environment variables:
    - SYNC_FLOW_N_NAME: Human-readable name for sync flow N
    - SYNC_FLOW_N_SOURCE_ACCOUNT_ID: Source account ID for sync flow N
    - SYNC_FLOW_N_SOURCE_CALENDAR_ID: Source calendar ID for sync flow N
    - SYNC_FLOW_N_TARGET_ACCOUNT_ID: Target account ID for sync flow N
    - SYNC_FLOW_N_TARGET_CALENDAR_ID: Target calendar ID for sync flow N
    - SYNC_FLOW_N_START_OFFSET: Start offset in minutes for sync flow N
    - SYNC_FLOW_N_END_OFFSET: End offset in minutes for sync flow N
    
    Where N is a positive integer (1, 2, 3, ...)
    
    Returns:
        List of SyncFlow instances
        
    Raises:
        ConfigurationError: If required environment variables are missing or invalid
    """
    flows: List[SyncFlow] = []
    flow_id = 1
    
    while True:
        # Check for flow configuration
        name_key = f"SYNC_FLOW_{flow_id}_NAME"
        source_account_key = f"SYNC_FLOW_{flow_id}_SOURCE_ACCOUNT_ID"
        source_calendar_key = f"SYNC_FLOW_{flow_id}_SOURCE_CALENDAR_ID"
        target_account_key = f"SYNC_FLOW_{flow_id}_TARGET_ACCOUNT_ID"
        target_calendar_key = f"SYNC_FLOW_{flow_id}_TARGET_CALENDAR_ID"
        start_offset_key = f"SYNC_FLOW_{flow_id}_START_OFFSET"
        end_offset_key = f"SYNC_FLOW_{flow_id}_END_OFFSET"
        
        # If the first key doesn't exist, stop looking
        if name_key not in os.environ:
            break
        
        # Validate all required keys exist
        missing_keys: List[str] = []
        for key in [name_key, source_account_key, source_calendar_key, 
                   target_account_key, target_calendar_key, start_offset_key, end_offset_key]:
            if key not in os.environ or not os.environ[key].strip():
                missing_keys.append(key)
        
        if missing_keys:
            raise ConfigurationError(f"Missing or empty environment variables for sync flow {flow_id}: {', '.join(missing_keys)}")
        
        # Parse and validate numeric values
        try:
            source_account_id = int(os.environ[source_account_key].strip())
            target_account_id = int(os.environ[target_account_key].strip())
            start_offset = int(os.environ[start_offset_key].strip())
            end_offset = int(os.environ[end_offset_key].strip())
        except ValueError as e:
            raise ConfigurationError(f"Invalid numeric value in sync flow {flow_id}: {e}")
        
        # Create sync flow
        flow = SyncFlow(
            name=os.environ[name_key].strip(),
            source_account_id=source_account_id,
            source_calendar_id=os.environ[source_calendar_key].strip(),
            target_account_id=target_account_id,
            target_calendar_id=os.environ[target_calendar_key].strip(),
            start_offset=start_offset,
            end_offset=end_offset
        )
        
        flows.append(flow)
        logger.info(f"Loaded sync flow {flow_id}: {flow.name}")
        
        flow_id += 1
    
    if not flows:
        raise ConfigurationError("No sync flows configured. Please set SYNC_FLOW_1_* environment variables.")
    
    return flows


def load_multi_account_config() -> MultiAccountConfig:
    """Load complete multi-account configuration from environment variables.
    
    Returns:
        MultiAccountConfig instance with all accounts and sync flows
        
    Raises:
        ConfigurationError: If configuration is invalid or incomplete
    """
    try:
        # Load accounts
        accounts = load_google_accounts_from_env()
        
        # Load sync flows
        sync_flows = load_sync_flows_from_env()
        
        # Load polling settings
        daily_sync_hour = int(os.environ.get("DAILY_SYNC_HOUR", "6"))
        daily_sync_timezone = os.environ.get("DAILY_SYNC_TIMEZONE", "UTC")
        
        # Create configuration
        config = MultiAccountConfig(
            accounts=accounts,
            sync_flows=sync_flows,
            daily_sync_hour=daily_sync_hour,
            daily_sync_timezone=daily_sync_timezone
        )
        
        logger.info(f"Loaded configuration: {len(accounts)} accounts, {len(sync_flows)} sync flows")
        
        return config
        
    except Exception as e:
        raise ConfigurationError(f"Failed to load multi-account configuration: {e}")


def validate_environment_variables() -> Dict[str, str]:
    """Validate that required environment variables are present.
    
    Returns:
        Dictionary of validation results
        
    Raises:
        ConfigurationError: If critical environment variables are missing
    """
    validation_results: Dict[str, str] = {}
    
    try:
        # Try to load accounts
        accounts = load_google_accounts_from_env()
        validation_results["accounts"] = f"Found {len(accounts)} accounts"
        
        # Try to load sync flows
        sync_flows = load_sync_flows_from_env()
        validation_results["sync_flows"] = f"Found {len(sync_flows)} sync flows"
        
        # Check polling settings
        daily_sync_hour = int(os.environ.get("DAILY_SYNC_HOUR", "6"))
        if not (0 <= daily_sync_hour <= 23):
            validation_results["daily_sync_hour"] = "Invalid hour (must be 0-23)"
        else:
            validation_results["daily_sync_hour"] = f"Hour: {daily_sync_hour}"
        
        daily_sync_timezone = os.environ.get("DAILY_SYNC_TIMEZONE", "UTC")
        validation_results["daily_sync_timezone"] = f"Timezone: {daily_sync_timezone}"
        
        # Try to create full configuration to validate cross-references
        MultiAccountConfig(
            accounts=accounts,
            sync_flows=sync_flows,
            daily_sync_hour=daily_sync_hour,
            daily_sync_timezone=daily_sync_timezone
        )
        
        validation_results["validation"] = "All validations passed"
        
    except Exception as e:
        validation_results["error"] = str(e)
        raise ConfigurationError(f"Environment validation failed: {e}")
    
    return validation_results


def get_configuration_summary() -> Dict[str, Any]:
    """Get summary of current configuration without validating.
    
    Returns:
        Dictionary with configuration summary
    """
    summary: Dict[str, Any] = {
        "accounts": [],
        "sync_flows": [],
        "polling_settings": {},
        "validation_status": "unknown"
    }
    
    # Check accounts
    account_id = 1
    while True:
        name_key = f"GOOGLE_ACCOUNT_{account_id}_NAME"
        if name_key not in os.environ:
            break
        
        account_info = {
            "account_id": account_id,
            "name": os.environ.get(name_key, ""),
            "has_client_id": bool(os.environ.get(f"GOOGLE_ACCOUNT_{account_id}_CLIENT_ID", "")),
            "has_client_secret": bool(os.environ.get(f"GOOGLE_ACCOUNT_{account_id}_CLIENT_SECRET", "")),
            "has_refresh_token": bool(os.environ.get(f"GOOGLE_ACCOUNT_{account_id}_REFRESH_TOKEN", ""))
        }
        summary["accounts"].append(account_info)  # type: ignore
        account_id += 1
    
    # Check sync flows
    flow_id = 1
    while True:
        name_key = f"SYNC_FLOW_{flow_id}_NAME"
        if name_key not in os.environ:
            break
        
        flow_info = {
            "flow_id": flow_id,
            "name": os.environ.get(name_key, ""),
            "source_account_id": os.environ.get(f"SYNC_FLOW_{flow_id}_SOURCE_ACCOUNT_ID", ""),
            "source_calendar_id": os.environ.get(f"SYNC_FLOW_{flow_id}_SOURCE_CALENDAR_ID", ""),
            "target_account_id": os.environ.get(f"SYNC_FLOW_{flow_id}_TARGET_ACCOUNT_ID", ""),
            "target_calendar_id": os.environ.get(f"SYNC_FLOW_{flow_id}_TARGET_CALENDAR_ID", ""),
            "start_offset": os.environ.get(f"SYNC_FLOW_{flow_id}_START_OFFSET", ""),
            "end_offset": os.environ.get(f"SYNC_FLOW_{flow_id}_END_OFFSET", "")
        }
        summary["sync_flows"].append(flow_info)  # type: ignore
        flow_id += 1
    
    # Check polling settings
    summary["polling_settings"] = {
        "daily_sync_hour": os.environ.get("DAILY_SYNC_HOUR", "6"),
        "daily_sync_timezone": os.environ.get("DAILY_SYNC_TIMEZONE", "UTC")
    }
    
    # Try validation
    try:
        validate_environment_variables()
        summary["validation_status"] = "valid"
    except Exception as e:
        summary["validation_status"] = f"invalid: {e}"
    
    return summary


 