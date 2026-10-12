# Synthetic workforce-planning data (CSV)

These CSVs are human-readable seed data for the Climate-Resilient Workforce Planning Agent. All workers, work orders, equipment and policies are synthetic demo records.

## Files
- `workers.csv` — five fictional workers, skills, certifications, shifts and breaks.
- `work_orders.csv` — five tasks, priorities, durations, crew requirements, dependencies and exposure windows.
- `equipment.csv` — four equipment records; the confined-space monitoring kit is intentionally unavailable.
- `safety_policies.csv` — illustrative configurable policy rules for testing only.

## Important notes
- Site IDs should match the synthetic `vadodara.json` configuration.
- These files use human-readable, semicolon-separated lists in cells. A loader should parse those fields deliberately.
- Dates are seeded for 13–14 October 2026; use a controllable clock or refresh fixture dates for repeatable future tests.
- Safety thresholds are illustrative software-test values, not approved occupational safety limits.
- CSVs are for human editing; validate them against the repository's Pydantic schemas when loading.
