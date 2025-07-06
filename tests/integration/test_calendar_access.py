#!/usr/bin/env python3
"""
Integration tests for Google Calendar access with multiple accounts.

This script tests the calendar synchronization system by:
1. Loading multi-account configuration from environment variables
2. Testing connection to each configured Google account
3. Listing available calendars for each account
4. Verifying sync flow configurations

Usage:
    # As pytest integration test
    python -m pytest tests/integration/test_calendar_access.py -v -m integration
    
    # As standalone script
    python tests/integration/test_calendar_access.py
    python tests/integration/test_calendar_access.py --account-id 1
    python tests/integration/test_calendar_access.py --list-flows
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import pytest

# Load environment variables from .env file
load_dotenv(override=True)

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.google_calendar.config_loader import (
    load_multi_account_config,
    get_configuration_summary,
    ConfigurationError
)
from backend.services.google_calendar.account_manager import AccountManager, AccountManagerError
from backend.models.calendar import MultiAccountConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.integration
def test_load_configuration():
    """Test loading multi-account configuration from environment variables."""
    config = load_multi_account_config()
    assert len(config.accounts) > 0, "No accounts configured"
    assert len(config.sync_flows) > 0, "No sync flows configured"
    
    # Validate each account has required fields
    for account in config.accounts:
        assert account.account_id is not None, f"Account {account.name} missing account_id"
        assert account.name, f"Account {account.account_id} missing name"
        assert account.client_id, f"Account {account.name} missing client_id"
        assert account.client_secret, f"Account {account.name} missing client_secret"
        assert account.refresh_token, f"Account {account.name} missing refresh_token"


@pytest.mark.integration
def test_account_manager_creation():
    """Test creating AccountManager with loaded configuration."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    
    # Test that all accounts are accessible
    for account in config.accounts:
        retrieved_account = account_manager.get_account(account.account_id)
        assert retrieved_account is not None, f"Account {account.account_id} not found in manager"
        assert retrieved_account.name == account.name, f"Account name mismatch for {account.account_id}"


@pytest.mark.integration
def test_account_connections():
    """Test connections to all configured Google accounts."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    
    for account in config.accounts:
        logger.info(f"Testing connection to account {account.account_id} ({account.name})...")
        connection_ok = account_manager.test_account_connection(account.account_id)
        assert connection_ok, f"Connection failed for account {account.account_id} ({account.name})"


@pytest.mark.integration
def test_calendar_access():
    """Test calendar access for all configured accounts."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    
    for account in config.accounts:
        logger.info(f"Testing calendar access for account {account.account_id} ({account.name})...")
        calendars = account_manager.list_calendars_for_account(account.account_id)
        assert len(calendars) > 0, f"No calendars found for account {account.account_id} ({account.name})"


@pytest.mark.integration
def test_sync_flow_validation():
    """Test sync flow configurations and calendar access."""
    config = load_multi_account_config()
    account_manager = AccountManager(config)
    
    for flow in config.sync_flows:
        logger.info(f"Testing sync flow: {flow.name}")
        
        # Test source account exists
        source_account = account_manager.get_account(flow.source_account_id)
        assert source_account is not None, f"Source account {flow.source_account_id} not found for flow {flow.name}"
        
        # Test target account exists
        target_account = account_manager.get_account(flow.target_account_id)
        assert target_account is not None, f"Target account {flow.target_account_id} not found for flow {flow.name}"
        
        # Test source calendar access
        source_calendars = account_manager.list_calendars_for_account(flow.source_account_id)
        source_found = any(cal.get('id') == flow.source_calendar_id for cal in source_calendars)
        assert source_found, f"Source calendar {flow.source_calendar_id} not found for flow {flow.name}"
        
        # Test target calendar access
        target_calendars = account_manager.list_calendars_for_account(flow.target_account_id)
        target_found = any(cal.get('id') == flow.target_calendar_id for cal in target_calendars)
        assert target_found, f"Target calendar {flow.target_calendar_id} not found for flow {flow.name}"


def check_single_account(account_manager: AccountManager, account_id: int) -> Dict[str, Any]:
    """Test access to a single Google account.
    
    Args:
        account_manager: AccountManager instance
        account_id: Account ID to test
        
    Returns:
        Test results dictionary
    """
    results = {  # type: ignore
        "account_id": account_id,
        "account_name": "Unknown",
        "connection_test": False,
        "calendar_count": 0,
        "calendars": [],
        "error": None
    }
    
    try:
        # Get account info
        account = account_manager.get_account(account_id)
        if account:
            results["account_name"] = account.name
        
        # Test connection
        logger.info(f"Testing connection to account {account_id}...")
        connection_ok = account_manager.test_account_connection(account_id)
        results["connection_test"] = connection_ok
        
        if connection_ok:
            # List calendars
            logger.info(f"Listing calendars for account {account_id}...")
            calendars = account_manager.list_calendars_for_account(account_id)
            results["calendar_count"] = len(calendars)
            results["calendars"] = calendars
            
            logger.info(f"✅ Account {account_id} ({results['account_name']}): {len(calendars)} calendars")
        else:
            logger.error(f"❌ Account {account_id} ({results['account_name']}): Connection failed")
            results["error"] = "Connection test failed"
            
    except Exception as e:
        logger.error(f"❌ Account {account_id}: Error - {e}")
        results["error"] = str(e)
    
    return results  # type: ignore


def check_all_accounts(config: MultiAccountConfig) -> List[Dict[str, Any]]:
    """Test access to all configured Google accounts.
    
    Args:
        config: Multi-account configuration
        
    Returns:
        List of test results for each account
    """
    logger.info(f"Testing access to {len(config.accounts)} configured accounts...")
    
    # Create account manager
    try:
        account_manager = AccountManager(config)
    except AccountManagerError as e:
        logger.error(f"Failed to create AccountManager: {e}")
        return []
    
    results = []
    
    # Test each account
    for account in config.accounts:
        result = check_single_account(account_manager, account.account_id)
        results.append(result)  # type: ignore
    
    return results  # type: ignore


def display_account_results(results: List[Dict[str, Any]]) -> None:
    """Display detailed results for account tests.
    
    Args:
        results: List of test results from test_all_accounts
    """
    print("\n" + "="*60)
    print("GOOGLE CALENDAR ACCESS TEST RESULTS")
    print("="*60)
    
    for result in results:
        account_id = result["account_id"]
        account_name = result["account_name"]
        connection_ok = result["connection_test"]
        calendar_count = result["calendar_count"]
        calendars = result["calendars"]
        error = result["error"]
        
        print(f"\nAccount {account_id}: {account_name}")
        print("-" * 40)
        
        if error:
            print(f"❌ Error: {error}")
            continue
        
        if connection_ok:
            print(f"✅ Connection: OK")
            print(f"📅 Calendars: {calendar_count}")
            
            if calendars:
                print("\nAvailable calendars:")
                for i, calendar in enumerate(calendars, 1):
                    primary_marker = " (PRIMARY)" if calendar.get('primary', False) else ""
                    access_role = calendar.get('accessRole', 'unknown')
                    print(f"  {i}. {calendar.get('summary', 'Unknown')} {primary_marker}")
                    print(f"     ID: {calendar.get('id', 'Unknown')}")
                    print(f"     Access: {access_role}")
                    print()
        else:
            print(f"❌ Connection: FAILED")
    
    print("="*60)


def check_sync_flows(config: MultiAccountConfig) -> None:
    """Test sync flow configurations.
    
    Args:
        config: Multi-account configuration
    """
    print("\n" + "="*60)
    print("SYNC FLOW CONFIGURATION TEST")
    print("="*60)
    
    if not config.sync_flows:
        print("❌ No sync flows configured")
        return
    
    try:
        account_manager = AccountManager(config)
    except AccountManagerError as e:
        logger.error(f"Failed to create AccountManager: {e}")
        return
    
    print(f"Found {len(config.sync_flows)} sync flows:")
    
    for i, flow in enumerate(config.sync_flows, 1):
        print(f"\n{i}. {flow.name}")
        print("-" * 40)
        
        # Check source account
        source_account = account_manager.get_account(flow.source_account_id)
        if source_account:
            print(f"✅ Source: Account {flow.source_account_id} ({source_account.name})")
            print(f"   Calendar: {flow.source_calendar_id}")
        else:
            print(f"❌ Source: Account {flow.source_account_id} (NOT FOUND)")
        
        # Check target account
        target_account = account_manager.get_account(flow.target_account_id)
        if target_account:
            print(f"✅ Target: Account {flow.target_account_id} ({target_account.name})")
            print(f"   Calendar: {flow.target_calendar_id}")
        else:
            print(f"❌ Target: Account {flow.target_account_id} (NOT FOUND)")
        
        # Display timing
        print(f"⏰ Timing: {flow.start_offset} min before → {flow.end_offset} min after")
        
        # Test calendar access
        try:
            if source_account:
                source_calendars = account_manager.list_calendars_for_account(flow.source_account_id)
                source_found = any(cal.get('id') == flow.source_calendar_id for cal in source_calendars)
                print(f"📅 Source calendar access: {'✅' if source_found else '❌'}")
            
            if target_account:
                target_calendars = account_manager.list_calendars_for_account(flow.target_account_id)
                target_found = any(cal.get('id') == flow.target_calendar_id for cal in target_calendars)
                print(f"📅 Target calendar access: {'✅' if target_found else '❌'}")
                
        except Exception as e:
            print(f"❌ Calendar access test failed: {e}")
    
    print("="*60)


def display_configuration_summary() -> None:
    """Display configuration summary."""
    print("\n" + "="*60)
    print("CONFIGURATION SUMMARY")
    print("="*60)
    
    try:
        summary = get_configuration_summary()
        
        # Display accounts
        accounts = summary.get("accounts", [])
        print(f"\nAccounts ({len(accounts)}):")
        for account in accounts:
            account_id = account.get("account_id", "?")
            name = account.get("name", "Unknown")
            has_client_id = account.get("has_client_id", False)
            has_client_secret = account.get("has_client_secret", False)
            has_refresh_token = account.get("has_refresh_token", False)
            
            print(f"  {account_id}. {name}")
            print(f"     Client ID: {'✅' if has_client_id else '❌'}")
            print(f"     Client Secret: {'✅' if has_client_secret else '❌'}")
            print(f"     Refresh Token: {'✅' if has_refresh_token else '❌'}")
        
        # Display sync flows
        flows = summary.get("sync_flows", [])
        print(f"\nSync Flows ({len(flows)}):")
        for flow in flows:
            flow_id = flow.get("flow_id", "?")
            name = flow.get("name", "Unknown")
            source_account = flow.get("source_account_id", "?")
            target_account = flow.get("target_account_id", "?")
            
            print(f"  {flow_id}. {name}")
            print(f"     Source: Account {source_account}")
            print(f"     Target: Account {target_account}")
        
        # Display polling settings
        polling = summary.get("polling_settings", {})
        print(f"\nPolling Settings:")
        print(f"  Daily sync hour: {polling.get('daily_sync_hour', 'Unknown')}")
        print(f"  Timezone: {polling.get('daily_sync_timezone', 'Unknown')}")
        
        # Display validation status
        validation = summary.get("validation_status", "unknown")
        print(f"\nValidation Status: {validation}")
        
    except Exception as e:
        print(f"❌ Failed to get configuration summary: {e}")
    
    print("="*60)


def main() -> None:
    """Main function to run calendar access tests."""
    parser = argparse.ArgumentParser(description="Test Google Calendar access for multiple accounts")
    parser.add_argument(
        "--account-id",
        type=int,
        help="Test specific account ID only"
    )
    parser.add_argument(
        "--list-flows",
        action="store_true",
        help="Test sync flow configurations"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display configuration summary only"
    )
    
    args = parser.parse_args()
    
    # Display configuration summary if requested
    if args.summary:
        display_configuration_summary()
        return
    
    # Load configuration
    try:
        logger.info("Loading multi-account configuration...")
        config = load_multi_account_config()
        logger.info(f"Configuration loaded: {len(config.accounts)} accounts, {len(config.sync_flows)} sync flows")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your environment variables and try again.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    
    # Test sync flows if requested
    if args.list_flows:
        check_sync_flows(config)
        return
    
    # Test specific account if requested
    if args.account_id:
        try:
            account_manager = AccountManager(config)
            result = check_single_account(account_manager, args.account_id)
            display_account_results([result])
        except AccountManagerError as e:
            logger.error(f"AccountManager error: {e}")
            print(f"\n❌ AccountManager Error: {e}")
            sys.exit(1)
        return
    
    # Test all accounts
    try:
        results = check_all_accounts(config)
        display_account_results(results)
        
        # Also test sync flows
        check_sync_flows(config)
        
        # Show summary
        display_configuration_summary()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 