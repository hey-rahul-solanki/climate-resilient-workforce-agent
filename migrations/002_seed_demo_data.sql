-- Seed Demo Data for Hackathon
-- Run this after migration to populate demo data
-- Version: 002
-- Date: 2024-01-15

BEGIN;

-- ============================================
-- DEMO USERS
-- ============================================

-- Insert demo users if they don't exist
INSERT INTO users (username, email, employee_id, full_name, role, status, location_id, password_hash)
VALUES
('rahul', 'rahul@example.com', 'EMP001', 'Rahul Sharma', 'employee', 'active',
 (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1),
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWq5F5H5W6i'), -- password: password123
('amit', 'amit@example.com', 'EMP002', 'Amit Patel', 'employee', 'active',
 (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1),
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWq5F5H5W6i'), -- password: password123
('supervisor1', 'supervisor1@example.com', 'SUP001', 'Jane Smith', 'supervisor', 'active',
 (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1),
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWq5F5H5W6i') -- password: password123
ON CONFLICT (username) DO NOTHING;

-- ============================================
-- DEMO SITES
-- ============================================

-- Insert demo sites if they don't exist
INSERT INTO sites (site_id, name, city, state, country, latitude, longitude, location_id, timezone, status)
VALUES
('VAD-PLANT-01', 'Vadodara Process Plant', 'Vadodara', 'Gujarat', 'India', 22.3072, 73.1812,
 (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1), 'Asia/Kolkata', 'active'),
('MUM-SITE-01', 'Mumbai Industrial Site', 'Mumbai', 'Maharashtra', 'India', 19.0760, 72.8777,
 (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1), 'Asia/Kolkata', 'active')
ON CONFLICT (site_id) DO NOTHING;

-- ============================================
-- DEMO ASSIGNMENTS
-- ============================================

-- Insert demo assignments if they don't exist
INSERT INTO assignments (user_id, site_id, status, description, start_time, end_time, shift, hours_allocated)
VALUES
((SELECT id FROM users WHERE username = 'rahul' LIMIT 1),
 (SELECT id FROM sites WHERE site_id = 'VAD-PLANT-01' LIMIT 1),
 'scheduled', 'Site B - Inspection', '2024-01-15T14:00:00Z', '2024-01-15T16:00:00Z', 'afternoon', 2),
((SELECT id FROM users WHERE username = 'amit' LIMIT 1),
 (SELECT id FROM sites WHERE site_id = 'MUM-SITE-01' LIMIT 1),
 'scheduled', 'Site C - Repair', '2024-01-15T13:00:00Z', '2024-01-15T15:00:00Z', 'afternoon', 2)
ON CONFLICT DO NOTHING;

-- Update assignments with weather data for demo
UPDATE assignments
SET weather = '{"temperature_c": 42, "precipitation_percent": 5, "wind_speed_kmh": 10, "visibility_km": 10, "humidity_percent": 60}',
    weather_safe = false,
    weather_status = 'SEVERE',
    weather_assessment = '{"status": "SEVERE", "is_safe": false, "reason": "Extreme heat: 42°C", "recommendations": ["DO NOT PROCEED - Reschedule immediately"]}'
WHERE id = (SELECT id FROM assignments WHERE description LIKE '%Site B%' LIMIT 1);

-- ============================================
-- LOCATION CACHE
-- ============================================

-- Insert location cache entries
INSERT INTO location_cache (query, latitude, longitude, display_name, city, state, country)
VALUES
('Mumbai, Maharashtra, India', 19.0760, 72.8777, 'Mumbai, Maharashtra, India', 'Mumbai', 'Maharashtra', 'India'),
('Vadodara, Gujarat, India', 22.3072, 73.1812, 'Vadodara, Gujarat, India', 'Vadodara', 'Gujarat', 'India')
ON CONFLICT (query) DO NOTHING;

COMMIT;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Uncomment to verify seed data

-- SELECT username, email, full_name, role FROM users WHERE username IN ('rahul', 'amit', 'supervisor1');
-- SELECT site_id, name, city, status FROM sites WHERE site_id IN ('VAD-PLANT-01', 'MUM-SITE-01');
-- SELECT id, description, start_time, end_time, weather_status FROM assignments WHERE description LIKE '%Site%';
-- SELECT query, display_name FROM location_cache;
-- SELECT rule_type FROM weather_safety_rules;
