import os
import json
from pathlib import Path
import asyncio
import signal
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import psycopg2
from psycopg2.extras import execute_batch


# Configure logging
logger.add(
    "vrchat_calendar_sync.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

# Path configuration
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "vrchat_events",
    "user": "creator_role",    
    "password": "creator_role"
}

@dataclass
class EventData:
    """Event data model matching database schema"""
    id: str
    summary: str
    start_time: datetime
    end_time: datetime
    location: str
    description: str

class GoogleCalendarClient:
    """Simplified Google Calendar API client"""
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
    ]

    def __init__(
        self, 
        credentials_file: str = "credentials.json", 
        token_file: str = "token.json"
    ):
        # Resolve paths relative to config directory
        self.credentials_path = CONFIG_DIR / credentials_file
        self.token_path = CONFIG_DIR / token_file
        
        # Ensure config directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Validate credentials file exists
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found at {self.credentials_path}. "
                "Please ensure you have placed your Google Calendar credentials file "
                "in the config directory."
            )
            
        self._credentials: Optional[Credentials] = None
    
#     def __init__(self, credentials_file: str, token_file: str = "../config/token.json"):
#         self.credentials_path = credentials_file
#         self.token_path = token_file
#         self._credentials: Optional[Credentials] = None
        
    # def get_credentials(self) -> Credentials:
    #     """Get or refresh Google Calendar credentials"""
    #     if self._credentials and self._credentials.valid:
    #         return self._credentials
            
    #     if os.path.exists(self.token_path):
    #         self._credentials = Credentials.from_authorized_user_file(
    #             self.token_path, self.SCOPES
    #         )
            
    #     if not self._credentials or not self._credentials.valid:
    #         if self._credentials and self._credentials.expired and self._credentials.refresh_token:
    #             self._credentials.refresh(Request())
    #         else:
    #             flow = InstalledAppFlow.from_client_secrets_file(
    #                 self.credentials_path, self.SCOPES
    #             )
    #             self._credentials = flow.run_local_server(port=0)
                
    #         with open(self.token_path, 'w') as token:
    #             token.write(self._credentials.to_json())
                
    #     return self._credentials
    
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

class VRChatCalendarSync:
    """Manages synchronization between Google Calendar and PostgreSQL"""
    def __init__(
        self,
        calendar_id: str = 'vrchateventsdotcom@gmail.com',
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
        sync_interval: int = 300  # 5 minutes
    ):
        self.calendar_id = calendar_id
        self.calendar_client = GoogleCalendarClient(credentials_file, token_file)
        self.service = build('calendar', 'v3', credentials=self.calendar_client.get_credentials())
        self.sync_interval = sync_interval
        self._stop_sync = False
        self._sync_task = None
        
    def _convert_event(self, event: Dict) -> EventData:
        """Convert Google Calendar event to EventData"""
        return EventData(
            id=event['iCalUID'],
            summary=event.get('summary', ''),
            start_time=datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))),
            end_time=datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))),
            location=event.get('location', ''),
            description=event.get('description', '')
        )
        
    async def fetch_events(self) -> List[EventData]:
        """Fetch events from Google Calendar"""
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=datetime.now(timezone.utc).isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return [
                self._convert_event(event)
                for event in events_result.get('items', [])
            ]
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []
            
    async def sync_to_database(self, events: List[EventData]):
        """Sync events to PostgreSQL database"""
        try:
            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    # Prepare event data for batch insert/update
                    event_data = [
                        (
                            event.id,
                            event.summary,
                            event.start_time,
                            event.end_time,
                            event.location,
                            event.description
                        )
                        for event in events
                    ]
                    
                    # Upsert events
                    execute_batch(cur, """
                        INSERT INTO events (_id, summary, start_time, end_time, location, description)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (_id) DO UPDATE SET
                            summary = EXCLUDED.summary,
                            start_time = EXCLUDED.start_time,
                            end_time = EXCLUDED.end_time,
                            location = EXCLUDED.location,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP
                    """, event_data)
                    
                    # Clean up old events
                    cur.execute("""
                        DELETE FROM events 
                        WHERE end_time < %s
                    """, (datetime.now(timezone.utc) - timedelta(days=7),))
                    
                conn.commit()
                logger.info(f"Successfully synced {len(events)} events")
                
        except Exception as e:
            logger.error(f"Database sync error: {e}")
            
    async def start(self):
        """Start the sync service"""
        self._stop_sync = False
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Calendar sync service started")
        
    async def stop(self):
        """Stop the sync service"""
        self._stop_sync = True
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Calendar sync service stopped")
        
    async def _sync_loop(self):
        """Main sync loop"""
        while not self._stop_sync:
            try:
                events = await self.fetch_events()
                await self.sync_to_database(events)
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(60)

async def main():
    # Initialize sync service
    sync_service = VRChatCalendarSync()
    
    # Setup shutdown handler
    async def shutdown(sig=None):
        if sig:
            logger.info(f"Received exit signal {sig.name}")
        await sync_service.stop()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        asyncio.get_event_loop().stop()
    
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))
    
    try:
        await sync_service.start()
        # Keep the service running
        while True:
            await asyncio.sleep(1)
    finally:
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted")
    finally:
        logger.info("Sync service shutdown complete")