import os
import psycopg2
from loguru import logger

# Database configuration matching our setup guide
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "vr_event_hub",
    "user": "select_user",    # Using the select_user we created
    "password": "select_user"  # Using the password we set
}

def test_database_connection():
    """Test PostgreSQL database connection"""
    try:
        # Attempt to connect
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Successfully connected to PostgreSQL database!")
        
        # Test basic query
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            logger.info(f"PostgreSQL version: {version}")
            
            # Test if events table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'events'
                );
            """)
            table_exists = cur.fetchone()[0]
            if table_exists:
                cur.execute("SELECT COUNT(*) FROM events;")
                count = cur.fetchone()
                logger.info(f"Number of events in database: {count[0]}")
            else:
                logger.warning("Events table does not exist yet")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()