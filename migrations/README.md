# Database Migrations

This directory contains SQL migration files for the hackathon solution.

## Migration Files

### 001_hackathon_schema_updates.sql
Creates the new tables and columns needed for the hackathon solution:
- weather_safety_rules table
- schedule_change_requests table
- location_cache table
- Updates to assignments, requests, and sites tables
- All necessary indexes and constraints

### 002_seed_demo_data.sql
Populates the database with demo data:
- Demo users (rahul, amit, supervisor1)
- Demo sites (VAD-PLANT-01, MUM-SITE-01)
- Demo assignments with extreme heat scenario
- Location cache entries
- Default weather safety rules

## How to Run Migrations

### Using psql

```bash
# Run schema migration
psql -U workforce_user -d workforce_db -f migrations/001_hackathon_schema_updates.sql

# Run seed data
psql -U workforce_user -d workforce_db -f migrations/002_seed_demo_data.sql
```

### Using Docker Compose

If using Docker Compose with PostgreSQL:

```bash
# Connect to PostgreSQL container
docker exec -it workforce_postgres psql -U workforce_user -d workforce_db

# Run migrations
\i migrations/001_hackathon_schema_updates.sql
\i migrations/002_seed_demo_data.sql
```

## Verification

After running migrations, you can verify by uncommenting the verification queries at the bottom of each SQL file and running them.

## Rollback

To rollback changes, you would need to manually:
1. Drop new tables: `DROP TABLE schedule_change_requests, location_cache, weather_safety_rules;`
2. Remove columns from existing tables
3. Remove indexes

A rollback script can be created if needed.
