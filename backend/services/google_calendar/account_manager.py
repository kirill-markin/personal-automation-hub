"""
Account Manager for handling multiple Google Calendar accounts.

This module provides:
- AccountManager: Manages multiple Google accounts and their credentials
- Account-based client creation and management
- Account validation and testing
"""

import logging
from typing import Dict, List, Optional, Any
from backend.models.calendar import GoogleAccount, MultiAccountConfig
from backend.services.google_calendar.client import GoogleCalendarClient, GoogleCalendarError

logger = logging.getLogger(__name__)


class AccountManagerError(Exception):
    """Exception raised when account management operations fail."""
    pass


class AccountManager:
    """Manages multiple Google Calendar accounts and their clients."""
    
    def __init__(self, config: MultiAccountConfig) -> None:
        """Initialize AccountManager with configuration.
        
        Args:
            config: Multi-account configuration containing all accounts and sync flows
        """
        self.config = config
        self._clients: Dict[int, GoogleCalendarClient] = {}
        
        # Validate all accounts on initialization
        self._validate_accounts()
    
    def _validate_accounts(self) -> None:
        """Validate that all accounts have unique IDs and required credentials."""
        account_ids: set[int] = set()
        
        for account in self.config.accounts:
            if account.account_id in account_ids:
                raise AccountManagerError(f"Duplicate account ID: {account.account_id}")
            account_ids.add(account.account_id)
            
            # Validate account has all required fields
            if not account.client_id.strip():
                raise AccountManagerError(f"Account {account.account_id} missing client_id")
            if not account.client_secret.strip():
                raise AccountManagerError(f"Account {account.account_id} missing client_secret")
            if not account.refresh_token.strip():
                raise AccountManagerError(f"Account {account.account_id} missing refresh_token")
        
        logger.info(f"Validated {len(self.config.accounts)} accounts")
    
    def get_client(self, account_id: int) -> GoogleCalendarClient:
        """Get or create a Google Calendar client for the specified account.
        
        Args:
            account_id: Account ID to get client for
            
        Returns:
            GoogleCalendarClient instance for the account
            
        Raises:
            AccountManagerError: If account not found or client creation fails
        """
        # Check if client already exists
        if account_id in self._clients:
            return self._clients[account_id]
        
        # Find the account
        account = self.config.get_account_by_id(account_id)
        if account is None:
            raise AccountManagerError(f"Account {account_id} not found")
        
        # Create new client
        try:
            client = GoogleCalendarClient(
                client_id=account.client_id,
                client_secret=account.client_secret,
                refresh_token=account.refresh_token
            )
            
            # Test the client connection
            if not client.test_connection():
                raise AccountManagerError(f"Failed to connect to Google Calendar for account {account_id}")
            
            # Cache the client
            self._clients[account_id] = client
            logger.info(f"Created and cached client for account {account_id} ({account.name})")
            
            return client
            
        except GoogleCalendarError as e:
            raise AccountManagerError(f"Failed to create client for account {account_id}: {e}")
        except Exception as e:
            raise AccountManagerError(f"Unexpected error creating client for account {account_id}: {e}")
    
    def get_account(self, account_id: int) -> Optional[GoogleAccount]:
        """Get account configuration by ID.
        
        Args:
            account_id: Account ID to retrieve
            
        Returns:
            GoogleAccount instance or None if not found
        """
        return self.config.get_account_by_id(account_id)
    
    def list_accounts(self) -> List[GoogleAccount]:
        """Get list of all configured accounts.
        
        Returns:
            List of all GoogleAccount instances
        """
        return self.config.accounts.copy()
    
    def test_account_connection(self, account_id: int) -> bool:
        """Test if an account can connect to Google Calendar API.
        
        Args:
            account_id: Account ID to test
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            client = self.get_client(account_id)
            return client.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed for account {account_id}: {e}")
            return False
    
    def test_all_accounts(self) -> Dict[int, bool]:
        """Test connection for all accounts.
        
        Returns:
            Dictionary mapping account_id to connection test result
        """
        results: Dict[int, bool] = {}
        
        for account in self.config.accounts:
            results[account.account_id] = self.test_account_connection(account.account_id)
        
        return results
    
    def list_calendars_for_account(self, account_id: int) -> List[Dict[str, Any]]:
        """List all calendars accessible by the specified account.
        
        Args:
            account_id: Account ID to list calendars for
            
        Returns:
            List of calendar dictionaries
            
        Raises:
            AccountManagerError: If account not found or API call fails
        """
        try:
            client = self.get_client(account_id)
            calendars = client.list_calendars()
            
            # Add account info to each calendar
            account = self.get_account(account_id)
            account_name = account.name if account else 'Unknown'
            
            for calendar in calendars:
                calendar['account_id'] = account_id
                calendar['account_name'] = account_name
            
            return calendars
            
        except GoogleCalendarError as e:
            raise AccountManagerError(f"Failed to list calendars for account {account_id}: {e}")
        except Exception as e:
            raise AccountManagerError(f"Unexpected error listing calendars for account {account_id}: {e}")
    
    def list_all_calendars(self) -> Dict[int, List[Dict[str, Any]]]:
        """List calendars for all accounts.
        
        Returns:
            Dictionary mapping account_id to list of calendars
        """
        all_calendars: Dict[int, List[Dict[str, Any]]] = {}
        
        for account in self.config.accounts:
            try:
                calendars = self.list_calendars_for_account(account.account_id)
                all_calendars[account.account_id] = calendars
                logger.info(f"Listed {len(calendars)} calendars for account {account.account_id} ({account.name})")
            except Exception as e:
                logger.error(f"Failed to list calendars for account {account.account_id}: {e}")
                all_calendars[account.account_id] = []
        
        return all_calendars
    
    def get_account_summary(self) -> List[Dict[str, Any]]:
        """Get summary information for all accounts.
        
        Returns:
            List of account summaries with connection status and calendar count
        """
        summaries: List[Dict[str, Any]] = []
        
        for account in self.config.accounts:
            try:
                # Test connection
                connection_ok = self.test_account_connection(account.account_id)
                
                # Count calendars if connection is OK
                calendar_count = 0
                if connection_ok:
                    try:
                        calendars = self.list_calendars_for_account(account.account_id)
                        calendar_count = len(calendars)
                    except Exception:
                        calendar_count = 0
                
                summary = {
                    'account_id': account.account_id,
                    'name': account.name,
                    'connection_ok': connection_ok,
                    'calendar_count': calendar_count,
                    'client_cached': account.account_id in self._clients
                }
                
                summaries.append(summary)
                
            except Exception as e:
                logger.error(f"Error creating summary for account {account.account_id}: {e}")
                summaries.append({
                    'account_id': account.account_id,
                    'name': account.name,
                    'connection_ok': False,
                    'calendar_count': 0,
                    'client_cached': False,
                    'error': str(e)
                })
        
        return summaries
    
    def clear_client_cache(self, account_id: Optional[int] = None) -> None:
        """Clear cached clients.
        
        Args:
            account_id: Specific account to clear cache for, or None to clear all
        """
        if account_id is not None:
            if account_id in self._clients:
                del self._clients[account_id]
                logger.info(f"Cleared cached client for account {account_id}")
        else:
            self._clients.clear()
            logger.info("Cleared all cached clients")
    
    def reload_config(self, new_config: MultiAccountConfig) -> None:
        """Reload configuration with new accounts/flows.
        
        Args:
            new_config: New multi-account configuration
        """
        # Clear existing clients since accounts may have changed
        self.clear_client_cache()
        
        # Update config
        self.config = new_config
        
        # Validate new accounts
        self._validate_accounts()
        
        logger.info(f"Reloaded configuration with {len(self.config.accounts)} accounts and {len(self.config.sync_flows)} sync flows") 