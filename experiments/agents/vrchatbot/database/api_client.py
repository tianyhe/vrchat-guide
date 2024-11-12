import os
import json
from typing import Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from loguru import logger
from pathlib import Path

class GoogleCalendarClient:
    """Client for handling Google Calendar authentication and credentials"""
    
    # Update scopes to include event modification permissions
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
    ]
    
    def __init__(
        self,
        credentials_file: str,
        token_file: str = "token.json",
        token_dir: Optional[str] = None
    ):
        self.credentials_path = credentials_file
        self.token_dir = token_dir or os.path.dirname(os.path.abspath(__file__))
        self.token_path = os.path.join(self.token_dir, token_file)
        self._credentials: Optional[Credentials] = None
        
    def get_credentials(self) -> Credentials:
        """Get valid credentials with proper scopes"""
        if self._credentials and self._credentials.valid:
            return self._credentials
            
        if os.path.exists(self.token_path):
            try:
                self._credentials = Credentials.from_authorized_user_file(
                    self.token_path, self.SCOPES
                )
            except Exception as e:
                logger.warning(f"Error loading saved credentials: {e}")
                self._credentials = None
        
        # Handle expired credentials
        if self._credentials and not self._credentials.valid:
            if self._credentials.expired and self._credentials.refresh_token:
                try:
                    self._credentials.refresh(Request())
                    self._save_credentials()
                    return self._credentials
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    self._credentials = None
        
        # Get new credentials if needed
        if not self._credentials:
            self._credentials = self._get_new_credentials()
            self._save_credentials()
        
        return self._credentials
    
    def _get_new_credentials(self) -> Credentials:
        """Get new credentials via OAuth2 flow."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.SCOPES
            )
            # This will open a browser window for authentication
            credentials = flow.run_local_server(port=0)
            return credentials
        except Exception as e:
            logger.error(f"Error getting new credentials: {e}")
            raise
    
    def _save_credentials(self):
        """Save credentials to token file."""
        if not self._credentials:
            return
            
        try:
            # Create token directory if it doesn't exist
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            
            # Save credentials
            token_data = {
                'token': self._credentials.token,
                'refresh_token': self._credentials.refresh_token,
                'token_uri': self._credentials.token_uri,
                'client_id': self._credentials.client_id,
                'client_secret': self._credentials.client_secret,
                'scopes': self._credentials.scopes
            }
            
            with open(self.token_path, 'w') as token_file:
                json.dump(token_data, token_file)
                
            logger.info(f"Saved credentials to {self.token_path}")
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            raise
    
    def revoke_credentials(self):
        """Revoke and delete stored credentials."""
        if self._credentials:
            try:
                # Revoke credentials with Google
                if self._credentials.valid:
                    Request().post(
                        'https://oauth2.googleapis.com/revoke',
                        params={'token': self._credentials.token},
                        headers={'content-type': 'application/x-www-form-urlencoded'}
                    )
            except Exception as e:
                logger.warning(f"Error revoking credentials: {e}")
        
        # Delete token file
        if os.path.exists(self.token_path):
            try:
                os.remove(self.token_path)
                logger.info(f"Deleted token file: {self.token_path}")
            except Exception as e:
                logger.error(f"Error deleting token file: {e}")

    def check_credentials_validity(self) -> bool:
        """Check if current credentials are valid."""
        try:
            credentials = self.get_credentials()
            return credentials and credentials.valid
        except Exception:
            return False