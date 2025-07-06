#!/usr/bin/env python3
"""
Google OAuth2 setup script for multiple accounts.

This script helps obtain Google OAuth2 refresh tokens for multiple Google accounts
used in the calendar synchronization feature.

Usage:
    python scripts/setup_google_oauth.py --account-id 1
    python scripts/setup_google_oauth.py --account-id 2
    python scripts/setup_google_oauth.py --account-id 3

Each account will have its own refresh token that should be stored in environment variables:
    GOOGLE_ACCOUNT_1_REFRESH_TOKEN
    GOOGLE_ACCOUNT_2_REFRESH_TOKEN
    GOOGLE_ACCOUNT_3_REFRESH_TOKEN
"""

import os
import sys
import argparse
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from typing import Optional

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]


def get_client_credentials(account_id: int) -> tuple[str, str]:
    """Get client ID and secret for the specified account.
    
    Args:
        account_id: Account ID (1, 2, 3, etc.)
        
    Returns:
        Tuple of (client_id, client_secret)
        
    Raises:
        ValueError: If credentials are not found
    """
    # Try account-specific credentials first
    client_id_key = f"GOOGLE_ACCOUNT_{account_id}_CLIENT_ID"
    client_secret_key = f"GOOGLE_ACCOUNT_{account_id}_CLIENT_SECRET"
    
    client_id = os.environ.get(client_id_key)
    client_secret = os.environ.get(client_secret_key)
    
    # If account-specific credentials not found, try shared credentials
    if not client_id or not client_secret:
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError(
            f"Google OAuth2 credentials not found. Please set either:\n"
            f"- {client_id_key} and {client_secret_key}\n"
            f"- Or GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET (shared credentials)"
        )
    
    return client_id.strip(), client_secret.strip()


def setup_oauth2_for_account(account_id: int) -> str:
    """Set up OAuth2 and obtain refresh token for the specified account.
    
    Args:
        account_id: Account ID (1, 2, 3, etc.)
        
    Returns:
        Refresh token string
        
    Raises:
        Exception: If OAuth2 flow fails
    """
    logger.info(f"Setting up OAuth2 for account {account_id}")
    
    # Get credentials
    client_id, client_secret = get_client_credentials(account_id)
    
    # Create client config
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    # Create OAuth2 flow
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)  # type: ignore
    
    # Run the OAuth2 flow
    logger.info("Opening browser for OAuth2 authorization...")
    logger.info("Please log in to the Google account you want to authorize for calendar access.")
    
    try:
        # Use a different port for each account to avoid conflicts
        port = 8080 + account_id
        credentials = flow.run_local_server(port=port, open_browser=True)  # type: ignore
        
        if not credentials.refresh_token:  # type: ignore
            raise Exception(
                "No refresh token received. This might happen if you've already authorized this app. "
                "Try revoking the app's access in your Google account settings and run this script again."
            )
        
        logger.info(f"OAuth2 setup successful for account {account_id}")
        return credentials.refresh_token  # type: ignore
        
    except Exception as e:
        logger.error(f"OAuth2 setup failed for account {account_id}: {e}")
        raise


def save_refresh_token(account_id: int, refresh_token: str) -> None:
    """Save refresh token to environment variable instruction.
    
    Args:
        account_id: Account ID
        refresh_token: Refresh token to save
    """
    env_var_name = f"GOOGLE_ACCOUNT_{account_id}_REFRESH_TOKEN"
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS! OAuth2 setup complete for account {account_id}")
    print(f"{'='*60}")
    print(f"\nAdd this to your .env file:")
    print(f"\n{env_var_name}={refresh_token}")
    print(f"\nOr export it as an environment variable:")
    print(f"export {env_var_name}='{refresh_token}'")
    print(f"\n{'='*60}")


def get_account_name(account_id: int) -> Optional[str]:
    """Get account name from environment if available.
    
    Args:
        account_id: Account ID
        
    Returns:
        Account name or None if not set
    """
    return os.environ.get(f"GOOGLE_ACCOUNT_{account_id}_NAME")


def main() -> None:
    """Main function to run OAuth2 setup."""
    parser = argparse.ArgumentParser(description="Setup Google OAuth2 for calendar sync")
    parser.add_argument(
        "--account-id",
        type=int,
        required=True,
        help="Account ID (1, 2, 3, etc.) - determines which account to set up"
    )
    parser.add_argument(
        "--list-accounts",
        action="store_true",
        help="List configured accounts from environment variables"
    )
    
    args = parser.parse_args()
    
    if args.list_accounts:
        list_configured_accounts()
        return
    
    account_id = args.account_id
    
    if account_id <= 0:
        logger.error("Account ID must be a positive integer (1, 2, 3, etc.)")
        sys.exit(1)
    
    # Show account information
    account_name = get_account_name(account_id)
    if account_name:
        logger.info(f"Setting up OAuth2 for account {account_id}: {account_name}")
    else:
        logger.info(f"Setting up OAuth2 for account {account_id}")
        logger.info(f"Consider setting GOOGLE_ACCOUNT_{account_id}_NAME for better identification")
    
    try:
        # Set up OAuth2 and get refresh token
        refresh_token = setup_oauth2_for_account(account_id)
        
        # Save refresh token
        save_refresh_token(account_id, refresh_token)
        
        # Verify credentials work
        logger.info("Verifying credentials...")
        if verify_refresh_token(account_id, refresh_token):
            logger.info("✅ Credentials verified successfully!")
        else:
            logger.warning("⚠️  Credentials verification failed, but token was saved")
        
    except Exception as e:
        logger.error(f"OAuth2 setup failed: {e}")
        sys.exit(1)


def list_configured_accounts() -> None:
    """List all configured accounts from environment variables."""
    print("\n" + "="*50)
    print("CONFIGURED ACCOUNTS")
    print("="*50)
    
    found_accounts = False
    account_id = 1
    
    while True:
        name_key = f"GOOGLE_ACCOUNT_{account_id}_NAME"
        client_id_key = f"GOOGLE_ACCOUNT_{account_id}_CLIENT_ID"
        client_secret_key = f"GOOGLE_ACCOUNT_{account_id}_CLIENT_SECRET"
        refresh_token_key = f"GOOGLE_ACCOUNT_{account_id}_REFRESH_TOKEN"
        
        # Check if account exists
        if name_key not in os.environ:
            break
        
        found_accounts = True
        name = os.environ.get(name_key, "")
        has_client_id = bool(os.environ.get(client_id_key, ""))
        has_client_secret = bool(os.environ.get(client_secret_key, ""))
        has_refresh_token = bool(os.environ.get(refresh_token_key, ""))
        
        print(f"\nAccount {account_id}:")
        print(f"  Name: {name}")
        print(f"  Client ID: {'✅' if has_client_id else '❌'}")
        print(f"  Client Secret: {'✅' if has_client_secret else '❌'}")
        print(f"  Refresh Token: {'✅' if has_refresh_token else '❌'}")
        
        if not has_refresh_token:
            print(f"  → Run: python scripts/setup_google_oauth.py --account-id {account_id}")
        
        account_id += 1
    
    if not found_accounts:
        print("\nNo accounts configured yet.")
        print("Set up your first account with:")
        print("  python scripts/setup_google_oauth.py --account-id 1")
    
    print("\n" + "="*50)


def verify_refresh_token(account_id: int, refresh_token: str) -> bool:
    """Verify that the refresh token works.
    
    Args:
        account_id: Account ID
        refresh_token: Refresh token to verify
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        client_id, client_secret = get_client_credentials(account_id)
        
        # Create credentials object
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Try to refresh the token
        credentials.refresh(Request())  # type: ignore
        
        return credentials.valid
        
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return False


if __name__ == "__main__":
    main() 