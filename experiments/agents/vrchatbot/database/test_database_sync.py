import asyncio
import os
from datetime import datetime, timezone, timedelta
import psycopg2
from loguru import logger

from sync_service import CalendarSyncService
from event_store import EventStore, EventData

async def test_calendar_sync():
    """Test calendar sync and verify database contents"""
    
    # Database connection parameters
    db_config = {
        "host": "localhost",
        "port": "5432",
        "dbname": "vrchat_events",  # Replace with your db name
        "user": "vrchat_user",  # Replace with your db user
        "password": "NEUcs7980"  # Replace with your db password
    }
    
    try:
        # Initialize sync service
        sync_service = CalendarSyncService(
            db_host=db_config["host"],
            db_port=db_config["port"],
            db_name=db_config["dbname"],
            db_user=db_config["user"],
            db_password=db_config["password"],
            credentials_file="credentials.json"
        )
        
        # Perform single sync
        logger.info("Starting calendar sync...")
        await sync_service.sync()
        
        # Verify database contents
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                # Count total events
                cur.execute("SELECT COUNT(*) FROM events")
                total_count = cur.fetchone()[0]
                logger.info(f"Total events in database: {total_count}")
                
                # Get sample of events
                cur.execute("""
                    SELECT _id, summary, start_time, end_time, location, description 
                    FROM events 
                    ORDER BY start_time 
                    LIMIT 5
                """)
                sample_events = cur.fetchall()
                
                # Display sample events
                logger.info("\nSample of upcoming events:")
                for event in sample_events:
                    logger.info("\nEvent Details:")
                    logger.info(f"ID: {event[0]}")
                    logger.info(f"Summary: {event[1]}")
                    logger.info(f"Start Time: {event[2]}")
                    logger.info(f"End Time: {event[3]}")
                    logger.info(f"Location: {event[4]}")
                    logger.info(f"Description: {event[5][:100]}...")  # First 100 chars of description
                
                # Verify date range
                cur.execute("""
                    SELECT MIN(start_time), MAX(start_time) 
                    FROM events
                """)
                date_range = cur.fetchone()
                logger.info(f"\nEvent date range: {date_range[0]} to {date_range[1]}")
                
        logger.success("Database verification complete!")
        
    except Exception as e:
        logger.error(f"Error during sync test: {e}")
        raise
    finally:
        await sync_service.stop()

if __name__ == "__main__":
    asyncio.run(test_calendar_sync())