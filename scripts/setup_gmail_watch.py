#!/usr/bin/env python3
"""
Script to setup Gmail push notifications for all configured accounts.
This script registers Gmail watch requests for each account to receive
notifications via Google Cloud Pub/Sub.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore

from backend.models.google_account import GoogleAccount
from backend.services.google_calendar.config_loader import load_google_accounts_from_env

# Load environment variables from .env file
load_dotenv()

def setup_gmail_watch_for_account(account: GoogleAccount, project_id: str, topic_name: str) -> None:
    """Setup Gmail push notifications for a single account."""
    print(f"Setting up Gmail watch for account: {account.email}")
    
    # Create OAuth2 credentials with Gmail scope
    credentials = Credentials(
        token=None,
        refresh_token=account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=account.client_id,
        client_secret=account.client_secret,
        scopes=["https://www.googleapis.com/auth/gmail.modify"]
    )
    
    # Build Gmail service
    service = build('gmail', 'v1', credentials=credentials)  # type: ignore
    
    # Setup watch request
    topic_name_full = f"projects/{project_id}/topics/{topic_name}"
    
    watch_request = {
        'labelIds': ['INBOX'],  # Only watch INBOX
        'topicName': topic_name_full
    }
    
    try:
        # Execute watch request
        result = service.users().watch(userId='me', body=watch_request).execute()  # type: ignore
        
        print(f"✅ Gmail watch setup successful for {account.email}")
        print(f"   Watch ID: {result.get('historyId')}")  # type: ignore
        print(f"   Expires: {result.get('expiration')}")  # type: ignore
        
    except Exception as e:
        print(f"❌ Failed to setup Gmail watch for {account.email}: {e}")
        raise

def main():
    """Main function to setup Gmail watch for all accounts."""
    print("🔧 Setting up Gmail push notifications...")
    
    # Force reload environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv(override=True)
    print("🔄 Reloaded environment variables from .env file")
    
    # Load Google accounts
    try:
        accounts = load_google_accounts_from_env()
        if not accounts:
            print("❌ No Google accounts found. Please run setup_google_oauth.py first.")
            return
            
        print(f"📧 Found {len(accounts)} Google accounts")
        
    except Exception as e:
        print(f"❌ Failed to load Google accounts: {e}")
        return
    
    # Get Google Cloud project ID
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT_ID not found in environment variables")
        print("   Please add it to your .env file")
        return
    
    topic_name = "gmail-notifications"
    
    print(f"🔧 Using Google Cloud Project: {project_id}")
    print(f"🔧 Using Pub/Sub Topic: {topic_name}")
    
    # Setup Gmail watch for each account
    for account in accounts:
        try:
            setup_gmail_watch_for_account(account, project_id, topic_name)
            print()
            
        except Exception as e:
            print(f"❌ Failed to setup Gmail watch for {account.email}: {e}")
            print("   Continuing with other accounts...")
            print()
            continue
    
    print("✅ Gmail push notifications setup completed!")
    print()
    print("📋 Next steps:")
    print("   1. Verify that Gmail notifications are working")
    print("   2. Test the webhook endpoint")
    print("   3. Deploy the Gmail service to production")

if __name__ == "__main__":
    main() 