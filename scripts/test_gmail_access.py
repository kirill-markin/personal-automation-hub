#!/usr/bin/env python3
"""
Simple test script to check Gmail API access with current tokens.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore

# Force reload environment variables from .env file with override
print("🔄 Force reloading environment variables from .env file...")
load_dotenv(override=True)
print(f"📋 Loaded GOOGLE_CLOUD_PROJECT_ID: {os.getenv('GOOGLE_CLOUD_PROJECT_ID')}")

def test_gmail_access() -> bool:
    """Test Gmail API access for the first account."""
    print("🧪 Testing Gmail API access...")
    
    # Get first account credentials
    account_id = 1
    email = os.getenv(f"GOOGLE_ACCOUNT_{account_id}_EMAIL")
    client_id = os.getenv(f"GOOGLE_ACCOUNT_{account_id}_CLIENT_ID")
    client_secret = os.getenv(f"GOOGLE_ACCOUNT_{account_id}_CLIENT_SECRET")
    refresh_token = os.getenv(f"GOOGLE_ACCOUNT_{account_id}_REFRESH_TOKEN")
    
    # Check if all required environment variables are present
    if not all([email, client_id, client_secret, refresh_token]):
        print("❌ Missing required environment variables")
        return False
    
    print(f"📧 Testing account: {email}")
    print(f"🔑 Client ID: {client_id[:20]}...")  # type: ignore
    print(f"🔄 Refresh Token: {refresh_token[:20]}...")  # type: ignore
    
    # Create OAuth2 credentials (scopes already encoded in refresh_token)
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    
    try:
        # Test Gmail API
        print("🔧 Building Gmail service...")
        service = build('gmail', 'v1', credentials=credentials)  # type: ignore
        
        print("📋 Testing Gmail profile access...")
        profile = service.users().getProfile(userId='me').execute()  # type: ignore
        print(f"✅ Gmail profile accessed successfully!")
        print(f"   Email: {profile.get('emailAddress')}")  # type: ignore
        print(f"   Messages Total: {profile.get('messagesTotal')}")  # type: ignore
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail API access failed: {e}")
        return False

if __name__ == "__main__":
    test_gmail_access() 