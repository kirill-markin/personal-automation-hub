#!/usr/bin/env python3
"""
List all calendars for configured Google accounts.

This script displays all available calendars for each Google account
configured in environment variables. This is useful for setting up
sync flows and finding the correct calendar IDs.

Usage:
    python scripts/list_calendars.py
    python scripts/list_calendars.py --account-id 1
    python scripts/list_calendars.py --json
"""

import os
import sys
import json
import argparse
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
    selected: bool
    description: str
    timezone: str
    background_color: str
    foreground_color: str


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
                "selected": calendar.get('selected', False),
                "description": calendar.get('description', ''),
                "timezone": calendar.get('timeZone', ''),
                "background_color": calendar.get('backgroundColor', ''),
                "foreground_color": calendar.get('foregroundColor', ''),
            }
            processed_calendars.append(calendar_info)
        
        result["calendars"] = processed_calendars
        result["success"] = True
        
        logger.info(f"✅ Account {account_id} ({result['account_name']}): {len(calendars)} calendars")
        
    except Exception as e:
        logger.error(f"❌ Account {account_id}: Error - {e}")
        result["error"] = str(e)
    
    return result


def display_calendars_formatted(results: List[AccountResult]) -> None:
    """Display calendars in a formatted, readable way.
    
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


def display_calendars_json(results: List[AccountResult]) -> None:
    """Display calendars in JSON format.
    
    Args:
        results: List of results from get_calendars_for_account
    """
    print(json.dumps(results, indent=2, ensure_ascii=False))


def display_copy_paste_format(results: List[AccountResult]) -> None:
    """Display calendars in copy-paste friendly format for .env configuration.
    
    Args:
        results: List of results from get_calendars_for_account
    """
    print("\n" + "="*80)
    print("COPY-PASTE FORMAT FOR .env CONFIGURATION")
    print("="*80)
    
    for result in results:
        if not result["success"]:
            continue
            
        account_id = result["account_id"]
        account_name = result["account_name"]
        calendars = result["calendars"]
        
        print(f"\n# Account {account_id}: {account_name}")
        
        for calendar in calendars:
            name = calendar.get('name', 'Unknown')
            calendar_id = calendar.get('id', 'Unknown')
            is_primary = calendar.get('primary', False)
            
            # Clean name for comment
            clean_name = name.replace(' ', '_').replace('-', '_')
            primary_note = " (PRIMARY)" if is_primary else ""
            
            print(f"# {name}{primary_note}")
            print(f"# CALENDAR_ID_{account_id}_{clean_name.upper()}={calendar_id}")
            print()
    
    print("="*80)


def main() -> None:
    """Main function to list calendars for all accounts."""
    parser = argparse.ArgumentParser(description="List calendars for configured Google accounts")
    parser.add_argument(
        "--account-id",
        type=int,
        help="Show calendars for specific account ID only"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    parser.add_argument(
        "--copy-paste",
        action="store_true",
        help="Output in copy-paste friendly format for .env configuration"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        logger.info("Loading multi-account configuration...")
        config = load_multi_account_config()
        logger.info(f"Configuration loaded: {len(config.accounts)} accounts")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your environment variables and try again.")
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
    
    # Get calendars
    results: List[AccountResult] = []
    
    if args.account_id:
        # Get calendars for specific account
        if not any(acc.account_id == args.account_id for acc in config.accounts):
            print(f"❌ Account {args.account_id} not found in configuration")
            sys.exit(1)
        
        result = get_calendars_for_account(account_manager, args.account_id)
        results.append(result)
    else:
        # Get calendars for all accounts
        for account in config.accounts:
            result = get_calendars_for_account(account_manager, account.account_id)
            results.append(result)
    
    # Display results
    if args.json:
        display_calendars_json(results)
    elif args.copy_paste:
        display_copy_paste_format(results)
    else:
        display_calendars_formatted(results)


if __name__ == "__main__":
    main() 