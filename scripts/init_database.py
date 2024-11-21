import os
import psycopg2
from loguru import logger

DB_CONFIG = {
    "host": "host.docker.internal",
    "port": "5432",
    "dbname": "vrchat_events",
    "user": "creator_role",    
    "password": "creator_role"
}

def setup_database():
    """Create the events table and required indices"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Create the events table
            logger.info("Creating events table...")
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
                CREATE INDEX IF NOT EXISTS idx_events_summary_text ON events USING gin(to_tsvector('english', summary));
                CREATE INDEX IF NOT EXISTS idx_events_description_text ON events USING gin(to_tsvector('english', description));
                
                -- Grant permissions
                GRANT USAGE ON SCHEMA public TO select_user;
                GRANT SELECT ON ALL TABLES IN SCHEMA public TO select_user;
                GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO select_user;
                ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO select_user;
            """)
            
            logger.info("Successfully created events table and set permissions!")
            
            # Insert sample event
            logger.info("Inserting sample event...")
            cur.execute("""
                INSERT INTO events (_id, summary, start_time, end_time, location, description)
                VALUES (
                    'test_event_001',
                    'VRChat Meditation Session',
                    CURRENT_TIMESTAMP + interval '1 day',
                    CURRENT_TIMESTAMP + interval '1 day' + interval '1 hour',
                    'Zen Garden World',
                    'Join us for a guided meditation session in VRChat. 
                     Suitable for both VR and desktop users. 
                     The session will focus on mindfulness and relaxation techniques.'
                )
                ON CONFLICT (_id) DO NOTHING;
            """)
            
            # Verify setup
            cur.execute("SELECT COUNT(*) FROM events;")
            count = cur.fetchone()[0]
            logger.info(f"Current number of events in database: {count}")
            
        conn.close()
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_database()