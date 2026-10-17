# Database Schema Updates for Hackathon

## Overview

This document describes the database schema changes needed for the simplified hackathon solution.

---

## New Tables

### 1. `weather_safety_rules`

Stores configurable safety thresholds for weather conditions.

```sql
CREATE TABLE weather_safety_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_type VARCHAR(50) NOT NULL, -- heat, rain, wind, visibility
    safe_threshold JSONB NOT NULL,
    caution_threshold JSONB NOT NULL,
    warning_threshold JSONB NOT NULL,
    severe_threshold JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_on TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- Example data
INSERT INTO weather_safety_rules (rule_type, safe_threshold, caution_threshold, warning_threshold, severe_threshold) VALUES
('heat', '{"max_temp_c": 32}', '{"max_temp_c": 35}', '{"max_temp_c": 40}', '{"max_temp_c": 999}'),
('rain', '{"max_precipitation_percent": 20}', '{"max_precipitation_percent": 40}', '{"max_precipitation_percent": 60}', '{"max_precipitation_percent": 999}'),
('wind', '{"max_wind_speed_kmh": 20}', '{"max_wind_speed_kmh": 30}', '{"max_wind_speed_kmh": 50}', '{"max_wind_speed_kmh": 999}'),
('visibility', '{"min_visibility_km": 5}', '{"min_visibility_km": 2}', '{"min_visibility_km": 1}', '{"min_visibility_km": 0}');

-- Indexes
CREATE INDEX idx_weather_safety_rules_type ON weather_safety_rules(rule_type);
CREATE INDEX idx_weather_safety_rules_active ON weather_safety_rules(active);
```

### 2. `schedule_change_requests`

Stores employee requests for schedule changes due to weather.

```sql
CREATE TABLE schedule_change_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    assignment_id UUID NOT NULL,
    original_start_time TIMESTAMPTZ NOT NULL,
    original_end_time TIMESTAMPTZ NOT NULL,
    suggested_start_time TIMESTAMPTZ NOT NULL,
    suggested_end_time TIMESTAMPTZ NOT NULL,
    original_weather JSONB,
    suggested_weather JSONB,
    weather_status VARCHAR(20) NOT NULL, -- SAFE, CAUTION, WARNING, SEVERE
    reason TEXT,
    urgency VARCHAR(20) NOT NULL DEFAULT 'medium', -- low, medium, high
    status VARCHAR(30) NOT NULL DEFAULT 'pending', -- pending, approved, rejected
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

-- Indexes
CREATE INDEX idx_schedule_change_user ON schedule_change_requests(user_id);
CREATE INDEX idx_schedule_change_assignment ON schedule_change_requests(assignment_id);
CREATE INDEX idx_schedule_change_status ON schedule_change_requests(status);
CREATE INDEX idx_schedule_change_supervisor ON schedule_change_requests(supervisor_id);
CREATE INDEX idx_schedule_change_created ON schedule_change_requests(created_on);
CREATE INDEX idx_schedule_change_active ON schedule_change_requests(active);
```

### 3. `location_cache`

Caches OpenStreetMap geocoding results to avoid repeated API calls.

```sql
CREATE TABLE location_cache (
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

-- Indexes
CREATE INDEX idx_location_cache_query ON location_cache(query);
CREATE INDEX idx_location_cache_coords ON location_cache(latitude, longitude);
CREATE INDEX idx_location_cache_last_accessed ON location_cache(last_accessed);
CREATE INDEX idx_location_cache_active ON location_cache(active);
```

---

## Existing Table Updates

### 1. `assignments` table

Add AI weather assessment columns:

```sql
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS weather_safe BOOLEAN,
ADD COLUMN IF NOT EXISTS weather_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS weather_assessment JSONB;

-- Add constraints
ALTER TABLE assignments
ADD CONSTRAINT chk_assignments_weather_status
CHECK (weather_status IS NULL OR weather_status IN ('SAFE', 'CAUTION', 'WARNING', 'SEVERE'));

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_assignments_weather_safe ON assignments(weather_safe);
CREATE INDEX IF NOT EXISTS idx_assignments_weather_status ON assignments(weather_status);
```

### 2. `requests` table

Add support for weather-related requests:

```sql
-- Add weather-related request type
-- Update the request_type check constraint if needed
-- Current constraint may already allow custom types via 'other'

-- Add weather context column
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS weather_context JSONB,
ADD COLUMN IF NOT EXISTS original_assignment_time TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS suggested_assignment_time TIMESTAMPTZ;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_requests_weather ON requests(request_type) WHERE request_type = 'weather_change';
```

### 3. `sites` table

Add OpenStreetMap coordinates if not present:

```sql
-- Ensure latitude and longitude columns exist (they should already exist per original schema)
-- Add display_name from OSM if helpful
ALTER TABLE sites
ADD COLUMN IF NOT EXISTS osm_display_name TEXT;

-- Add index for OSM display name search
CREATE INDEX IF NOT EXISTS idx_sites_osm_display_name ON sites(osm_display_name);
```

---

## Migration Script

```sql
-- Hackathon Schema Migration
-- Run this to update the database for the hackathon solution

BEGIN;

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

-- Insert default safety rules
INSERT INTO weather_safety_rules (rule_type, safe_threshold, caution_threshold, warning_threshold, severe_threshold)
VALUES
('heat', '{"max_temp_c": 32}', '{"max_temp_c": 35}', '{"max_temp_c": 40}', '{"max_temp_c": 999}'),
('rain', '{"max_precipitation_percent": 20}', '{"max_precipitation_percent": 40}', '{"max_precipitation_percent": 60}', '{"max_precipitation_percent": 999}'),
('wind', '{"max_wind_speed_kmh": 20}', '{"max_wind_speed_kmh": 30}', '{"max_wind_speed_kmh": 50}', '{"max_wind_speed_kmh": 999}'),
('visibility', '{"min_visibility_km": 5}', '{"min_visibility_km": 2}', '{"min_visibility_km": 1}', '{"min_visibility_km": 0}')
ON CONFLICT DO NOTHING;

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

-- 4. Update assignments table
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS weather_safe BOOLEAN,
ADD COLUMN IF NOT EXISTS weather_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS weather_assessment JSONB;

-- 5. Update requests table
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS weather_context JSONB,
ADD COLUMN IF NOT EXISTS original_assignment_time TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS suggested_assignment_time TIMESTAMPTZ;

-- 6. Update sites table
ALTER TABLE sites
ADD COLUMN IF NOT EXISTS osm_display_name TEXT;

-- 7. Create indexes
CREATE INDEX IF NOT EXISTS idx_weather_safety_rules_type ON weather_safety_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_weather_safety_rules_active ON weather_safety_rules(active);

CREATE INDEX IF NOT EXISTS idx_schedule_change_user ON schedule_change_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_schedule_change_assignment ON schedule_change_requests(assignment_id);
CREATE INDEX IF NOT EXISTS idx_schedule_change_status ON schedule_change_requests(status);
CREATE INDEX IF NOT EXISTS idx_schedule_change_supervisor ON schedule_change_requests(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_schedule_change_created ON schedule_change_requests(created_on);
CREATE INDEX IF NOT EXISTS idx_schedule_change_active ON schedule_change_requests(active);

CREATE INDEX IF NOT EXISTS idx_location_cache_query ON location_cache(query);
CREATE INDEX IF NOT EXISTS idx_location_cache_coords ON location_cache(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_location_cache_last_accessed ON location_cache(last_accessed);
CREATE INDEX IF NOT EXISTS idx_location_cache_active ON location_cache(active);

CREATE INDEX IF NOT EXISTS idx_assignments_weather_safe ON assignments(weather_safe);
CREATE INDEX IF NOT EXISTS idx_assignments_weather_status ON assignments(weather_status);

CREATE INDEX IF NOT EXISTS idx_requests_weather ON requests(request_type) WHERE request_type = 'weather_change';

CREATE INDEX IF NOT EXISTS idx_sites_osm_display_name ON sites(osm_display_name);

COMMIT;
```

---

## Rollback Script

```sql
-- Rollback Hackathon Schema Changes
-- Run this to revert the database changes

BEGIN;

-- Drop indexes
DROP INDEX IF EXISTS idx_weather_safety_rules_type;
DROP INDEX IF EXISTS idx_weather_safety_rules_active;
DROP INDEX IF EXISTS idx_schedule_change_user;
DROP INDEX IF EXISTS idx_schedule_change_assignment;
DROP INDEX IF EXISTS idx_schedule_change_status;
DROP INDEX IF EXISTS idx_schedule_change_supervisor;
DROP INDEX IF EXISTS idx_schedule_change_created;
DROP INDEX IF EXISTS idx_schedule_change_active;
DROP INDEX IF EXISTS idx_location_cache_query;
DROP INDEX IF EXISTS idx_location_cache_coords;
DROP INDEX IF EXISTS idx_location_cache_last_accessed;
DROP INDEX IF EXISTS idx_location_cache_active;
DROP INDEX IF EXISTS idx_assignments_weather_safe;
DROP INDEX IF EXISTS idx_assignments_weather_status;
DROP INDEX IF EXISTS idx_requests_weather;
DROP INDEX IF EXISTS idx_sites_osm_display_name;

-- Drop tables
DROP TABLE IF EXISTS schedule_change_requests;
DROP TABLE IF EXISTS location_cache;
DROP TABLE IF EXISTS weather_safety_rules;

-- Remove columns from existing tables
ALTER TABLE assignments
DROP COLUMN IF EXISTS weather_safe,
DROP COLUMN IF EXISTS weather_status,
DROP COLUMN IF EXISTS weather_assessment;

ALTER TABLE requests
DROP COLUMN IF EXISTS weather_context,
DROP COLUMN IF EXISTS original_assignment_time,
DROP COLUMN IF EXISTS suggested_assignment_time;

ALTER TABLE sites
DROP COLUMN IF EXISTS osm_display_name;

COMMIT;
```

---

## Data Seeding for Demo

```sql
-- Seed data for hackathon demo

-- Demo weather safety rules (customized for demo scenario)
INSERT INTO weather_safety_rules (rule_type, safe_threshold, caution_threshold, warning_threshold, severe_threshold) VALUES
('heat_demo', '{"max_temp_c": 30}', '{"max_temp_c": 35}', '{"max_temp_c": 40}', '{"max_temp_c": 999}')
ON CONFLICT DO NOTHING;

-- Demo location cache (Mumbai, Vadodara)
INSERT INTO location_cache (query, latitude, longitude, display_name, city, state, country) VALUES
('Mumbai, Maharashtra, India', 19.0760, 72.8777, 'Mumbai, Maharashtra, India', 'Mumbai', 'Maharashtra', 'India'),
('Vadodara, Gujarat, India', 22.3072, 73.1812, 'Vadodara, Gujarat, India', 'Vadodara', 'Gujarat', 'India')
ON CONFLICT (query) DO NOTHING;

-- Demo schedule change request (pending)
-- This requires existing users and assignments to be set up first
-- Uncomment after users and assignments exist:
/*
INSERT INTO schedule_change_requests (
    user_id,
    assignment_id,
    original_start_time,
    original_end_time,
    suggested_start_time,
    suggested_end_time,
    original_weather,
    suggested_weather,
    weather_status,
    reason,
    urgency,
    status
) VALUES (
    (SELECT id FROM users WHERE username = 'rahul' LIMIT 1),
    (SELECT id FROM assignments WHERE description LIKE '%Site B%' LIMIT 1),
    '2024-01-15T14:00:00Z',
    '2024-01-15T16:00:00Z',
    '2024-01-15T18:00:00Z',
    '2024-01-15T20:00:00Z',
    '{"temperature_c": 42, "precipitation_percent": 5, "wind_speed_kmh": 10, "visibility_km": 10, "humidity_percent": 60}',
    '{"temperature_c": 32, "precipitation_percent": 10, "wind_speed_kmh": 8, "visibility_km": 10, "humidity_percent": 55}',
    'SEVERE',
    'Too hot, worried about heat stroke',
    'high',
    'pending'
);
*/
```

---

## Notes

1. **Soft Delete Pattern**: All tables follow the existing `active` column pattern for soft deletion.

2. **UTC Timestamps**: All timestamps are stored in UTC to maintain consistency across timezones.

3. **JSONB for Flexibility**: Weather data and assessments use JSONB for flexible schema evolution.

4. **Indexing Strategy**: Indexes are created on frequently queried columns (user_id, status, created_on).

5. **Constraints**: Check constraints ensure data integrity for status enums and numeric ranges.

6. **Foreign Keys**: All foreign keys have appropriate ON DELETE actions (RESTRICT for critical, SET NULL for optional).

7. **OpenStreetMap Integration**: The `location_cache` table reduces API calls to OSM Nominatim by caching geocoding results.

8. **Demo Data**: The seeding script provides sample data for the hackathon demo scenario.
