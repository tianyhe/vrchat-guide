import psycopg2

# Test database connection
try:
    conn = psycopg2.connect(
        dbname="vrchat_events",
        user="vrchat_user",
        password="NEUcs7980",
        host="127.0.0.1",
        port="5432"  # or "5432" if using default
    )
    cur = conn.cursor()
    
    # Check if events table has data
    cur.execute("SELECT COUNT(*) FROM events;")
    count = cur.fetchone()[0]
    print(f"Total events in database: {count}")
    
    # Check sample of events
    cur.execute("SELECT _id, summary, start_time FROM events LIMIT 3;")
    samples = cur.fetchall()
    print("Sample events:", samples)
    
except Exception as e:
    print(f"Database connection error: {e}")