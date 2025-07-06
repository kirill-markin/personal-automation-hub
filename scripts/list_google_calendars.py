#!/usr/bin/env python3
"""
Simple script to list all Google Calendar calendars for configured accounts.

This script displays all available calendars for each Google account
configured in GOOGLE_ACCOUNT_*** environment variables.

Usage:
    python scripts/list_google_calendars.py
"""

import os
import sys
import logging
from typing import List, TypedDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.google_calendar.config_loader import (
    load_multi_account_config,
    ConfigurationError
)
from backend.services.google_calendar.account_manager import AccountManager, AccountManagerError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalendarInfo(TypedDict):
    """Calendar information structure."""
    name: str
    id: str
    primary: bool
    access_role: str
    timezone: str
    description: str


class AccountResult(TypedDict):
    """Account result structure."""
    account_id: int
    account_name: str
    success: bool
    error: str | None
    calendars: List[CalendarInfo]


def get_calendars_for_account(account_manager: AccountManager, account_id: int) -> AccountResult:
    """Get all calendars for a specific account.
    
    Args:
        account_manager: AccountManager instance
        account_id: Account ID to get calendars for
        
    Returns:
        Dictionary with account info and calendars
    """
    result: AccountResult = {
        "account_id": account_id,
        "account_name": "Unknown",
        "success": False,
        "error": None,
        "calendars": []
    }
    
    try:
        # Get account info
        account = account_manager.get_account(account_id)
        if account:
            result["account_name"] = account.name
        
        # Test connection first
        logger.info(f"Testing connection to account {account_id}...")
        connection_ok = account_manager.test_account_connection(account_id)
        
        if not connection_ok:
            result["error"] = "Connection test failed"
            return result
        
        # Get calendars
        logger.info(f"Getting calendars for account {account_id}...")
        calendars = account_manager.list_calendars_for_account(account_id)
        
        # Process calendar data
        processed_calendars: List[CalendarInfo] = []
        for calendar in calendars:
            calendar_info: CalendarInfo = {
                "name": calendar.get('summary', 'Unknown'),
                "id": calendar.get('id', 'Unknown'),
                "primary": calendar.get('primary', False),
                "access_role": calendar.get('accessRole', 'unknown'),
                "timezone": calendar.get('timeZone', ''),
                "description": calendar.get('description', ''),
            }
            processed_calendars.append(calendar_info)
        
        result["calendars"] = processed_calendars
        result["success"] = True
        
        logger.info(f"✅ Account {account_id} ({result['account_name']}): {len(calendars)} calendars")
        
    except Exception as e:
        logger.error(f"❌ Account {account_id}: Error - {e}")
        result["error"] = str(e)
    
    return result


def display_calendars(results: List[AccountResult]) -> None:
    """Display calendars in a simple, readable format.
    
    Args:
        results: List of results from get_calendars_for_account
    """
    print("\n" + "="*80)
    print("GOOGLE CALENDAR LIST")
    print("="*80)
    
    for result in results:
        account_id = result["account_id"]
        account_name = result["account_name"]
        success = result["success"]
        error = result["error"]
        calendars = result["calendars"]
        
        print(f"\n🔵 Account {account_id}: {account_name}")
        print("-" * 60)
        
        if not success:
            print(f"❌ Error: {error}")
            continue
        
        if not calendars:
            print("❌ No calendars found")
            continue
        
        print(f"📅 Found {len(calendars)} calendars:")
        print()
        
        # Sort calendars: primary first, then by name
        sorted_calendars = sorted(
            calendars, 
            key=lambda x: (not x.get('primary', False), x.get('name', '').lower())
        )
        
        for i, calendar in enumerate(sorted_calendars, 1):
            name = calendar.get('name', 'Unknown')
            calendar_id = calendar.get('id', 'Unknown')
            is_primary = calendar.get('primary', False)
            access_role = calendar.get('access_role', 'unknown')
            timezone = calendar.get('timezone', '')
            description = calendar.get('description', '')
            
            # Format primary indicator
            primary_indicator = " 🟢 PRIMARY" if is_primary else ""
            
            print(f"  {i}. {name}{primary_indicator}")
            print(f"     ID: {calendar_id}")
            print(f"     Access: {access_role}")
            
            if timezone:
                print(f"     Timezone: {timezone}")
            
            if description:
                print(f"     Description: {description}")
            
            print()
    
    print("="*80)


def main() -> None:
    """Main function to list calendars for all accounts."""
    
    # Load configuration
    try:
        logger.info("Loading multi-account configuration...")
        config = load_multi_account_config()
        logger.info(f"Configuration loaded: {len(config.accounts)} accounts")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your GOOGLE_ACCOUNT_*** environment variables and try again.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    
    # Create account manager
    try:
        account_manager = AccountManager(config)
    except AccountManagerError as e:
        logger.error(f"AccountManager error: {e}")
        print(f"\n❌ AccountManager Error: {e}")
        sys.exit(1)
    
    # Get calendars for all accounts
    results: List[AccountResult] = []
    for account in config.accounts:
        result = get_calendars_for_account(account_manager, account.account_id)
        results.append(result)
    
    # Display results
    display_calendars(results)


if __name__ == "__main__":
    main() 