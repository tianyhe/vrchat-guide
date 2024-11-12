import os
import sys
from datetime import datetime, timezone, timedelta
from loguru import logger
import psycopg2
from psycopg2.extras import RealDictCursor

current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(current_dir)

from database.api_client import GoogleCalendarClient
from database.event_store import EventStore
from database.sync_service import CalendarSyncService

class VRChatDatabaseManager:
    """Manages database operations and Google Calendar synchronization for VRChat events."""
    
    def __init__(
        self,
        db_host: str,
        db_port: str,
        db_name: str,
        db_user: str,
        db_password: str,
        credentials_file: str = "credentials.json"
    ):
        self.db_config = {
            "host": db_host,
            "port": db_port,
            "dbname": db_name,
            "user": db_user,
            "password": db_password
        }
        self.credentials_file = credentials_file
        self.event_store = None
        self.calendar_sync = None
        
    async def initialize(self):
        """Initialize database and event syncing."""
        try:
            # Test database connection
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                # Check if events table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'events'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    logger.info("Creating events table...")
                    # Create events table if it doesn't exist
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS events (
                            _id TEXT PRIMARY KEY,
                            summary TEXT NOT NULL,
                            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                            end_time TIMESTAMP WITH TIME ZONE NOT NULL,
                            location TEXT,
                            description TEXT,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        -- Create indices
                        CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_time);
                        CREATE INDEX IF NOT EXISTS idx_events_end ON events(end_time);
                        
                        -- Create text search indices
                        CREATE INDEX IF NOT EXISTS idx_events_summary_text ON events USING gin(to_tsvector('english', summary));
                        CREATE INDEX IF NOT EXISTS idx_events_description_text ON events USING gin(to_tsvector('english', description));
                    """)
            conn.commit()
            conn.close()
            
            # Initialize Google Calendar client
            try:
                logger.info("Initializing Google Calendar client...")
                calendar_client = GoogleCalendarClient(
                    credentials_file=self.credentials_file
                )
                credentials = calendar_client.get_credentials()
                
                # Initialize EventStore
                self.event_store = EventStore(
                    credentials=credentials,
                    calendar_id='vrchateventsdotcom@gmail.com'  # Your calendar ID
                )
                
                # Initialize sync service
                self.calendar_sync = CalendarSyncService(
                    db_host=self.db_config["host"],
                    db_port=self.db_config["port"],
                    db_name=self.db_config["dbname"],
                    db_user=self.db_config["user"],
                    db_password=self.db_config["password"],
                    credentials_file=self.credentials_file
                )
                
                # Start initial sync
                await self.sync_events()
                
            except Exception as e:
                logger.error(f"Error initializing Google Calendar services: {e}")
                raise
                
            logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
            
    async def sync_events(self):
        """Synchronize events from Google Calendar to database."""
        try:
            if self.event_store is None:
                raise ValueError("EventStore not initialized")
                
            # Force sync from Google Calendar
            self.event_store.sync_events(force=True)
            
            # Get all upcoming events
            events = self.event_store.get_upcoming_events(days=30)
            
            # Convert to database format
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    for event in events:
                        cur.execute("""
                            INSERT INTO events (_id, summary, start_time, end_time, location, description)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (_id) DO UPDATE SET
                                summary = EXCLUDED.summary,
                                start_time = EXCLUDED.start_time,
                                end_time = EXCLUDED.end_time,
                                location = EXCLUDED.location,
                                description = EXCLUDED.description,
                                updated_at = CURRENT_TIMESTAMP;
                        """, (
                            event.id,
                            event.summary,
                            event.start,
                            event.end,
                            event.location,
                            event.description
                        ))
                conn.commit()
                
            logger.info(f"Synchronized {len(events)} events")
            return True
            
        except Exception as e:
            logger.error(f"Event synchronization failed: {e}")
            return False
            
    async def check_database_status(self):
        """Check database and sync status."""
        try:
            status = {
                "database_connected": False,
                "events_count": 0,
                "last_sync": None,
                "calendar_connected": False
            }
            
            # Check database connection
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                status["database_connected"] = True
                
                # Count events
                cur.execute("SELECT COUNT(*) FROM events;")
                status["events_count"] = cur.fetchone()[0]
                
                # Get last update
                cur.execute("SELECT MAX(updated_at) FROM events;")
                status["last_sync"] = cur.fetchone()[0]
            
            # Check calendar connection
            if self.event_store:
                status["calendar_connected"] = True
                
            conn.close()
            return status
            
        except Exception as e:
            logger.error(f"Error checking database status: {e}")
            return None
            
    async def shutdown(self):
        """Cleanup and shutdown."""
        try:
            if self.calendar_sync:
                await self.calendar_sync.stop()
            logger.info("Database manager shut down successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")