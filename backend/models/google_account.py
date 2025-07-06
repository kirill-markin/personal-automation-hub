"""
GoogleAccount model for multi-service Google integrations.

This module defines the base GoogleAccount model used across all Google services
(Calendar, Gmail, etc.) to maintain consistency and avoid duplication.
"""

from pydantic import BaseModel, Field, model_validator


class GoogleAccount(BaseModel):
    """Configuration for a single Google account."""
    
    account_id: int = Field(..., description="Unique account identifier")
    email: str = Field(..., description="Google account email address")
    client_id: str = Field(..., description="Google OAuth2 client ID")
    client_secret: str = Field(..., description="Google OAuth2 client secret")
    refresh_token: str = Field(..., description="OAuth2 refresh token for this account")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'GoogleAccount':
        # Validate account_id
        if self.account_id <= 0:
            raise ValueError('account_id must be positive')
        
        # Validate email
        if not self.email.strip():
            raise ValueError('email cannot be empty')
        self.email = self.email.strip()
        
        # Validate client_id
        if not self.client_id.strip():
            raise ValueError('client_id cannot be empty')
        self.client_id = self.client_id.strip()
        
        # Validate client_secret
        if not self.client_secret.strip():
            raise ValueError('client_secret cannot be empty')
        self.client_secret = self.client_secret.strip()
        
        # Validate refresh_token
        if not self.refresh_token.strip():
            raise ValueError('refresh_token cannot be empty')
        self.refresh_token = self.refresh_token.strip()
        
        return self