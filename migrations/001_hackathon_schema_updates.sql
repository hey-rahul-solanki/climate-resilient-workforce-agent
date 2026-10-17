-- Hackathon Schema Migration
-- Run this to update the database for the hackathon solution
-- Version: 001
-- Date: 2024-01-15

BEGIN;

-- ============================================
-- NEW TABLES
-- ============================================

-- 1. Create weather_safety_rules table
CREATE TABLE IF NOT EXISTS weather_safety_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_type VARCHAR(50) NOT NULL,
    safe_threshold JSONB NOT NULL,
    caution_threshold JSONB NOT NULL,
    warning_threshold JSONB NOT NULL,
    severe_threshold JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_on TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- 2. Create schedule_change_requests table
CREATE TABLE IF NOT EXISTS schedule_change_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    assignment_id UUID NOT NULL,
    original_start_time TIMESTAMPTZ NOT NULL,
    original_end_time TIMESTAMPTZ NOT NULL,
    suggested_start_time TIMESTAMPTZ NOT NULL,
    suggested_end_time TIMESTAMPTZ NOT NULL,
    original_weather JSONB,
    suggested_weather JSONB,
    weather_status VARCHAR(20) NOT NULL,
    reason TEXT,
    urgency VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    supervisor_id UUID,
    supervisor_note TEXT,
    approved_at TIMESTAMPTZ,
    rejected_at TIMESTAMPTZ,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_on TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),

    CONSTRAINT fk_schedule_change_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_schedule_change_assignment FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE RESTRICT,
    CONSTRAINT fk_schedule_change_supervisor FOREIGN KEY (supervisor_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_schedule_change_times CHECK (suggested_end_time > suggested_start_time AND original_end_time > original_start_time),
    CONSTRAINT chk_schedule_change_status CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT chk_schedule_change_urgency CHECK (urgency IN ('low', 'medium', 'high')),
    CONSTRAINT chk_schedule_change_weather_status CHECK (weather_status IN ('SAFE', 'CAUTION', 'WARNING', 'SEVERE'))
);

-- 3. Create location_cache table
CREATE TABLE IF NOT EXISTS location_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query VARCHAR(500) NOT NULL UNIQUE,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    display_name TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    last_accessed TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_on TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),

    CONSTRAINT chk_location_cache_latitude CHECK (latitude BETWEEN -90.0 AND 90.0),
    CONSTRAINT chk_location_cache_longitude CHECK (longitude BETWEEN -180.0 AND 180.0)
);

-- ============================================
-- UPDATE EXISTING TABLES
-- ============================================

-- 4. Update assignments table
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS weather_safe BOOLEAN,
ADD COLUMN IF NOT EXISTS weather_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS weather_assessment JSONB;

-- Add check constraint for assignments.weather_status
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_assignments_weather_status'
    ) THEN
        ALTER TABLE assignments
        ADD CONSTRAINT chk_assignments_weather_status
        CHECK (weather_status IS NULL OR weather_status IN ('SAFE', 'CAUTION', 'WARNING', 'SEVERE'));
    END IF;
END $$;

-- 5. Update requests table
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS weather_context JSONB,
ADD COLUMN IF NOT EXISTS original_assignment_time TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS suggested_assignment_time TIMESTAMPTZ;

-- 6. Update sites table
ALTER TABLE sites
ADD COLUMN IF NOT EXISTS osm_display_name TEXT;

-- ============================================
-- CREATE INDEXES
-- ============================================

-- Indexes for weather_safety_rules
CREATE INDEX IF NOT EXISTS idx_weather_safety_rules_type ON weather_safety_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_weather_safety_rules_active ON weather_safety_rules(active);

-- Indexes for schedule_change_requests
CREATE INDEX IF NOT EXISTS idx_schedule_change_user ON schedule_change_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_schedule_change_assignment ON schedule_change_requests(assignment_id);
CREATE INDEX IF NOT EXISTS idx_schedule_change_status ON schedule_change_requests(status);
CREATE INDEX IF NOT EXISTS idx_schedule_change_supervisor ON schedule_change_requests(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_schedule_change_created ON schedule_change_requests(created_on);
CREATE INDEX IF NOT EXISTS idx_schedule_change_active ON schedule_change_requests(active);

-- Indexes for location_cache
CREATE INDEX IF NOT EXISTS idx_location_cache_query ON location_cache(query);
CREATE INDEX IF NOT EXISTS idx_location_cache_coords ON location_cache(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_location_cache_last_accessed ON location_cache(last_accessed);
CREATE INDEX IF NOT EXISTS idx_location_cache_active ON location_cache(active);

-- Indexes for assignments
CREATE INDEX IF NOT EXISTS idx_assignments_weather_safe ON assignments(weather_safe);
CREATE INDEX IF NOT EXISTS idx_assignments_weather_status ON assignments(weather_status);

-- Index for requests
CREATE INDEX IF NOT EXISTS idx_requests_weather ON requests(request_type) WHERE request_type = 'weather_change';

-- Index for sites
CREATE INDEX IF NOT EXISTS idx_sites_osm_display_name ON sites(osm_display_name);

-- ============================================
-- INSERT DEFAULT DATA
-- ============================================

-- Insert default weather safety rules
INSERT INTO weather_safety_rules (rule_type, safe_threshold, caution_threshold, warning_threshold, severe_threshold)
VALUES
('heat', '{"max_temp_c": 32}', '{"max_temp_c": 35}', '{"max_temp_c": 40}', '{"max_temp_c": 999}'),
('rain', '{"max_precipitation_percent": 20}', '{"max_precipitation_percent": 40}', '{"max_precipitation_percent": 60}', '{"max_precipitation_percent": 999}'),
('wind', '{"max_wind_speed_kmh": 20}', '{"max_wind_speed_kmh": 30}', '{"max_wind_speed_kmh": 50}', '{"max_wind_speed_kmh": 999}'),
('visibility', '{"min_visibility_km": 5}', '{"min_visibility_km": 2}', '{"min_visibility_km": 1}', '{"min_visibility_km": 0}')
ON CONFLICT DO NOTHING;

COMMIT;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Uncomment to verify migration

-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('weather_safety_rules', 'schedule_change_requests', 'location_cache');
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'assignments' AND column_name IN ('weather_safe', 'weather_status', 'weather_assessment');
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'requests' AND column_name IN ('weather_context', 'original_assignment_time', 'suggested_assignment_time');
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'sites' AND column_name = 'osm_display_name';
