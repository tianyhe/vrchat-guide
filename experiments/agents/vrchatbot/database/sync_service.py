import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import psycopg2
from psycopg2.extras import execute_batch
from loguru import logger

from database.api_client import GoogleCalendarClient
from database.event_store import EventStore, EventData

class CalendarSyncService:
    def __init__(
        self,
        db_host: str,
        db_port: str,
        db_name: str,
        db_user: str,
        db_password: str,
        credentials_file: str = "credentials.json",
        sync_interval: int = 300  # 5 minutes
    ):
        # Database connection
        self.db_config = {
            "host": db_host,
            "port": db_port,
            "dbname": db_name,
            "user": db_user,
            "password": db_password
        }
        
        # Calendar setup
        self.calendar_client = GoogleCalendarClient(credentials_file=credentials_file)
        self.event_store = EventStore(
            credentials=self.calendar_client.get_credentials(),
            calendar_id='vrchateventsdotcom@gmail.com'
        )
        
        self.sync_interval = sync_interval
        self.last_sync = None
        self._stop_sync = False
        self._sync_task = None

    async def start(self):
        """Start the periodic sync service"""
        self._stop_sync = False
        self._sync_task = asyncio.create_task(self._periodic_sync())
        logger.info("Calendar sync service started")

    async def stop(self):
        """Stop the periodic sync service"""
        self._stop_sync = True
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Calendar sync service stopped")

    async def _periodic_sync(self):
        """Run periodic sync based on sync_interval"""
        while not self._stop_sync:
            try:
                await self.sync()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def sync(self):
        """Synchronize Google Calendar events with PostgreSQL database"""
        try:
            # Fetch events from Google Calendar
            self.event_store.sync_events(force=True)
            calendar_events = self.event_store.get_upcoming_events(days=30)
            
            # Get connection to PostgreSQL
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Prepare data for batch insert/update
                    event_data = [
                        (
                            event.id,
                            event.summary,
                            event.start,
                            event.end,
                            event.location or '',
                            event.description or ''
                        )
                        for event in calendar_events
                    ]
                    
                    # Upsert events using ON CONFLICT
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
            
            self.last_sync = datetime.now(timezone.utc)
            logger.info(f"Successfully synced {len(calendar_events)} events")
            
        except Exception as e:
            logger.error(f"Error syncing events: {e}")
            raise

    async def force_sync(self):
        """Force an immediate sync"""
        await self.sync()

    def get_sync_status(self) -> dict:
        """Get current sync status"""
        return {
            "last_sync": self.last_sync,
            "sync_interval": self.sync_interval,
            "is_running": not self._stop_sync if self._sync_task else False
        }