-- Initialize events table
CREATE TABLE events (
    _id TEXT PRIMARY KEY,                    -- Maps to iCalUID (required by both SUQL and Google Calendar)
    summary TEXT NOT NULL,                   -- Event title/name
    start_time TIMESTAMP WITH TIME ZONE NOT NULL, -- Event start time
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,   -- Event end time
    location TEXT,                          -- Event location (VRChat world)
    description TEXT,                       -- Event description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for efficient querying
CREATE INDEX idx_events_start ON events(start_time);
CREATE INDEX idx_events_end ON events(end_time);

-- Create text search indices for SUQL queries
CREATE INDEX idx_events_summary_text ON events USING gin(to_tsvector('english', summary));
CREATE INDEX idx_events_description_text ON events USING gin(to_tsvector('english', description));
CREATE INDEX idx_events_location_text ON events USING gin(to_tsvector('english', location));

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_events_timestamp
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
-- GRANT SELECT, INSERT, UPDATE, DELETE ON events TO vrchat_user;
GRANT SELECT events TO vrchat_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vrchat_user;